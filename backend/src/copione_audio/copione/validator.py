"""Controlli sul contenuto di un copione già letto dal parser."""

from collections import Counter

from copione_audio.copione.model import Copione, Errore


def valida(copione: Copione) -> list[Errore]:
    """
    Controlla il copione: personaggi ripetuti nell'intestazione, nomi non
    dichiarati, battute vuote e copione senza battute.

    :return: Gli errori trovati, in ordine di riga.
    """
    errori = [
        Errore(None, f"personaggio '{nome}' ripetuto nell'intestazione")
        for nome, volte in Counter(copione.personaggi).items()
        if volte > 1
    ]

    dichiarati = set(copione.personaggi)
    for battuta in copione.battute:
        for nome in battuta.personaggi:
            # Senza elenco il parser ha già segnalato "manca 'personaggi'".
            if dichiarati and nome not in dichiarati:
                errori.append(
                    Errore(
                        battuta.riga,
                        f"personaggio '{nome}' non dichiarato nell'intestazione",
                    )
                )
        if not battuta.testo:
            errori.append(Errore(battuta.riga, "battuta vuota"))

    if not copione.battute:
        errori.append(Errore(None, "il copione non contiene battute"))
    return errori
