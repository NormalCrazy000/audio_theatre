import hashlib
import json
import os
from pathlib import Path

from copione_audio.tts.base import InfoVoce, TTSEngine, Voce


# cache.py → tts → copione_audio → src → backend → radice del progetto
CACHE_PREDEFINITA = Path(__file__).parents[4] / "cache"


def cartella_predefinita() -> Path:
    """`$COPIONE_AUDIO_CACHE`, oppure la cartella `cache/` nella radice del progetto."""
    return Path(os.environ.get("COPIONE_AUDIO_CACHE", CACHE_PREDEFINITA))


class CacheTTS:
    """
    Avvolge un motore TTS e salva su disco ogni sintesi, con chiave
    (motore, voce, testo): la stessa battuta non viene richiesta due volte.
    """

    def __init__(self, motore: TTSEngine, cartella: Path | None = None):
        self.motore = motore
        self.formato = motore.formato
        self.cartella = cartella or cartella_predefinita()

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
        return await self.motore.voci(lingua)
