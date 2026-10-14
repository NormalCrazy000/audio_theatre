import pytest

from copione_audio.copione import Battuta, Didascalia, analizza, leggi_copione

INTESTAZIONE = """\
---
titolo: Romeo e Giulietta
lingua: it
personaggi: ROMEO, GIULIETTA, BALIA
---
"""

ESEMPIO = (
    INTESTAZIONE
    + """
# Atto I – Scena 5

(Una sala in casa Capuleti)

ROMEO: Se profano con la mia mano indegna
  questo sacro altare, il peccato è gentile.
GIULIETTA: Buon pellegrino, fate torto alla vostra mano.
BALIA [pausa=4]: Signora, vostra madre vuole parlarvi.
"""
)


def messaggi(testo: str) -> list[str]:
    """Gli errori di `analizza` come stringhe `riga N: messaggio`."""
    return [str(e) for e in analizza(testo)[1]]


def test_esempio_della_specifica():
    copione, errori = analizza(ESEMPIO)

    assert errori == []
    assert copione.titolo == "Romeo e Giulietta"
    assert copione.lingua == "it"
    assert copione.personaggi == ["ROMEO", "GIULIETTA", "BALIA"]
    assert len(copione.scene) == 1
    scena = copione.scene[0]
    assert (scena.titolo, scena.riga) == ("Atto I – Scena 5", 7)
    assert scena.elementi == [
        Didascalia("Una sala in casa Capuleti", 9),
        Battuta(
            ("ROMEO",),
            "Se profano con la mia mano indegna "
            "questo sacro altare, il peccato è gentile.",
            11,
        ),
        Battuta(("GIULIETTA",), "Buon pellegrino, fate torto alla vostra mano.", 13),
        Battuta(("BALIA",), "Signora, vostra madre vuole parlarvi.", 14, 4.0),
    ]


@pytest.mark.parametrize(
    ("riga", "personaggi"),
    [
        ("ROMEO e GIULIETTA: Addio!", ("ROMEO", "GIULIETTA")),
        ("ROMEO, BALIA e GIULIETTA: Addio!", ("ROMEO", "BALIA", "GIULIETTA")),
        ("ROMEO,GIULIETTA: Addio!", ("ROMEO", "GIULIETTA")),
    ],
)
def test_battuta_detta_insieme(riga, personaggi):
    copione, errori = analizza(INTESTAZIONE + riga)
    assert errori == []
    assert copione.battute[0].personaggi == personaggi


def test_pausa_con_virgola_decimale():
    copione, _ = analizza(INTESTAZIONE + "ROMEO [pausa=2,5]: Ciao")
    assert copione.battute[0].pausa_s == 2.5


def test_battute_prima_del_primo_titolo_in_scena_senza_titolo():
    copione, errori = analizza(INTESTAZIONE + "ROMEO: Uno\n# Scena 2\nBALIA: Due")
    assert errori == []
    assert [(s.titolo, len(s.battute)) for s in copione.scene] == [
        (None, 1),
        ("Scena 2", 1),
    ]


def test_continuazione_dopo_riga_vuota_e_con_tab():
    copione, _ = analizza(INTESTAZIONE + "ROMEO: Uno\n\n\tdue\n   tre")
    assert copione.battute[0].testo == "Uno due tre"


def test_testo_tutto_nella_continuazione():
    copione, errori = analizza(INTESTAZIONE + "ROMEO:\n  Solo qui.")
    assert errori == []
    assert copione.battute[0].testo == "Solo qui."


def test_bom_iniziale_ignorato():
    assert analizza("﻿" + ESEMPIO)[1] == []


def test_due_punti_nel_testo_della_battuta():
    copione, _ = analizza(INTESTAZIONE + "ROMEO: Ascolta: ti amo.")
    assert copione.battute[0].testo == "Ascolta: ti amo."


# --- Errori ---


def test_nome_non_dichiarato():
    assert messaggi(INTESTAZIONE + "TEBALDO: Chi va là?") == [
        "riga 6: personaggio 'TEBALDO' non dichiarato nell'intestazione"
    ]


def test_nome_non_dichiarato_in_battuta_insieme():
    assert messaggi(INTESTAZIONE + "ROMEO e TEBALDO: Chi va là?") == [
        "riga 6: personaggio 'TEBALDO' non dichiarato nell'intestazione"
    ]


def test_battuta_vuota():
    assert messaggi(INTESTAZIONE + "ROMEO: Ciao\nBALIA:") == ["riga 7: battuta vuota"]


def test_riga_non_riconosciuta():
    assert messaggi(INTESTAZIONE + "ROMEO: Ciao\nsenza due punti") == [
        "riga 7: riga non riconosciuta: 'senza due punti'"
    ]


def test_riga_indentata_fuori_da_una_battuta():
    assert messaggi(INTESTAZIONE + "# Scena\n  orfana\nROMEO: Ciao") == [
        "riga 7: riga indentata fuori da una battuta"
    ]


def test_opzione_non_valida():
    copione, errori = analizza(INTESTAZIONE + "ROMEO [pausa=tanto]: Ciao")
    assert [str(e) for e in errori] == [
        "riga 6: opzione non valida '[pausa=tanto]', atteso [pausa=SECONDI]"
    ]
    assert copione.battute[0].pausa_s is None


def test_titolo_di_scena_vuoto():
    assert messaggi(INTESTAZIONE + "#\nROMEO: Ciao") == [
        "riga 6: titolo di scena vuoto"
    ]


def test_senza_intestazione():
    copione, errori = analizza("ROMEO: Ciao")
    assert [str(e) for e in errori] == ["manca l'intestazione tra '---'"]
    assert copione.battute[0].testo == "Ciao"


def test_intestazione_non_chiusa():
    assert messaggi("---\ntitolo: X\nROMEO: Ciao") == [
        "il copione non contiene battute",
        "riga 1: intestazione non chiusa da '---'",
    ]


def test_intestazione_incompleta_e_chiavi_sbagliate():
    testo = "---\ntitolo: X\nautore: Shakespeare\ntitolo: Y\n---\nROMEO: Ciao"
    assert messaggi(testo) == [
        "riga 1: manca 'lingua' nell'intestazione",
        "riga 1: manca 'personaggi' nell'intestazione",
        "riga 3: riga dell'intestazione non valida: 'autore: Shakespeare' "
        "(chiavi ammesse: titolo, lingua, personaggi)",
        "riga 4: chiave 'titolo' ripetuta",
    ]


def test_personaggio_ripetuto_nell_intestazione():
    testo = INTESTAZIONE.replace("BALIA", "BALIA, ROMEO") + "ROMEO: Ciao"
    assert messaggi(testo) == ["personaggio 'ROMEO' ripetuto nell'intestazione"]


def test_copione_vuoto():
    assert messaggi(INTESTAZIONE) == ["il copione non contiene battute"]


def test_leggi_copione_non_valida_il_contenuto():
    _, errori = leggi_copione(INTESTAZIONE + "TEBALDO:")
    assert errori == []
