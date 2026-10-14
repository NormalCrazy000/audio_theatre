import asyncio

from copione_audio.tts import InfoVoce, Voce, assegna_voci
from copione_audio.tts.cache import CacheTTS

DISPONIBILI = [
    InfoVoce("M1", "Male", "it-IT"),
    InfoVoce("M2", "Male", "it-IT"),
    InfoVoce("F1", "Female", "it-IT"),
]


def test_assegna_voci_alterna_i_generi_e_poi_cambia_tono():
    voci = assegna_voci(["A", "B", "C", "D", "E"], DISPONIBILI)
    assert voci == {
        "A": Voce("M1"),
        "B": Voce("F1"),
        "C": Voce("M2"),
        "D": Voce("M1", tono="-12Hz"),
        "E": Voce("F1", tono="-12Hz"),
    }


def test_cache_evita_la_seconda_sintesi(finto_tts, tmp_path):
    cache = CacheTTS(finto_tts, tmp_path)
    primo = asyncio.run(cache.sintetizza("ciao", Voce("a")))
    secondo = asyncio.run(cache.sintetizza("ciao", Voce("a")))
    asyncio.run(cache.sintetizza("ciao", Voce("a", tono="+12Hz")))
    assert primo == secondo
    assert len(finto_tts.richieste) == 2
    assert not list(tmp_path.rglob("*.tmp"))
