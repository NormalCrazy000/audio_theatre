"""
Generazione audio dal testo con separatori inseriti a mano.

Modulo provvisorio: verrà sostituito da `piano.py` e `render.py` (Fase 3 di
REFACTOR.md), che lavorano sul formato standard del copione.
"""

from collections.abc import Callable
from io import BytesIO

from gtts import gTTS
from pydub import AudioSegment

Sintetizzatore = Callable[[str, str], AudioSegment]


def dividi_testo(testo: str, separatore: str | None) -> list[str]:
    """
    Divide il testo in frasi sul separatore, scartando le parti vuote.

    :param testo: Il testo completo.
    :param separatore: Il separatore; con None il testo resta intero.
    :return: Le frasi, senza spazi iniziali e finali.
    """
    parti = testo.split(separatore) if separatore else [testo]
    return [parte.strip() for parte in parti if parte.strip()]


def sintetizza(frase: str, lingua: str) -> AudioSegment:
    """
    Legge una frase con gTTS (richiede internet) e restituisce l'audio.

    :param frase: Il testo da leggere.
    :param lingua: Codice della lingua (es. "it").
    """
    buffer = BytesIO()
    gTTS(text=frase, lang=lingua).write_to_fp(buffer)
    buffer.seek(0)
    return AudioSegment.from_file(buffer, format="mp3")


def testo_ad_audio(
    testo: str,
    lingua: str,
    separatore: str | None,
    silenzio_ms: int,
    sintetizzatore: Sintetizzatore = sintetizza,
) -> AudioSegment:
    """
    Converte il testo in un unico audio. Se c'è un separatore, dopo ogni frase
    aggiunge un silenzio in cui ripetere la battuta.

    :param testo: Il testo completo.
    :param lingua: Codice della lingua per il TTS.
    :param separatore: Il separatore delle frasi; con None nessuna pausa.
    :param silenzio_ms: Durata di ogni pausa in millisecondi.
    :param sintetizzatore: Funzione `(frase, lingua) -> audio`; sostituibile nei test.
    """
    audio = AudioSegment.empty()
    for frase in dividi_testo(testo, separatore):
        audio += sintetizzatore(frase, lingua)
        if separatore:
            audio += AudioSegment.silent(duration=silenzio_ms)
    return audio
