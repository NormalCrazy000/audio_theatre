"""
Piano audio: dal copione e dalle opzioni calcola la sequenza di segmenti.

È una funzione pura: non usa il TTS né la rete. La durata delle pause che
dipendono dalla lettura (`Pausa`) viene risolta da `render.py`.
"""

import re
from dataclasses import dataclass
from typing import Literal

from copione_audio.copione import Battuta, Copione, Didascalia, Scena

NARRATORE = "NARRATORE"
"""Il "personaggio" che legge le didascalie quando `leggi_didascalie` è attivo."""

RE_PARENTESI = re.compile(r"\([^()]*\)")


@dataclass(frozen=True)
class Parla:
    """Il TTS legge `testo` con la voce di `personaggio`."""

    personaggio: str
    testo: str


@dataclass(frozen=True)
class Silenzio:
    """Silenzio di durata fissa."""

    secondi: float


@dataclass(frozen=True)
class Pausa:
    """
    Pausa per dire la propria battuta: dura quanto la lettura di `testo` con la
    voce di `personaggio`, per `moltiplicatore`, limitata tra `min_s` e `max_s`.
    Con `testo` vuoto (battuta di soli gesti) dura `min_s`.
    """

    personaggio: str
    testo: str
    moltiplicatore: float
    min_s: float
    max_s: float


type Segmento = Parla | Silenzio | Pausa


@dataclass(frozen=True)
class Opzioni:
    """
    Opzioni del piano (vedi REFACTOR.md, Fase 3).

    :param personaggio: Il personaggio da studiare.
    :param personaggi_inclusi: Gli altri personaggi da far sentire; None = tutti.
    :param modalita_battuta: "muta" (solo pausa) o "letta" (lettura, poi pausa).
    :param moltiplicatore: Durata della pausa rispetto alla lettura della battuta.
    :param pausa_min_s: Durata minima della pausa.
    :param pausa_max_s: Durata massima della pausa.
    :param contesto: Quante battute precedenti far sentire; None = scena intera.
    :param stacco_s: Silenzio tra un blocco e l'altro e tra le scene.
    :param respiro_s: Silenzio dopo ogni battuta letta.
    :param scene: Indici (da 0) delle scene da includere; None = tutte.
    :param leggi_didascalie: Se leggere le didascalie, anche quelle tra
        parentesi dentro le battute.
    """

    personaggio: str
    personaggi_inclusi: frozenset[str] | None = None
    modalita_battuta: Literal["muta", "letta"] = "muta"
    moltiplicatore: float = 1.2
    pausa_min_s: float = 1.5
    pausa_max_s: float = 30.0
    contesto: int | None = 3
    stacco_s: float = 1.5
    respiro_s: float = 0.4
    scene: frozenset[int] | None = None
    leggi_didascalie: bool = False


def testo_parlato(testo: str, leggi_didascalie: bool) -> str:
    """
    Il testo da far leggere al TTS: senza le parti tra parentesi, a meno che
    le didascalie vadano lette.
    """
    if leggi_didascalie:
        return testo
    return " ".join(RE_PARENTESI.sub(" ", testo).split())


def crea_piano(copione: Copione, opzioni: Opzioni) -> list[Segmento]:
    """
    Calcola la sequenza di segmenti audio per studiare `opzioni.personaggio`.

    Le scene in cui il personaggio non parla vengono saltate. Il contesto non
    attraversa i confini di scena.

    :raises ValueError: Se il personaggio non è dichiarato nel copione.
    """
    if opzioni.personaggio not in copione.personaggi:
        raise ValueError(f"personaggio '{opzioni.personaggio}' non presente nel copione")

    segmenti: list[Segmento] = []
    for indice, scena in enumerate(copione.scene):
        if opzioni.scene is not None and indice not in opzioni.scene:
            continue
        if not any(_e_mia(b, opzioni) for b in scena.battute):
            continue
        if opzioni.contesto is None:
            segmenti += _scena_intera(scena, opzioni)
        else:
            segmenti += _scena_a_blocchi(scena, opzioni)
    return segmenti


def _e_mia(battuta: Battuta, opzioni: Opzioni) -> bool:
    """Una battuta è mia se tra chi la dice c'è il personaggio studiato."""
    return opzioni.personaggio in battuta.personaggi


