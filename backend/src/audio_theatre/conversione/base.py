from pathlib import Path
from typing import Protocol

ISTRUZIONI = Path(__file__).with_name("istruzioni.md")


class Converter(Protocol):
    """
    Converte il testo grezzo di un copione (per esempio estratto da un PDF) nel
    formato standard (docs/formato-copione.md).

    Le implementazioni seguono le regole di `istruzioni.md`, le stesse usate
    dalla skill `converti-copione`.
    """

    def converti(self, testo_grezzo: str) -> str:
        """
        :param testo_grezzo: Il testo così come è stato estratto.
        :return: Il contenuto del file `.copione.txt`.
        """
        ...
