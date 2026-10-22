import asyncio

import edge_tts

from audio_theatre.tts.base import InfoVoce, Voce


class EdgeTTS:
    """Motore edge-tts (voci neurali Microsoft, richiede internet)."""

    formato = "mp3"

    def __init__(self, tentativi: int = 3):
        """:param tentativi: Quante volte provare una sintesi prima di arrendersi."""
        self.tentativi = tentativi
        self._voci: list[dict] | None = None

    async def sintetizza(self, testo: str, voce: Voce) -> bytes:
        for tentativo in range(self.tentativi):
            try:
                comunicazione = edge_tts.Communicate(
                    testo, voce.nome, rate=voce.velocita, pitch=voce.tono
                )
                audio = bytearray()
                async for pezzo in comunicazione.stream():
                    if pezzo["type"] == "audio":
                        audio += pezzo["data"]
                return bytes(audio)
            except Exception:
                if tentativo == self.tentativi - 1:
                    raise
                await asyncio.sleep(2**tentativo)
        raise AssertionError("irraggiungibile")

    async def voci(self, lingua: str) -> list[InfoVoce]:
        # L'elenco arriva dalla rete: lo si chiede una volta sola.
        if self._voci is None:
            self._voci = await edge_tts.list_voices()
        return [
            InfoVoce(v["ShortName"], v["Gender"], v["Locale"])
            for v in self._voci
            if v["Locale"].split("-")[0] == lingua
        ]
