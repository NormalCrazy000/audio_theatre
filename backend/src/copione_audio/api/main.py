"""
API HTTP. Tutti gli endpoint stanno sotto `/api`; se esiste la build del
frontend, viene servita su `/`.

Avvio (dalla radice): `uv run --project backend uvicorn copione_audio.api.main:app`.
"""

import asyncio
import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from copione_audio.conversione.pdf import estrai_testo
from copione_audio.copione import Copione, Errore, analizza
from copione_audio.piano import NARRATORE, Opzioni, Segmento, crea_piano
from copione_audio.render import render
from copione_audio.tts import InfoVoce, TTSEngine, Voce, assegna_voci
from copione_audio.tts.cache import CacheTTS
from copione_audio.tts.edge import EdgeTTS

# main.py → api → copione_audio → src → backend → radice del progetto
FRONTEND_PREDEFINITO = Path(__file__).parents[4] / "frontend" / "dist"


@cache
def motore_tts() -> TTSEngine:
    """Il motore TTS dell'app (sostituibile nei test con `dependency_overrides`)."""
    return CacheTTS(EdgeTTS())


Motore = Annotated[TTSEngine, Depends(motore_tts)]


# --- Modelli di richiesta e risposta ---


class Testo(BaseModel):
    testo: str


class ErroreOut(BaseModel):
    riga: int | None
    messaggio: str


class ScenaOut(BaseModel):
    indice: int
    titolo: str | None
    battute: int
    personaggi: list[str]
    """Chi parla nella scena, in ordine di prima battuta."""


class Analisi(BaseModel):
    titolo: str
    lingua: str
    personaggi: list[str]
    battute_per_personaggio: dict[str, int]
    scene: list[ScenaOut]
    errori: list[ErroreOut]


class RichiestaAudio(BaseModel):
    testo: str
    opzioni: Opzioni
    voci: dict[str, Voce] = {}
    """Voci scelte; i personaggi mancanti ricevono una voce automatica."""


class StatoLavoro(BaseModel):
    id: str
    stato: Literal["in_corso", "completato", "errore"]
    fatte: int
    totali: int
    errore: str | None
    durata_s: float | None
    nome_file: str


@dataclass
class Lavoro:
    """Una generazione audio in corso o finita."""

    id: str
    nome_file: str
    stato: Literal["in_corso", "completato", "errore"] = "in_corso"
    fatte: int = 0
    totali: int = 0
    errore: str | None = None
    durata_s: float | None = None
    file: Path | None = field(default=None, repr=False)

    def stato_out(self) -> StatoLavoro:
        return StatoLavoro(
            id=self.id,
            stato=self.stato,
            fatte=self.fatte,
            totali=self.totali,
            errore=self.errore,
            durata_s=self.durata_s,
            nome_file=self.nome_file,
        )


def _errori_out(errori: list[Errore]) -> list[ErroreOut]:
    return [ErroreOut(riga=e.riga, messaggio=e.messaggio) for e in errori]


def _analisi(copione: Copione, errori: list[Errore]) -> Analisi:
    return Analisi(
        titolo=copione.titolo,
        lingua=copione.lingua,
        personaggi=copione.personaggi,
        battute_per_personaggio=copione.battute_per_personaggio(),
        scene=[
            ScenaOut(
                indice=i,
                titolo=s.titolo,
                battute=len(s.battute),
                personaggi=list(dict.fromkeys(n for b in s.battute for n in b.personaggi)),
            )
            for i, s in enumerate(copione.scene)
        ],
        errori=_errori_out(errori),
    )


def _nome_file(titolo: str, personaggio: str) -> str:
    """Nome dell'mp3 da scaricare, es. "Così non vale.LAURA.mp3"."""
    base = " ".join(re.sub(r'[\\/:*?"<>|]', " ", titolo).split()) or "copione"
    return f"{base}.{personaggio}.mp3"


async def _esegui(
    lavoro: Lavoro,
    segmenti: list[Segmento],
    voci: dict[str, Voce],
    motore: TTSEngine,
    cartella: Path,
):
    """Esegue il render e salva l'mp3, aggiornando lo stato del lavoro."""

    def progresso(fatte: int, totali: int):
        lavoro.fatte, lavoro.totali = fatte, totali

    try:
        audio = await render(segmenti, voci, motore, progresso)
        percorso = cartella / f"{lavoro.id}.mp3"
        file = await asyncio.to_thread(audio.export, percorso, format="mp3")
        file.close()
        lavoro.file, lavoro.durata_s = percorso, len(audio) / 1000
        lavoro.stato = "completato"
    except Exception as e:
        lavoro.stato, lavoro.errore = "errore", str(e) or type(e).__name__


