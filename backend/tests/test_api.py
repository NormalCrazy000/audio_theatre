import time
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from copione_audio.api.main import crea_app, motori_tts
from copione_audio.tts.piper import PiperTTS

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
    with TestClient(app) as client:
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
    with TestClient(app) as client:
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
    with TestClient(app) as client:
        risposta = client.post(
            "/api/voci/anteprima", json={"voce": {"nome": "x"}, "motore": "piper"}
        )
        assert risposta.status_code == 200
        assert len(offline.richieste) == 1 and not finto_tts.richieste
        assert client.get("/api/voci", params={"motore": "altro"}).status_code == 422


def test_piper_senza_voci_spiega_come_scaricarle(tmp_path, finto_tts):
    app = crea_app(cartella_lavori=tmp_path, frontend=tmp_path / "assente")
    app.dependency_overrides[motori_tts] = lambda: {
        "edge": finto_tts,
        "piper": PiperTTS(tmp_path / "voci"),
    }
    with TestClient(app) as client:
        risposta = client.get("/api/voci", params={"lingua": "it", "motore": "piper"})
        assert risposta.status_code == 422
        assert "copione_audio.tts.piper" in risposta.json()["detail"]["messaggio"]
        risposta = client.post(
            "/api/audio",
            json={"testo": COPIONE, "opzioni": {"personaggio": "A"}, "motore": "piper"},
        )
        assert risposta.status_code == 422
