"""Modello dati del copione nel formato standard (vedi docs/formato-copione.md)."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Battuta:
    """
    Una battuta, detta da uno o più personaggi insieme.

    :param personaggi: Chi la dice, nell'ordine scritto nel file.
    :param testo: Il testo, con le righe di continuazione unite da uno spazio.
    :param riga: Numero di riga (da 1) in cui inizia.
    :param pausa_s: Override della pausa in secondi (`[pausa=N]`), se presente.
    """

    personaggi: tuple[str, ...]
    testo: str
    riga: int
    pausa_s: float | None = None


@dataclass(frozen=True)
class Didascalia:
    """Una didascalia, scritta tra parentesi su una riga sola."""

    testo: str
    riga: int


type Elemento = Battuta | Didascalia


@dataclass
class Scena:
    """
    Una scena, aperta da una riga `# titolo`. Gli elementi prima del primo
    titolo stanno in una scena senza titolo (`titolo` è None).
    """

    titolo: str | None
    riga: int | None
    elementi: list[Elemento] = field(default_factory=list)

    @property
    def battute(self) -> list[Battuta]:
        return [e for e in self.elementi if isinstance(e, Battuta)]


@dataclass
class Copione:
    """Un copione completo: intestazione e scene in ordine."""

    titolo: str
    lingua: str
    personaggi: list[str]
    scene: list[Scena] = field(default_factory=list)

    @property
    def battute(self) -> list[Battuta]:
        return [b for scena in self.scene for b in scena.battute]


@dataclass(frozen=True)
class Errore:
    """
    Un problema trovato nel copione.

    :param riga: Numero di riga (da 1); None se riguarda il file intero.
    :param messaggio: Descrizione in italiano, da mostrare all'utente.
    """

    riga: int | None
    messaggio: str

    def __str__(self) -> str:
        return f"riga {self.riga}: {self.messaggio}" if self.riga else self.messaggio
