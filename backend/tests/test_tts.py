import asyncio

from audio_theatre.tts import InfoVoce, Voce, assegna_voci
import json

from audio_theatre.tts.cache import CacheTTS
import io

import pytest

from audio_theatre.tts.piper import PiperTTS, _percentuale
from audio_theatre.tts.voci_piper import aggiungi_file, elimina_voce, voci_installate

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
        configurazione = {"language": {"code": codice}, "phoneme_id_map": {}}
        (tmp_path / f"{nome}.onnx.json").write_text(json.dumps(configurazione))
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


CONFIGURAZIONE = json.dumps({"language": {"code": "it_IT"}, "phoneme_id_map": {}}).encode()


@pytest.mark.parametrize(
    "nome, contenuto, messaggio",
    [
        ("it_IT-paola-medium (1).onnx", b"\x08", "nome non riconosciuto"),
        ("../it_IT-paola-medium.onnx", b"\x08", None),  # il percorso viene ignorato
        ("it_IT-paola-medium.onnx", b"<html>", "non sembra un modello ONNX"),
        ("it_IT-paola-medium.onnx", b"", "non sembra un modello ONNX"),
        ("it_IT-paola-medium.onnx.json", b"{", "JSON non valido"),
        ("it_IT-paola-medium.onnx.json", b'{"language": {}}', "JSON non valido"),
    ],
)
def test_aggiungi_file_controlla_nome_e_contenuto(tmp_path, nome, contenuto, messaggio):
    if messaggio is None:
        assert aggiungi_file(tmp_path, nome, io.BytesIO(contenuto)) == "it_IT-paola-medium"
        assert (tmp_path / "it_IT-paola-medium.onnx").exists()
    else:
        with pytest.raises(ValueError, match=messaggio):
            aggiungi_file(tmp_path, nome, io.BytesIO(contenuto))
        assert [f.name for f in tmp_path.iterdir()] == []  # niente file temporanei rimasti


def test_voci_installate_e_eliminazione(tmp_path):
    aggiungi_file(tmp_path, "it_IT-paola-medium.onnx", io.BytesIO(b"\x08" * 1000))
    aggiungi_file(tmp_path, "it_IT-paola-medium.onnx.json", io.BytesIO(CONFIGURAZIONE))
    aggiungi_file(tmp_path, "it_IT-riccardo-x_low.onnx.json", io.BytesIO(CONFIGURAZIONE))
    voci = {v.nome: v for v in voci_installate(tmp_path)}
    assert voci["it_IT-paola-medium"].completa and voci["it_IT-paola-medium"].genere == "Female"
    assert not voci["it_IT-riccardo-x_low"].completa and not voci["it_IT-riccardo-x_low"].modello
    assert [v.nome for v in asyncio.run(PiperTTS(tmp_path).voci("it"))] == ["it_IT-paola-medium"]

    elimina_voce(tmp_path, "it_IT-paola-medium")
    assert [v.nome for v in voci_installate(tmp_path)] == ["it_IT-riccardo-x_low"]
    with pytest.raises(ValueError):
        elimina_voce(tmp_path, "../voci")
