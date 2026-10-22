from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader


def estrai_testo(percorso_pdf: Path | BinaryIO) -> str:
    """
    Estrae il testo grezzo da un PDF, una pagina dopo l'altra.

    :param percorso_pdf: Percorso del file PDF, oppure il file già aperto in binario.
    :return: Il testo di tutte le pagine, separate da un a capo.
    """
    reader = PdfReader(percorso_pdf)
    return "".join((pagina.extract_text() or "") + "\n" for pagina in reader.pages)
