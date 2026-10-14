from pydub import AudioSegment

from copione_audio.testo_audio import dividi_testo, testo_ad_audio


def finto_sintetizzatore(frase: str, lingua: str) -> AudioSegment:
    """Restituisce 100 ms di silenzio per ogni frase, senza rete."""
    return AudioSegment.silent(duration=100)


def test_dividi_testo_sul_separatore():
    assert dividi_testo("ciao & come stai &  bene ", "&") == [
        "ciao",
        "come stai",
        "bene",
    ]


def test_dividi_testo_scarta_parti_vuote():
    assert dividi_testo("a && b &\n& ", "&") == ["a", "b"]


def test_dividi_testo_senza_separatore():
    assert dividi_testo(" tutto & intero ", None) == ["tutto & intero"]


def test_testo_ad_audio_con_pause():
    audio = testo_ad_audio("a & b", "it", "&", 500, finto_sintetizzatore)
    assert len(audio) == 2 * (100 + 500)


def test_testo_ad_audio_senza_pause():
    audio = testo_ad_audio("a & b", "it", None, 500, finto_sintetizzatore)
    assert len(audio) == 100
