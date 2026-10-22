import time
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

import json

from audio_theatre.api import main
from audio_theatre.api.main import Lavoro, cartella_voci_piper, crea_app, motori_tts
from audio_theatre.tts.piper import PiperTTS

COPIONE = """\
---
titolo: Prova: uno
lingua: it
personaggi: A, B
---
# Scena 1
B: Ciao a te.
A: (ride) Ciao.
# Scena 2
B: Solo io.
"""


@pytest.fixture
def client(tmp_path, finto_tts):
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path / "assente")
    app.dependency_overrides[motori_tts] = lambda: {"edge": finto_tts, "piper": finto_tts}
    with TestClient(app, base_url="http://localhost") as client:
        yield client


def aspetta(client, id: str) -> dict:
    """Interroga lo stato finché il lavoro non è finito."""
    for _ in range(100):
        stato = client.get(f"/api/audio/{id}").json()
        if stato["stato"] != "in_corso":
            return stato
        time.sleep(0.02)
    raise TimeoutError(id)


def test_analizza(client):
    risposta = client.post("/api/copioni/analizza", json={"testo": COPIONE + "C: Chi?\n"})
    assert risposta.status_code == 200
    analisi = risposta.json()
    assert analisi["personaggi"] == ["A", "B"]
    assert analisi["battute_per_personaggio"] == {"A": 1, "B": 2}
    assert analisi["scene"] == [
        {"indice": 0, "titolo": "Scena 1", "battute": 2, "personaggi": ["B", "A"]},
        {"indice": 1, "titolo": "Scena 2", "battute": 2, "personaggi": ["B", "C"]},
    ]
    assert analisi["errori"] == [
        {"riga": 11, "messaggio": "personaggio 'C' non dichiarato nell'intestazione"}
    ]


def test_pdf(client):
    pdf = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    writer.write(pdf)
    risposta = client.post("/api/copioni/pdf", files={"file": ("c.pdf", pdf.getvalue())})
    assert risposta.status_code == 200
    assert risposta.json() == {"testo": "\n"}


def test_pdf_non_valido(client):
    risposta = client.post("/api/copioni/pdf", files={"file": ("c.pdf", b"non un pdf")})
    assert risposta.status_code == 422


def test_voci(client):
    assert client.get("/api/voci", params={"lingua": "en"}).json() == [
        {"nome": "finta", "genere": "Female", "lingua": "en-XX"}
    ]


def test_audio_dal_job_al_download(client, finto_tts):
    risposta = client.post(
        "/api/audio",
        json={
            "testo": COPIONE,
            "opzioni": {"personaggio": "A", "contesto": None, "respiro_s": 0},
            "voci": {"B": {"nome": "scelta"}},
        },
    )
    assert risposta.status_code == 202
    stato = aspetta(client, risposta.json()["id"])
    assert stato["stato"] == "completato", stato
    assert (stato["fatte"], stato["totali"]) == (2, 2)
    assert stato["nome_file"] == "Prova uno.A.mp3"
    # "Ciao a te." (3 s) + pausa di "Ciao." (1 s × 1.2, alzata a 1.5) + stacco 1.5
    assert stato["durata_s"] == pytest.approx(6.0, abs=0.1)
    assert {v.nome for _, v in finto_tts.richieste} == {"scelta", "finta"}

    mp3 = client.get(f"/api/audio/{stato['id']}/mp3")
    assert mp3.status_code == 200
    assert mp3.headers["content-type"] == "audio/mpeg"
    assert "Prova%20uno.A.mp3" in mp3.headers["content-disposition"]


@pytest.mark.parametrize(
    ("testo", "opzioni", "messaggio"),
    [
        (COPIONE + "C: Chi?\n", {"personaggio": "A"}, "il copione contiene errori"),
        (COPIONE, {"personaggio": "Z"}, "personaggio 'Z' non presente nel copione"),
        (COPIONE, {"personaggio": "A", "scene": [1]}, "nessuna battuta da studiare"),
    ],
)
def test_audio_errori_immediati(client, testo, opzioni, messaggio):
    risposta = client.post("/api/audio", json={"testo": testo, "opzioni": opzioni})
    assert risposta.status_code == 422
    assert risposta.json()["detail"]["messaggio"].startswith(messaggio)


def test_audio_opzioni_non_valide(client):
    risposta = client.post(
        "/api/audio",
        json={"testo": COPIONE, "opzioni": {"personaggio": "A", "pausa_min_s": -1}},
    )
    assert risposta.status_code == 422