def crea_app(
    cartella_lavori: Path | None = None, frontend: Path | None = None
) -> FastAPI:
    """
    Crea l'applicazione.

    :param cartella_lavori: Dove salvare gli mp3 generati; di default una
        cartella temporanea.
    :param frontend: La build del frontend da servire su `/`; di default
        `$COPIONE_AUDIO_FRONTEND` o `frontend/dist`, se esiste.
    """
    app = FastAPI(title="Copione Audio")
    app.state.cartella = cartella_lavori or Path(tempfile.mkdtemp(prefix="copione-audio-"))
    app.state.lavori: dict[str, Lavoro] = {}
    # Riferimenti ai task in corso, perché non vengano raccolti dal GC.
    app.state.task: set[asyncio.Task] = set()

    @app.post("/api/copioni/analizza")
    def analizza_copione(richiesta: Testo) -> Analisi:
        """Legge e valida un copione nel formato standard."""
        return _analisi(*analizza(richiesta.testo))

    @app.post("/api/copioni/pdf")
    def testo_da_pdf(file: UploadFile) -> Testo:
        """Estrae il testo grezzo da un PDF."""
        try:
            return Testo(testo=estrai_testo(file.file))
        except Exception as e:
            raise HTTPException(422, f"PDF non leggibile: {e}")

    @app.get("/api/voci")
    async def voci(motore: Motore, lingua: str = "it") -> list[InfoVoce]:
        """Le voci disponibili per una lingua."""
        return await motore.voci(lingua)

    @app.post("/api/audio", status_code=202)
    async def genera_audio(
        richiesta: RichiestaAudio, motore: Motore, request: Request
    ) -> StatoLavoro:
        """
        Avvia la generazione dell'mp3. I problemi del copione e delle opzioni
        vengono segnalati subito (422); la sintesi prosegue in background.
        """
        copione, errori = analizza(richiesta.testo)
        if errori:
            raise HTTPException(
                422,
                {
                    "messaggio": "il copione contiene errori",
                    "errori": [e.model_dump() for e in _errori_out(errori)],
                },
            )
        try:
            segmenti = crea_piano(copione, richiesta.opzioni)
            disponibili = await motore.voci(copione.lingua)
            voci = assegna_voci(copione.personaggi + [NARRATORE], disponibili)
        except ValueError as e:
            raise HTTPException(422, {"messaggio": str(e)})
        if not segmenti:
            raise HTTPException(
                422, {"messaggio": "nessuna battuta da studiare con queste opzioni"}
            )

        lavoro = Lavoro(
            id=uuid.uuid4().hex,
            nome_file=_nome_file(copione.titolo, richiesta.opzioni.personaggio),
        )
        request.app.state.lavori[lavoro.id] = lavoro
        task = asyncio.create_task(
            _esegui(
                lavoro,
                segmenti,
                voci | richiesta.voci,
                motore,
                request.app.state.cartella,
            )
        )
        request.app.state.task.add(task)
        task.add_done_callback(request.app.state.task.discard)
        return lavoro.stato_out()

    def _lavoro(request: Request, id: str) -> Lavoro:
        lavoro = request.app.state.lavori.get(id)
        if lavoro is None:
            raise HTTPException(404, "lavoro non trovato")
        return lavoro

    @app.get("/api/audio/{id}")
    def stato_audio(id: str, request: Request) -> StatoLavoro:
        """Stato e progresso di una generazione."""
        return _lavoro(request, id).stato_out()

    @app.get("/api/audio/{id}/mp3")
    def scarica_audio(id: str, request: Request) -> FileResponse:
        """L'mp3 generato, da scaricare."""
        lavoro = _lavoro(request, id)
        if lavoro.stato != "completato" or lavoro.file is None:
            raise HTTPException(409, f"audio non pronto (stato: {lavoro.stato})")
        return FileResponse(lavoro.file, media_type="audio/mpeg", filename=lavoro.nome_file)

    frontend = frontend or Path(
        os.environ.get("COPIONE_AUDIO_FRONTEND", FRONTEND_PREDEFINITO)
    )
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = crea_app()
