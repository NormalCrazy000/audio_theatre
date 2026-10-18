"""
Motore Piper: sintesi vocale sul computer, senza internet.

Le voci sono modelli ONNX (`NOME.onnx` + `NOME.onnx.json`) da scaricare una
volta sola nella cartella delle voci. Per scaricare quelle italiane:

    uv run --project backend python -m copione_audio.tts.piper
"""

import argparse
import asyncio
import json
import os
import re
import shutil
import tempfile
import threading
from io import BytesIO
from pathlib import Path

from pydub import AudioSegment

from copione_audio.tts.base import InfoVoce, Voce

VOCI_CONSIGLIATE = ("it_IT-paola-medium", "it_IT-riccardo-x_low", "it_IT-serena-medium")
"""Le voci italiane da scaricare: una per ogni speaker disponibile."""

# I modelli non dichiarano il genere: quello delle voci note è scritto qui.
GENERI = {"paola": "Female", "riccardo": "Male", "serena": "Female"}

# Piper non varia il tono: lo si sposta dopo la sintesi, trattando gli Hz
# delle voci (pensati per edge-tts) come scarto da una voce media di 200 Hz.
HZ_RIFERIMENTO = 200


def cartella_predefinita() -> Path:
    """
    `$COPIONE_AUDIO_PIPER`, oppure `$XDG_DATA_HOME/copione-audio/piper`, o
    `~/.local/share/copione-audio/piper`.
    """
    if cartella := os.environ.get("COPIONE_AUDIO_PIPER"):
        return Path(cartella)
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "copione-audio" / "piper"


def _percentuale(valore: str, unita: str) -> float:
    """"+12Hz" → 12.0; "-10%" → -10.0. Un valore non valido vale 0."""
    trovato = re.fullmatch(rf"([+-]?\d+(?:\.\d+)?){unita}", valore.strip())
    return float(trovato.group(1)) if trovato else 0.0


class PiperTTS:
    """Motore Piper (voci locali, funziona senza internet)."""

    formato = "mp3"

    def __init__(self, cartella: Path | None = None):
        """:param cartella: Dove stanno le voci; di default `cartella_predefinita()`."""
        self.cartella = cartella or cartella_predefinita()
        self._modelli: dict[str, object] = {}
        self._blocco = threading.Lock()

    def _modello(self, nome: str):
        """Carica un modello una volta sola (la prima sintesi con quella voce)."""
        with self._blocco:
            if nome not in self._modelli:
                from piper import PiperVoice

                percorso = self.cartella / f"{nome}.onnx"
                if not percorso.exists():
                    raise ValueError(f"voce Piper non installata: {nome}")
                self._modelli[nome] = PiperVoice.load(percorso)
            return self._modelli[nome]

    def _sintetizza(self, testo: str, voce: Voce) -> bytes:
        from piper import SynthesisConfig

        modello = self._modello(voce.nome)
        velocita = 1 + _percentuale(voce.velocita, "%") / 100
        configurazione = SynthesisConfig(length_scale=1 / max(velocita, 0.1))
        pezzi = list(modello.synthesize(testo, configurazione))
        if not pezzi:
            raise ValueError(f"nessun audio per: {testo!r}")
        frequenza = pezzi[0].sample_rate
        audio = AudioSegment(
            data=b"".join(p.audio_int16_bytes for p in pezzi),
            sample_width=2,
            frame_rate=frequenza,
            channels=1,
        )
        parametri = []
        fattore = 1 + _percentuale(voce.tono, "Hz") / HZ_RIFERIMENTO
        if fattore != 1:
            # Alza o abbassa il tono lasciando invariata la durata.
            fattore = min(max(fattore, 0.5), 2)
            filtro = f"asetrate={frequenza * fattore:.0f},aresample={frequenza},atempo={1 / fattore:.6f}"
            parametri = ["-af", filtro]
        buffer = BytesIO()
        audio.export(buffer, format="mp3", bitrate="64k", parameters=parametri)
        return buffer.getvalue()

    async def sintetizza(self, testo: str, voce: Voce) -> bytes:
        # La sintesi usa la CPU: in un thread per non bloccare il server.
        return await asyncio.to_thread(self._sintetizza, testo, voce)

    async def voci(self, lingua: str) -> list[InfoVoce]:
        """Le voci installate per la lingua, lette ogni volta dalla cartella."""
        voci = []
        for configurazione in sorted(self.cartella.glob("*.onnx.json")):
            nome = configurazione.name.removesuffix(".onnx.json")
            if not (self.cartella / f"{nome}.onnx").exists():
                continue
            try:
                dati = json.loads(configurazione.read_text(encoding="utf-8"))
                codice = dati["language"]["code"]
            except (OSError, ValueError, KeyError, TypeError):
                continue
            if codice.split("_")[0] != lingua:
                continue
            speaker = nome.split("-")[1] if nome.count("-") >= 2 else nome
            voci.append(InfoVoce(nome, GENERI.get(speaker, "Unknown"), codice.replace("_", "-")))
        return voci


def scarica_voci(nomi: list[str], cartella: Path) -> None:
    """
    Scarica le voci in `cartella`, saltando quelle già presenti. Ogni file
    viene scritto prima in una cartella temporanea, così un'interruzione non
    lascia modelli a metà.
    """
    from piper.download_voices import download_voice

    cartella.mkdir(parents=True, exist_ok=True)
    for nome in nomi:
        file = [f"{nome}.onnx", f"{nome}.onnx.json"]
        if all((cartella / f).exists() for f in file):
            print(f"{nome}: già presente")
            continue
        print(f"{nome}: download in corso…", flush=True)
        with tempfile.TemporaryDirectory(dir=cartella) as temporanea:
            download_voice(nome, Path(temporanea))
            for f in file:
                shutil.move(Path(temporanea) / f, cartella / f)
        print(f"{nome}: fatto")


def main():
    parser = argparse.ArgumentParser(description="Scarica le voci Piper per l'uso offline.")
    parser.add_argument(
        "voci",
        nargs="*",
        default=list(VOCI_CONSIGLIATE),
        help="nomi delle voci (es. it_IT-paola-medium); di default quelle italiane",
    )
    parser.add_argument("--cartella", type=Path, default=cartella_predefinita())
    argomenti = parser.parse_args()
    scarica_voci(argomenti.voci, argomenti.cartella)
    print(f"Voci in {argomenti.cartella}")


if __name__ == "__main__":
    main()
