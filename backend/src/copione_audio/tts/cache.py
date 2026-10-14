import hashlib
import json
import os
from pathlib import Path

from copione_audio.tts.base import InfoVoce, TTSEngine, Voce


def cartella_predefinita() -> Path:
    """`$XDG_CACHE_HOME/copione-audio/tts`, o `~/.cache/copione-audio/tts`."""
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "copione-audio" / "tts"


class CacheTTS:
    """
    Avvolge un motore TTS e salva su disco ogni sintesi, con chiave
    (motore, voce, testo): la stessa battuta non viene richiesta due volte.
    """

    def __init__(self, motore: TTSEngine, cartella: Path | None = None):
        self.motore = motore
        self.formato = motore.formato
        self.cartella = cartella or cartella_predefinita()
        self._voci: dict[str, list[InfoVoce]] = {}

    def _percorso(self, testo: str, voce: Voce) -> Path:
        chiave = json.dumps(
            [type(self.motore).__name__, voce.nome, voce.tono, voce.velocita, testo]
        )
        nome = hashlib.sha256(chiave.encode()).hexdigest()
        return self.cartella / nome[:2] / f"{nome}.{self.formato}"

    async def sintetizza(self, testo: str, voce: Voce) -> bytes:
        percorso = self._percorso(testo, voce)
        if percorso.exists():
            return percorso.read_bytes()
        audio = await self.motore.sintetizza(testo, voce)
        percorso.parent.mkdir(parents=True, exist_ok=True)
        # Scrittura atomica: un'interruzione non lascia file a metà nella cache.
        temporaneo = percorso.with_suffix(".tmp")
        temporaneo.write_bytes(audio)
        temporaneo.replace(percorso)
        return audio

    async def voci(self, lingua: str) -> list[InfoVoce]:
        if lingua not in self._voci:
            self._voci[lingua] = await self.motore.voci(lingua)
        return self._voci[lingua]