def test_errore_durante_la_sintesi(client, finto_tts):
    async def guasto(testo, voce):
        raise RuntimeError("rete assente")

    finto_tts.sintetizza = guasto
    risposta = client.post("/api/audio", json={"testo": COPIONE, "opzioni": {"personaggio": "A"}})
    stato = aspetta(client, risposta.json()["id"])
    assert (stato["stato"], stato["errore"]) == ("errore", "rete assente")
    assert client.get(f"/api/audio/{stato['id']}/mp3").status_code == 409


def test_lavoro_inesistente(client):
    assert client.get("/api/audio/nessuno").status_code == 404


def test_frontend_servito_se_presente(tmp_path, finto_tts):
    (tmp_path / "index.html").write_text("<h1>ciao</h1>")
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path)
    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/").text == "<h1>ciao</h1>"
        assert client.post("/api/copioni/analizza", json={"testo": COPIONE}).status_code == 200


def test_assegna_voci(client):
    risposta = client.post("/api/voci/assegna", json={"lingua": "it", "personaggi": ["A", "B"]})
    assert risposta.json() == {
        "A": {"nome": "finta", "tono": "+0Hz", "velocita": "+0%"},
        "B": {"nome": "finta", "tono": "-12Hz", "velocita": "+0%"},
        "NARRATORE": {"nome": "finta", "tono": "+12Hz", "velocita": "+0%"},
    }


def test_anteprima(client, finto_tts):
    risposta = client.post("/api/voci/anteprima", json={"voce": {"nome": "x", "tono": "+12Hz"}})
    assert risposta.status_code == 200
    assert risposta.headers["content-type"] == "audio/wav"
    assert finto_tts.richieste[0][1].tono == "+12Hz"


def test_motore_scelto_nella_richiesta(tmp_path, finto_tts):
    from conftest import FintoTTS

    offline = FintoTTS()
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path / "assente")
    app.dependency_overrides[motori_tts] = lambda: {"edge": finto_tts, "piper": offline}
    with TestClient(app, base_url="http://localhost") as client:
        risposta = client.post(
            "/api/voci/anteprima", json={"voce": {"nome": "x"}, "motore": "piper"}
        )
        assert risposta.status_code == 200
        assert len(offline.richieste) == 1 and not finto_tts.richieste
        assert client.get("/api/voci", params={"motore": "altro"}).status_code == 422


def test_piper_senza_voci_spiega_dove_aggiungerle(tmp_path, finto_tts):
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path / "assente")
    app.dependency_overrides[motori_tts] = lambda: {
        "edge": finto_tts,
        "piper": PiperTTS(tmp_path / "voci"),
    }
    with TestClient(app, base_url="http://localhost") as client:
        risposta = client.get("/api/voci", params={"lingua": "it", "motore": "piper"})
        assert risposta.status_code == 422
        assert "Gestisci voci offline" in risposta.json()["detail"]["messaggio"]
        risposta = client.post(
            "/api/audio",
            json={"testo": COPIONE, "opzioni": {"personaggio": "A"}, "motore": "piper"},
        )
        assert risposta.status_code == 422


def test_gestione_voci_offline(tmp_path, finto_tts):
    voci = tmp_path / "voci"
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path / "assente")
    app.dependency_overrides[motori_tts] = lambda: {"edge": finto_tts, "piper": PiperTTS(voci)}
    app.dependency_overrides[cartella_voci_piper] = lambda: voci
    configurazione = json.dumps({"language": {"code": "it_IT"}, "phoneme_id_map": {}})
    with TestClient(app, base_url="http://localhost") as client:
        stato = client.get("/api/voci/piper").json()
        assert stato["installate"] == []
        paola = next(v for v in stato["catalogo"] if v["nome"] == "it_IT-paola-medium")
        assert paola["link_modello"].endswith(
            "/resolve/main/it/it_IT/paola/medium/it_IT-paola-medium.onnx?download=true"
        )
        assert not paola["installata"]

        # Prima il solo modello (voce incompleta), poi la configurazione e un file sbagliato.
        risposta = client.post(
            "/api/voci/piper",
            files=[("file", ("it_IT-paola-medium.onnx", b"\x08\x07resto", "application/octet-stream"))],
        ).json()
        assert risposta["voci"]["installate"][0]["completa"] is False
        risposta = client.post(
            "/api/voci/piper",
            files=[
                ("file", ("it_IT-paola-medium.onnx.json", configurazione.encode(), "application/json")),
                ("file", ("foto.png", b"x", "image/png")),
            ],
        ).json()
        assert risposta["aggiunti"] == ["it_IT-paola-medium.onnx.json"]
        assert [e["file"] for e in risposta["errori"]] == ["foto.png"]
        assert risposta["voci"]["installate"][0]["completa"] is True
        assert next(v for v in risposta["voci"]["catalogo"] if v["nome"] == "it_IT-paola-medium")["installata"]
        assert client.get("/api/voci", params={"motore": "piper"}).json()[0]["nome"] == "it_IT-paola-medium"

        assert client.delete("/api/voci/piper/it_IT-paola-medium").json()["installate"] == []
        assert client.delete("/api/voci/piper/it_IT-paola-medium").status_code == 404
        assert client.delete("/api/voci/piper/..%2Fsegreto").status_code == 404


