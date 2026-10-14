"""Formato standard del copione: modello, parser e validator."""

from copione_audio.copione.model import (
    Battuta,
    Copione,
    Didascalia,
    Elemento,
    Errore,
    Scena,
)
from copione_audio.copione.parser import leggi_copione
from copione_audio.copione.validator import valida

__all__ = [
    "Battuta",
    "Copione",
    "Didascalia",
    "Elemento",
    "Errore",
    "Scena",
    "analizza",
    "leggi_copione",
    "valida",
]


def analizza(testo: str) -> tuple[Copione, list[Errore]]:
    """
    Legge e valida un copione.

    :param testo: Il contenuto del file `.copione.txt`.
    :return: Il copione e tutti gli errori (prima quelli senza riga, poi per riga).
    """
    copione, errori = leggi_copione(testo)
    errori += valida(copione)
    return copione, sorted(errori, key=lambda e: (e.riga is not None, e.riga or 0))
