import asyncio

import pytest

from copione_audio.piano import Parla, Pausa, Silenzio
from copione_audio.render import render
from copione_audio.tts import Voce

VOCI = {"A": Voce("a"), "B": Voce("b")}


def esegui(segmenti, motore, **kwargs):
    return asyncio.run(render(segmenti, VOCI, motore, **kwargs))


def test_durate(finto_tts):
    segmenti = [
        Parla("B", "due parole"),  # 2 s
        Silenzio(0.5),
        Pausa("A", "tre parole qui", 1.5, 1, 30),  # 3 s × 1.5
        Pausa("A", "", 1.5, 1, 30),  # soli gesti: minimo
        Pausa("A", "uno", 1.0, 2, 30),  # 1 s, alzato al minimo
        Pausa("A", "a " * 40, 1.0, 1, 30),  # 40 s, tagliato al massimo
    ]
    audio = esegui(segmenti, finto_tts)
    assert len(audio) == 2000 + 500 + 4500 + 1000 + 2000 + 30000


def test_ogni_lettura_sintetizzata_una_volta(finto_tts):
    progresso = []
    segmenti = [Parla("B", "ciao"), Parla("B", "ciao"), Pausa("A", "io", 1, 0, 9)]
    esegui(segmenti, finto_tts, progresso=lambda f, t: progresso.append((f, t)))
    assert sorted(finto_tts.richieste, key=lambda r: r[0]) == [
        ("ciao", Voce("b")),
        ("io", Voce("a")),
    ]
    assert sorted(progresso) == [(1, 2), (2, 2)]


def test_voce_mancante(finto_tts):
    with pytest.raises(ValueError, match="voce mancante per: C"):
        esegui([Parla("C", "ciao")], finto_tts)
