from pathlib import Path

from click.testing import CliRunner
from pydub import AudioSegment

from copione_audio import cli as modulo_cli


def test_text_to_audio_legge_solo_txt_e_nomina_bene_l_output(tmp_path, monkeypatch):
    letti = []

    def finto_testo_ad_audio(testo, **_):
        letti.append(testo)
        return AudioSegment.silent(duration=100)

    monkeypatch.setattr(modulo_cli, "testo_ad_audio", finto_testo_ad_audio)
    entrata, uscita = tmp_path / "input", tmp_path / "audio"
    entrata.mkdir()
    (entrata / "copione.txt").write_text("battuta", encoding="utf-8")
    (entrata / "copione.pdf").write_bytes(b"%PDF finto")
    (entrata / "note.md").write_text("da ignorare", encoding="utf-8")

    risultato = CliRunner().invoke(
        modulo_cli.cli,
        [
            "text-to-audio",
            "--split",
            "--out-audio-format=wav",
            f"--input-dir={entrata}",
            f"--output-dir={uscita}",
        ],
        input="",  # nessun INVIO: non deve aspettare l'utente
    )

    assert risultato.exit_code == 0, risultato.output
    assert letti == ["battuta"]
    assert sorted(p.name for p in uscita.iterdir()) == ["copione.wav"]


def test_trova_file_ignora_maiuscole_e_cartelle(tmp_path: Path):
    (tmp_path / "a.PDF").touch()
    (tmp_path / "b.pdf").touch()
    (tmp_path / "c.txt").touch()
    (tmp_path / "d.pdf").mkdir()
    assert [p.name for p in modulo_cli.trova_file(tmp_path, ".pdf")] == [
        "a.PDF",
        "b.pdf",
    ]