@pytest.mark.parametrize(
    ("indirizzo", "origine", "codice"),
    [
        ("http://localhost:8000", None, 200),
        ("http://127.0.0.1:8000", "http://127.0.0.1:8000", 200),
        ("http://[::1]:8000", None, 200),
        ("http://localhost:5173", "http://localhost:5173", 200),  # Vite in sviluppo
        ("http://attacco.example", None, 403),  # DNS rebinding
        ("http://localhost:8000", "https://attacco.example", 403),  # richiesta da un altro sito
        ("http://localhost:8000", "null", 403),
    ],
)
def test_solo_richieste_da_questo_computer(client, indirizzo, origine, codice):
    intestazioni = {"origin": origine} if origine else {}
    risposta = client.post(
        f"{indirizzo}/api/copioni/analizza", json={"testo": COPIONE}, headers=intestazioni
    )
    assert risposta.status_code == codice
    if codice == 403:
        assert "questo computer" in risposta.json()["detail"]["messaggio"]


def test_host_aggiunti_con_variabile_d_ambiente(monkeypatch):
    monkeypatch.setenv("AUDIO_THEATRE_HOST", " Portatile.local , 192.168.1.5,")
    assert main.host_consentiti() == main.HOST_LOCALI | {"portatile.local", "192.168.1.5"}


def test_testo_troppo_lungo(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_CARATTERI", len(COPIONE) - 1)
    for percorso, corpo in [
        ("/api/copioni/analizza", {"testo": COPIONE}),
        ("/api/audio", {"testo": COPIONE, "opzioni": {"personaggio": "A"}}),
    ]:
        risposta = client.post(percorso, json=corpo)
        assert risposta.status_code == 413
        assert risposta.json()["detail"]["messaggio"].startswith("testo troppo lungo")


def test_pdf_troppo_grande(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_MB_PDF", 0)
    risposta = client.post("/api/copioni/pdf", files={"file": ("c.pdf", b"%PDF-1.7 ...")})
    assert risposta.status_code == 413


def test_voce_troppo_grande(client, monkeypatch, tmp_path):
    voci = tmp_path / "voci"
    client.app.dependency_overrides[cartella_voci_piper] = lambda: voci
    monkeypatch.setattr(main, "MAX_MB_VOCE", 0)
    risposta = client.post(
        "/api/voci/piper",
        files=[("file", ("it_IT-paola-medium.onnx", b"\x08\x07resto", "application/octet-stream"))],
    ).json()
    assert risposta["aggiunti"] == []
    assert risposta["errori"][0]["messaggio"].startswith("file troppo grande")
    assert not any(voci.glob("*.onnx"))


def test_troppe_generazioni_in_corso(client):
    lavori = client.app.state.lavori
    for i in range(main.MAX_LAVORI_IN_CORSO):
        lavori[f"lento{i}"] = Lavoro(id=f"lento{i}", nome_file="x.mp3")
    risposta = client.post("/api/audio", json={"testo": COPIONE, "opzioni": {"personaggio": "A"}})
    assert risposta.status_code == 429


def test_lavori_vecchi_scartati(client, monkeypatch):
    monkeypatch.setattr(main, "MAX_LAVORI", 2)
    corpo = {"testo": COPIONE, "opzioni": {"personaggio": "A"}}
    primo = aspetta(client, client.post("/api/audio", json=corpo).json()["id"])
    file_primo = client.app.state.lavori[primo["id"]].file
    assert file_primo.exists()
    for _ in range(2):
        aspetta(client, client.post("/api/audio", json=corpo).json()["id"])
    assert client.get(f"/api/audio/{primo['id']}").status_code == 404
    assert not file_primo.exists()
    assert len(client.app.state.lavori) == 2
