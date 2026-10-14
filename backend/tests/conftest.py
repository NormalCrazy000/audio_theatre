from io import BytesIO

import pytest
from pydub import AudioSegment

from copione_audio.tts import InfoVoce, Voce


class FintoTTS:
    """Motore TTS offline: 1 secondo di silenzio per ogni parola, in WAV."""

    formato = "wav"

    def __init__(self):
        self.richieste: list[tuple[str, Voce]] = []

    async def sintetizza(self, testo: str, voce: Voce) -> bytes:
        self.richieste.append((testo, voce))
        buffer = BytesIO()
        AudioSegment.silent(1000 * len(testo.split())).export(buffer, format="wav")
        return buffer.getvalue()

    async def voci(self, lingua: str) -> list[InfoVoce]:
        return [InfoVoce("finta", "Female", f"{lingua}-XX")]


@pytest.fixture
def finto_tts() -> FintoTTS:
    return FintoTTS()
