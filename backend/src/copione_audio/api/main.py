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
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from copione_audio.conversione.pdf import estrai_testo
from copione_audio.copione import Copione, Errore, analizza
from copione_audio.piano import NARRATORE, Opzioni, Segmento, crea_piano
from copione_audio.render import render
from copione_audio.tts import InfoVoce, TTSEngine, Voce, assegna_voci
from copione_audio.tts.cache import CacheTTS
from copione_audio.tts.edge import EdgeTTS
from copione_audio.tts import voci_piper
from copione_audio.tts.piper import PiperTTS

# main.py → api → copione_audio → src → backend → radice del progetto
FRONTEND_PREDEFINITO = Path(__file__).parents[4] / "frontend" / "dist"


NomeMotore = Literal["edge", "piper"]
"""`edge`: voci Microsoft online; `piper`: voci locali, senza internet."""


@cache
def motori_tts() -> dict[str, TTSEngine]:
    """I motori TTS dell'app (sostituibili nei test con `dependency_overrides`)."""
    return {"edge": CacheTTS(EdgeTTS()), "piper": CacheTTS(PiperTTS())}


Motori = Annotated[dict[str, TTSEngine], Depends(motori_tts)]


def cartella_voci_piper() -> Path:
    """La cartella delle voci Piper (sostituibile nei test con `dependency_overrides`)."""
    return voci_piper.cartella_predefinita()


CartellaVoci = Annotated[Path, Depends(cartella_voci_piper)]


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


class RichiestaAssegnazione(BaseModel):
    lingua: str
    personaggi: list[str]
    motore: NomeMotore = "edge"


class RichiestaAnteprima(BaseModel):
    voce: Voce
    testo: str = "Buongiorno, questa è la mia voce."
    motore: NomeMotore = "edge"


class RichiestaAudio(BaseModel):
    testo: str
    opzioni: Opzioni
    motore: NomeMotore = "edge"
    voci: dict[str, Voce] = {}
    """Voci scelte; i personaggi mancanti ricevono una voce automatica."""


class VoceInstallataOut(BaseModel):
    nome: str
    lingua: str
    genere: str
    modello: bool
    """Se c'è il file `.onnx`."""
    configurazione: bool
    """Se c'è il file `.onnx.json` ed è valido."""
    completa: bool
    mb: float


class VoceCatalogoOut(BaseModel):
    nome: str
    genere: str
    qualita: str
    mb: int
    dati: str
    link_modello: str
    link_configurazione: str
    pagina: str
    installata: bool


class VociOffline(BaseModel):
    """Stato della cartella delle voci Piper, con i link per scaricarne altre."""

    cartella: str
    installate: list[VoceInstallataOut]
    catalogo: list[VoceCatalogoOut]
    """Le voci della lingua richiesta, da scaricare a mano."""
    repository: str
    """Dove trovare le voci di tutte le lingue."""


class ErroreFile(BaseModel):
    file: str
    messaggio: str


class RisultatoAggiunta(BaseModel):
    aggiunti: list[str]
    """I file salvati."""
    errori: list[ErroreFile]
    """I file rifiutati, con il motivo."""
    voci: VociOffline


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


def _voci_offline(cartella: Path, lingua: str) -> VociOffline:
    installate = voci_piper.voci_installate(cartella)
    complete = {v.nome for v in installate if v.completa}
    return VociOffline(
        cartella=str(cartella.resolve()),
        installate=[
            VoceInstallataOut(
                nome=v.nome,
                lingua=v.lingua,
                genere=v.genere,
                modello=v.modello,
                configurazione=v.configurazione,
                completa=v.completa,
                mb=v.mb,
            )
            for v in installate
        ],
        catalogo=[
            VoceCatalogoOut(
                nome=v.nome,
                genere=v.genere,
                qualita=v.qualita,
                mb=v.mb,
                dati=v.dati,
                link_modello=v.link_modello,
                link_configurazione=v.link_configurazione,
                pagina=v.pagina,
                installata=v.nome in complete,
            )
            for v in voci_piper.CATALOGO
            if v.nome.split("_")[0] == lingua
        ],
        repository=voci_piper.REPOSITORY,
    )


