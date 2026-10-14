from dataclasses import replace

import pytest

from copione_audio.copione import analizza
from copione_audio.piano import (
    NARRATORE,
    Opzioni,
    Parla,
    Pausa,
    Silenzio,
    crea_piano,
    testo_parlato,
)

COPIONE = """\
---
titolo: Prova
lingua: it
personaggi: A, B, C
---
# Scena 1
(Entra A)
B: Uno.
C: Due.
A: (ride) Tre.
B: Quattro.
A [pausa=5]: Cinque.
# Scena 2
B: Sei.
C: Sette.
# Scena 3
C: Otto.
A e B: Nove.
A: (annuisce)
"""

# Senza respiro e con stacco riconoscibile, per sequenze leggibili.
BASE = Opzioni(personaggio="A", respiro_s=0, stacco_s=9)


def piano(**modifiche):
    copione, errori = analizza(COPIONE)
    assert errori == []
    return crea_piano(copione, replace(BASE, **modifiche))


def pausa(testo: str) -> Pausa:
    return Pausa("A", testo, BASE.moltiplicatore, BASE.pausa_min_s, BASE.pausa_max_s)


STACCO = Silenzio(9)


def test_testo_parlato_toglie_le_didascalie():
    assert testo_parlato("(ride) Ciao (piano) a te.", False) == "Ciao a te."
    assert testo_parlato("(ride) Ciao", True) == "(ride) Ciao"
    assert testo_parlato("(annuisce)", False) == ""


def test_contesto_1_muta():
    assert piano(contesto=1) == [
        # Scena 1
        Parla("C", "Due."), pausa("Tre."), STACCO,
        Parla("B", "Quattro."), Silenzio(5), STACCO,
        # Scena 2 saltata: A non parla. Scena 3:
        Parla("C", "Otto."), pausa("Nove."), STACCO,
        # La battuta di soli gesti ha comunque la sua pausa.
        Parla("C", "Otto."), pausa(""), STACCO,
    ]  # fmt: skip


def test_contesto_non_attraversa_le_scene():
    segmenti = piano(contesto=10, scene=frozenset({2}))
    assert segmenti[0] == Parla("C", "Otto.")


def test_contesto_2_include_le_mie_battute_lette_in_mezzo():
    segmenti = piano(contesto=2, modalita_battuta="letta", scene=frozenset({0}))
    assert segmenti == [
        Parla("B", "Uno."), Parla("C", "Due."),
        Parla("A", "Tre."), pausa("Tre."), STACCO,
        # Contesto: C, la mia battuta precedente (letta, senza pausa), B.
        Parla("C", "Due."), Parla("A", "Tre."), Parla("B", "Quattro."),
        Parla("A", "Cinque."), Silenzio(5), STACCO,
    ]  # fmt: skip


def test_contesto_muta_salta_le_mie_battute_precedenti():
    segmenti = piano(contesto=2, scene=frozenset({0}))
    assert segmenti[4:] == [
        Parla("C", "Due."), Parla("B", "Quattro."), Silenzio(5), STACCO,
    ]  # fmt: skip


def test_contesto_zero():
    assert piano(contesto=0, scene=frozenset({0})) == [
        pausa("Tre."), STACCO, Silenzio(5), STACCO,
    ]  # fmt: skip


def test_scena_intera():
    assert piano(contesto=None) == [
        Parla("B", "Uno."), Parla("C", "Due."), pausa("Tre."),
        Parla("B", "Quattro."), Silenzio(5), STACCO,
        Parla("C", "Otto."), pausa("Nove."), pausa(""), STACCO,
    ]  # fmt: skip


def test_personaggi_esclusi_saltati_e_non_contati_nel_contesto():
    segmenti = piano(
        contesto=1, personaggi_inclusi=frozenset({"B"}), scene=frozenset({0})
    )
    assert segmenti == [
        Parla("B", "Uno."), pausa("Tre."), STACCO,
        Parla("B", "Quattro."), Silenzio(5), STACCO,
    ]  # fmt: skip


def test_battuta_insieme_altrui_letta_dal_primo_incluso():
    copione, _ = analizza(COPIONE)
    segmenti = crea_piano(copione, replace(BASE, personaggio="C", contesto=1))
    assert Parla("A", "Nove.") not in segmenti
    assert Parla("B", "Nove.") not in segmenti  # "A e B" è dopo l'ultima di C
    segmenti = crea_piano(
        copione,
        replace(BASE, personaggio="C", contesto=None, personaggi_inclusi=frozenset({"B"})),
    )
    assert Parla("B", "Nove.") in segmenti


def test_leggi_didascalie():
    segmenti = piano(contesto=None, leggi_didascalie=True, scene=frozenset({0}))
    assert segmenti[:2] == [Parla(NARRATORE, "Entra A"), Parla("B", "Uno.")]
    assert pausa("(ride) Tre.") in segmenti


def test_respiro_dopo_ogni_lettura():
    segmenti = piano(contesto=1, respiro_s=0.4, scene=frozenset({2}))
    assert segmenti[:2] == [Parla("C", "Otto."), Silenzio(0.4)]


def test_personaggio_sconosciuto():
    with pytest.raises(ValueError, match="'Z'"):
        piano(personaggio="Z")
