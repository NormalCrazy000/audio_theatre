"""
Motore Piper: sintesi vocale sul computer, senza internet.

Le voci sono modelli ONNX (`NOME.onnx` + `NOME.onnx.json`) nella cartella delle
voci; si scaricano a mano e si gestiscono con `voci_piper`.
"""

import asyncio
import re
import threading
from io import BytesIO
from pathlib import Path

from pydub import AudioSegment

from copione_audio.tts.base import InfoVoce, Voce
from copione_audio.tts.voci_piper import cartella_predefinita, voci_installate

# Piper non varia il tono: lo si sposta dopo la sintesi, trattando gli Hz
# delle voci (pensati per edge-tts) come scarto da una voce media di 200 Hz.
HZ_RIFERIMENTO = 200


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
        self._modelli: dict[tuple[str, int], object] = {}
        self._blocco = threading.Lock()

    def _modello(self, nome: str):
        """
        Carica un modello una volta sola. La chiave include la data di modifica
        del file: una voce sostituita viene ricaricata.
        """
        percorso = self.cartella / f"{nome}.onnx"
        if not percorso.is_file():
            raise ValueError(f"voce Piper non installata: {nome}")
        chiave = (nome, percorso.stat().st_mtime_ns)
        with self._blocco:
            if chiave not in self._modelli:
                from piper import PiperVoice

                self._modelli = {k: m for k, m in self._modelli.items() if k[0] != nome}
                self._modelli[chiave] = PiperVoice.load(percorso)
            return self._modelli[chiave]

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
        """Le voci complete per la lingua, lette ogni volta dalla cartella."""
        return [
            InfoVoce(v.nome, v.genere, v.lingua)
            for v in voci_installate(self.cartella)
            if v.completa and v.lingua.split("-")[0] == lingua
        ]
