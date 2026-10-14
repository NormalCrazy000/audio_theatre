"""Render: dai segmenti del piano produce l'audio, usando il TTS."""

import asyncio
from collections.abc import Callable
from io import BytesIO

from pydub import AudioSegment

from copione_audio.piano import Parla, Pausa, Segmento, Silenzio
from copione_audio.tts import TTSEngine, Voce

Progresso = Callable[[int, int], None]
"""Riceve (sintesi completate, sintesi totali)."""


def _letture(segmenti: list[Segmento]) -> list[tuple[str, str]]:
    """Le coppie (personaggio, testo) da sintetizzare, senza ripetizioni."""
    letture = (
        (s.personaggio, s.testo)
        for s in segmenti
        if isinstance(s, (Parla, Pausa)) and s.testo
    )
    return list(dict.fromkeys(letture))


async def _sintetizza_tutte(
    letture: list[tuple[str, str]],
    voci: dict[str, Voce],
    motore: TTSEngine,
    progresso: Progresso | None,
    parallelo: int,
) -> dict[tuple[str, str], AudioSegment]:
    limite = asyncio.Semaphore(parallelo)
    completate = 0

    async def una(personaggio: str, testo: str) -> AudioSegment:
        nonlocal completate
        async with limite:
            dati = await motore.sintetizza(testo, voci[personaggio])
        completate += 1
        if progresso:
            progresso(completate, len(letture))
        # La decodifica chiama ffmpeg: in un thread per non bloccare il loop.
        return await asyncio.to_thread(
            AudioSegment.from_file, BytesIO(dati), format=motore.formato
        )

    audio = await asyncio.gather(*(una(p, t) for p, t in letture))
    return dict(zip(letture, audio))


async def render(
    segmenti: list[Segmento],
    voci: dict[str, Voce],
    motore: TTSEngine,
    progresso: Progresso | None = None,
    parallelo: int = 4,
) -> AudioSegment:
    """
    Sintetizza le letture dei segmenti e le unisce in un unico audio.

    :param voci: La voce di ogni personaggio che compare nei segmenti.
    :param progresso: Chiamata dopo ogni sintesi completata.
    :param parallelo: Quante sintesi eseguire contemporaneamente.
    :raises ValueError: Se manca la voce di un personaggio.
    """
    letture = _letture(segmenti)
    mancanti = sorted({p for p, _ in letture} - voci.keys())
    if mancanti:
        raise ValueError(f"voce mancante per: {', '.join(mancanti)}")

    audio = await _sintetizza_tutte(letture, voci, motore, progresso, parallelo)

    risultato = AudioSegment.empty()
    for s in segmenti:
        match s:
            case Parla():
                risultato += audio[(s.personaggio, s.testo)]
            case Silenzio():
                risultato += AudioSegment.silent(round(s.secondi * 1000))
            case Pausa():
                durata_s = len(audio[(s.personaggio, s.testo)]) / 1000 if s.testo else 0
                secondi = min(max(durata_s * s.moltiplicatore, s.min_s), s.max_s)
                risultato += AudioSegment.silent(round(secondi * 1000))
    return risultato
