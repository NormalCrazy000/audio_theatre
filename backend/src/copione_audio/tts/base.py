from dataclasses import dataclass
from itertools import zip_longest
from typing import Protocol

# Variazioni di tono per distinguere i personaggi che condividono una voce.
TONI = ("+0Hz", "-12Hz", "+12Hz", "-24Hz", "+24Hz")


@dataclass(frozen=True)
class Voce:
    """
    Una voce con cui leggere un personaggio.

    :param nome: Il nome della voce nel motore (es. "it-IT-ElsaNeural").
    :param tono: Variazione di tono, es. "+0Hz" o "-12Hz".
    :param velocita: Variazione di velocità, es. "+0%" o "-10%".
    """

    nome: str
    tono: str = "+0Hz"
    velocita: str = "+0%"


@dataclass(frozen=True)
class InfoVoce:
    """Una voce offerta dal motore."""

    nome: str
    genere: str
    lingua: str


class TTSEngine(Protocol):
    """Un motore di sintesi vocale."""

    formato: str
    """Formato audio dei byte restituiti da `sintetizza` (es. "mp3")."""

    async def sintetizza(self, testo: str, voce: Voce) -> bytes:
        """Legge `testo` con `voce` e restituisce l'audio."""
        ...

    async def voci(self, lingua: str) -> list[InfoVoce]:
        """Le voci disponibili per la lingua (es. "it")."""
        ...


def assegna_voci(personaggi: list[str], disponibili: list[InfoVoce]) -> dict[str, Voce]:
    """
    Assegna una voce a ogni personaggio, alternando i generi. Quando le voci
    finiscono ricomincia dalla prima cambiando il tono.

    :raises ValueError: Se non ci sono voci disponibili.
    """
    if not disponibili:
        raise ValueError("nessuna voce disponibile")
    maschili = [v for v in disponibili if v.genere == "Male"]
    altre = [v for v in disponibili if v.genere != "Male"]
    ordine = [v for coppia in zip_longest(maschili, altre) for v in coppia if v]

    voci = {}
    for i, nome in enumerate(personaggi):
        giro, posizione = divmod(i, len(ordine))
        voci[nome] = Voce(ordine[posizione].nome, tono=TONI[giro % len(TONI)])
    return voci
