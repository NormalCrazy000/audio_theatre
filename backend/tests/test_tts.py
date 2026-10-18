import asyncio

from copione_audio.tts import InfoVoce, Voce, assegna_voci
import json

from copione_audio.tts.cache import CacheTTS
from copione_audio.tts.piper import PiperTTS, _percentuale

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


def test_piper_elenca_le_voci_installate(tmp_path):
    def voce(nome: str, codice: str, modello: bool = True):
        (tmp_path / f"{nome}.onnx.json").write_text(json.dumps({"language": {"code": codice}}))
        if modello:
            (tmp_path / f"{nome}.onnx").write_bytes(b"")

    voce("it_IT-paola-medium", "it_IT")
    voce("it_IT-nuova-low", "it_IT")
    voce("it_IT-riccardo-x_low", "it_IT", modello=False)  # download incompleto
    voce("en_US-lessac-medium", "en_US")
    (tmp_path / "rotta.onnx.json").write_text("{")
    (tmp_path / "rotta.onnx").write_bytes(b"")

    voci = asyncio.run(PiperTTS(tmp_path).voci("it"))
    assert voci == [
        InfoVoce("it_IT-nuova-low", "Unknown", "it-IT"),
        InfoVoce("it_IT-paola-medium", "Female", "it-IT"),
    ]
    assert asyncio.run(PiperTTS(tmp_path / "assente").voci("it")) == []


def test_percentuale():
    assert _percentuale("+12Hz", "Hz") == 12
    assert _percentuale("-10%", "%") == -10
    assert _percentuale("boh", "Hz") == 0
