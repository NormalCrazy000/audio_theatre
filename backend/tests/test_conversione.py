from audio_theatre.conversione.base import ISTRUZIONI


def test_istruzioni_di_conversione_nel_pacchetto():
    assert ISTRUZIONI.is_file()
    assert "formato-copione.md" in ISTRUZIONI.read_text(encoding="utf-8")