def _voce_altrui(battuta: Battuta, opzioni: Opzioni) -> str | None:
    """
    Il personaggio con cui leggere una battuta altrui: il primo tra quelli
    inclusi. None se la battuta non si sente (esclusa o di soli gesti).
    """
    if not testo_parlato(battuta.testo, opzioni.leggi_didascalie):
        return None
    for nome in battuta.personaggi:
        if opzioni.personaggi_inclusi is None or nome in opzioni.personaggi_inclusi:
            return nome
    return None


def _leggi(personaggio: str, testo: str, opzioni: Opzioni) -> list[Segmento]:
    """Lettura di un testo seguita dal respiro."""
    segmenti: list[Segmento] = [Parla(personaggio, testo)]
    if opzioni.respiro_s:
        segmenti.append(Silenzio(opzioni.respiro_s))
    return segmenti


def _segmenti_elemento(
    elemento: Battuta | Didascalia, opzioni: Opzioni, con_pausa: bool
) -> list[Segmento]:
    """
    I segmenti di un elemento della scena.

    :param con_pausa: Per le mie battute: True se è la battuta da studiare
        (pausa per ripeterla), False se fa solo da contesto.
    """
    if isinstance(elemento, Didascalia):
        if opzioni.leggi_didascalie and elemento.testo:
            return _leggi(NARRATORE, elemento.testo, opzioni)
        return []

    testo = testo_parlato(elemento.testo, opzioni.leggi_didascalie)
    if not _e_mia(elemento, opzioni):
        voce = _voce_altrui(elemento, opzioni)
        return _leggi(voce, testo, opzioni) if voce else []

    io = opzioni.personaggio
    letta = _leggi(io, testo, opzioni) if testo else []
    if not con_pausa:
        # Nel contesto una mia battuta precedente si sente solo in modalità "letta".
        return letta if opzioni.modalita_battuta == "letta" else []

    if elemento.pausa_s is not None:
        pausa: Segmento = Silenzio(elemento.pausa_s)
    else:
        pausa = Pausa(
            io, testo, opzioni.moltiplicatore, opzioni.pausa_min_s, opzioni.pausa_max_s
        )
    if opzioni.modalita_battuta == "letta":
        return letta + [pausa]
    return [pausa]


def _scena_intera(scena: Scena, opzioni: Opzioni) -> list[Segmento]:
    """La scena in ordine, una volta sola, seguita dallo stacco."""
    segmenti: list[Segmento] = []
    for elemento in scena.elementi:
        segmenti += _segmenti_elemento(elemento, opzioni, con_pausa=True)
    return segmenti + [Silenzio(opzioni.stacco_s)]


def _scena_a_blocchi(scena: Scena, opzioni: Opzioni) -> list[Segmento]:
    """
    Per ogni mia battuta, un blocco: le `contesto` battute altrui udibili
    precedenti (con quello che c'è in mezzo), la mia battuta, lo stacco.
    """
    elementi = scena.elementi
    segmenti: list[Segmento] = []
    for i, elemento in enumerate(elementi):
        if not (isinstance(elemento, Battuta) and _e_mia(elemento, opzioni)):
            continue
        inizio = _inizio_contesto(elementi, i, opzioni)
        for precedente in elementi[inizio:i]:
            segmenti += _segmenti_elemento(precedente, opzioni, con_pausa=False)
        segmenti += _segmenti_elemento(elemento, opzioni, con_pausa=True)
        segmenti.append(Silenzio(opzioni.stacco_s))
    return segmenti


def _inizio_contesto(
    elementi: list[Battuta | Didascalia], i: int, opzioni: Opzioni
) -> int:
    """
    Indice da cui parte il contesto della battuta `i`: risale fino alla
    `contesto`-esima battuta altrui udibile, senza uscire dalla scena.
    """
    if not opzioni.contesto:
        return i
    trovate = 0
    for j in range(i - 1, -1, -1):
        e = elementi[j]
        if (
            isinstance(e, Battuta)
            and not _e_mia(e, opzioni)
            and _voce_altrui(e, opzioni)
        ):
            trovate += 1
            if trovate == opzioni.contesto:
                return j
    return 0