async def _disponibili(motori: dict[str, TTSEngine], motore: str, lingua: str) -> list[InfoVoce]:
    """
    Le voci del motore per la lingua.

    :raises HTTPException: 502 se il motore non risponde (es. edge-tts senza
        internet), 422 se non ci sono voci (es. Piper senza voci installate).
    """
    try:
        voci = await motori[motore].voci(lingua)
    except Exception as e:
        raise HTTPException(502, {"messaggio": f"elenco delle voci non disponibile: {e}"})
    if not voci:
        messaggio = f"nessuna voce per la lingua \"{lingua}\""
        if motore == "piper":
            messaggio += "; aggiungile da «Gestisci voci offline» nelle Impostazioni"
        raise HTTPException(422, {"messaggio": messaggio})
    return voci


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
    async def voci(
        motori: Motori, lingua: str = "it", motore: NomeMotore = "edge"
    ) -> list[InfoVoce]:
        """Le voci disponibili per una lingua; per Piper, quelle installate."""
        return await _disponibili(motori, motore, lingua)

    @app.post("/api/voci/assegna")
    async def assegna(richiesta: RichiestaAssegnazione, motori: Motori) -> dict[str, Voce]:
        """
        Assegnazione automatica delle voci (più quella del narratore), da usare
        come punto di partenza nella UI.
        """
        disponibili = await _disponibili(motori, richiesta.motore, richiesta.lingua)
        return assegna_voci(richiesta.personaggi + [NARRATORE], disponibili)

    @app.get("/api/voci/piper")
    def voci_offline(cartella: CartellaVoci, lingua: str = "it") -> VociOffline:
        """Le voci Piper installate e quelle della lingua da scaricare a mano."""
        return _voci_offline(cartella, lingua)

    @app.post("/api/voci/piper")
    def aggiungi_voci_offline(
        file: list[UploadFile], cartella: CartellaVoci, lingua: str = "it"
    ) -> RisultatoAggiunta:
        """
        Salva nella cartella i file delle voci (`.onnx` e `.onnx.json`),
        scaricati a mano. I file non validi vengono rifiutati uno per uno.
        """
        aggiunti, errori = [], []
        for f in file:
            nome = f.filename or "?"
            try:
                voci_piper.aggiungi_file(cartella, nome, f.file)
                aggiunti.append(nome)
            except ValueError as e:
                errori.append(ErroreFile(file=nome, messaggio=str(e)))
        return RisultatoAggiunta(
            aggiunti=aggiunti, errori=errori, voci=_voci_offline(cartella, lingua)
        )

    @app.delete("/api/voci/piper/{nome}")
    def elimina_voce_offline(nome: str, cartella: CartellaVoci, lingua: str = "it") -> VociOffline:
        """Cancella i file di una voce Piper."""
        try:
            voci_piper.elimina_voce(cartella, nome)
        except ValueError as e:
            raise HTTPException(404, {"messaggio": str(e)})
        return _voci_offline(cartella, lingua)

    @app.post(
        "/api/voci/anteprima",
        response_class=Response,
        responses={200: {"content": {"audio/mpeg": {}}}},
    )
    async def anteprima(richiesta: RichiestaAnteprima, motori: Motori) -> Response:
        """Una frase breve letta con la voce indicata."""
        motore = motori[richiesta.motore]
        testo = richiesta.testo.strip()[:300]
        if not testo:
            raise HTTPException(422, {"messaggio": "testo vuoto"})
        try:
            audio = await motore.sintetizza(testo, richiesta.voce)
        except Exception as e:
            raise HTTPException(502, {"messaggio": f"sintesi non riuscita: {e}"})
        tipo = "audio/mpeg" if motore.formato == "mp3" else f"audio/{motore.formato}"
        return Response(audio, media_type=tipo)

    @app.post("/api/audio", status_code=202)
    async def genera_audio(
        richiesta: RichiestaAudio, motori: Motori, request: Request
    ) -> StatoLavoro:
        """
        Avvia la generazione dell'mp3. I problemi del copione e delle opzioni
        vengono segnalati subito (422); la sintesi prosegue in background.
        """
        motore = motori[richiesta.motore]
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
        except ValueError as e:
            raise HTTPException(422, {"messaggio": str(e)})
        if not segmenti:
            raise HTTPException(
                422, {"messaggio": "nessuna battuta da studiare con queste opzioni"}
            )
        disponibili = await _disponibili(motori, richiesta.motore, copione.lingua)
        voci = assegna_voci(copione.personaggi + [NARRATORE], disponibili)

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
