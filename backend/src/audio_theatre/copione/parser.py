"""
Parser del formato standard del copione (vedi docs/formato-copione.md).

Il parser non si ferma al primo problema: restituisce il copione ricostruito
al meglio insieme a tutti gli errori di sintassi trovati.
"""

import re
from dataclasses import replace

from audio_theatre.copione.model import Battuta, Copione, Didascalia, Errore, Scena

DELIMITATORE = "---"
CHIAVI_INTESTAZIONE = ("titolo", "lingua", "personaggi")

# NOMI [opzioni]: testo — i nomi non iniziano con spazio, "(" o "#".
RE_BATTUTA = re.compile(
    r"^(?P<nomi>[^\s:\[\]()#][^:\[\]]*?)\s*"
    r"(?:\[(?P<opzioni>[^\]]*)\])?\s*:\s*(?P<testo>.*)$"
)
# Separa "ROMEO e GIULIETTA" e "ROMEO, BALIA e GIULIETTA".
RE_SEPARATORE_NOMI = re.compile(r"\s*,\s*|\s+e\s+")
RE_PAUSA = re.compile(r"pausa\s*=\s*(?P<secondi>\d+(?:[.,]\d+)?)")


def leggi_copione(testo: str) -> tuple[Copione, list[Errore]]:
    """
    Legge un copione nel formato standard.

    :param testo: Il contenuto del file `.copione.txt`.
    :return: Il copione e gli errori di sintassi, in ordine di riga.
    """
    righe = testo.removeprefix("\ufeff").splitlines()
    errori: list[Errore] = []
    intestazione, inizio_corpo = _leggi_intestazione(righe, errori)
    copione = Copione(
        titolo=intestazione.get("titolo", ""),
        lingua=intestazione.get("lingua", ""),
        personaggi=_dividi_nomi(intestazione.get("personaggi", "")),
    )
    copione.scene = _leggi_corpo(righe, inizio_corpo, errori)
    return copione, errori


def _leggi_intestazione(
    righe: list[str], errori: list[Errore]
) -> tuple[dict[str, str], int]:
    """
    Legge l'intestazione tra `---`.

    :return: Le chiavi lette e l'indice della prima riga del corpo.
    """
    inizio = next((i for i, r in enumerate(righe) if r.strip()), len(righe))
    if inizio == len(righe) or righe[inizio].strip() != DELIMITATORE:
        errori.append(Errore(None, f"manca l'intestazione tra '{DELIMITATORE}'"))
        return {}, inizio

    fine = next(
        (i for i in range(inizio + 1, len(righe)) if righe[i].strip() == DELIMITATORE),
        None,
    )
    if fine is None:
        errori.append(Errore(inizio + 1, f"intestazione non chiusa da '{DELIMITATORE}'"))
        return {}, len(righe)

    intestazione: dict[str, str] = {}
    for i in range(inizio + 1, fine):
        riga = righe[i].strip()
        if not riga:
            continue
        chiave, due_punti, valore = riga.partition(":")
        chiave = chiave.strip().lower()
        if not due_punti or chiave not in CHIAVI_INTESTAZIONE:
            errori.append(
                Errore(
                    i + 1,
                    f"riga dell'intestazione non valida: '{riga}' "
                    f"(chiavi ammesse: {', '.join(CHIAVI_INTESTAZIONE)})",
                )
            )
        elif chiave in intestazione:
            errori.append(Errore(i + 1, f"chiave '{chiave}' ripetuta"))
        else:
            intestazione[chiave] = valore.strip()

    for chiave in CHIAVI_INTESTAZIONE:
        if not intestazione.get(chiave):
            errori.append(Errore(inizio + 1, f"manca '{chiave}' nell'intestazione"))
    return intestazione, fine + 1


def _leggi_corpo(righe: list[str], inizio: int, errori: list[Errore]) -> list[Scena]:
    """Legge scene, battute e didascalie dalla riga di indice `inizio` in poi."""
    scene = [Scena(titolo=None, riga=None)]
    # Indica se l'ultimo elemento è una battuta che può continuare.
    battuta_aperta = False

    for i in range(inizio, len(righe)):
        numero, grezza = i + 1, righe[i]
        riga = grezza.strip()
        if not riga:
            continue

        if grezza[0] in " \t":
            if battuta_aperta:
                precedente = scene[-1].elementi[-1]
                testo = f"{precedente.testo} {riga}".strip()
                scene[-1].elementi[-1] = replace(precedente, testo=testo)
            else:
                errori.append(Errore(numero, "riga indentata fuori da una battuta"))
            continue

        battuta_aperta = False
        if riga.startswith("#"):
            titolo = riga.lstrip("#").strip()
            if not titolo:
                errori.append(Errore(numero, "titolo di scena vuoto"))
            scene.append(Scena(titolo=titolo, riga=numero))
        elif riga.startswith("(") and riga.endswith(")"):
            scene[-1].elementi.append(Didascalia(riga[1:-1].strip(), numero))
        elif battuta := _leggi_battuta(riga, numero, errori):
            scene[-1].elementi.append(battuta)
            battuta_aperta = True
        else:
            errori.append(Errore(numero, f"riga non riconosciuta: '{riga}'"))

    # La scena implicita iniziale si tiene solo se contiene qualcosa.
    if not scene[0].elementi:
        scene.pop(0)
    return scene


def _leggi_battuta(riga: str, numero: int, errori: list[Errore]) -> Battuta | None:
    """Legge una riga `NOMI [pausa=N]: testo`; None se non è una battuta."""
    m = RE_BATTUTA.match(riga)
    if not m:
        return None

    nomi = _dividi_nomi(m["nomi"])
    if len(nomi) != len(RE_SEPARATORE_NOMI.split(m["nomi"].strip())):
        errori.append(Errore(numero, f"nome vuoto in '{m['nomi'].strip()}'"))

    pausa_s = None
    if m["opzioni"] is not None:
        p = RE_PAUSA.fullmatch(m["opzioni"].strip())
        if p:
            pausa_s = float(p["secondi"].replace(",", "."))
        else:
            errori.append(
                Errore(
                    numero,
                    f"opzione non valida '[{m['opzioni']}]', atteso [pausa=SECONDI]",
                )
            )

    return Battuta(tuple(nomi), m["testo"].strip(), numero, pausa_s)


def _dividi_nomi(testo: str) -> list[str]:
    """Divide un elenco di nomi separati da virgole o da " e "."""
    return [n for n in RE_SEPARATORE_NOMI.split(testo.strip()) if n]
