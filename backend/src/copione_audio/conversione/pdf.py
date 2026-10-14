from pathlib import Path

from pypdf import PdfReader


def estrai_testo(percorso_pdf: Path) -> str:
    """
    Estrae il testo grezzo da un PDF, una pagina dopo l'altra.

    :param percorso_pdf: Percorso del file PDF.
    :return: Il testo di tutte le pagine, separate da un a capo.
    """
    reader = PdfReader(percorso_pdf)
    return "".join((pagina.extract_text() or "") + "\n" for pagina in reader.pages)
