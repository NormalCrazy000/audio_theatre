from pathlib import Path

from click.testing import CliRunner
from copione_audio import cli as modulo_cli


def test_trova_file_ignora_maiuscole_e_cartelle(tmp_path: Path):
    (tmp_path / "a.PDF").touch()
    (tmp_path / "b.pdf").touch()
    (tmp_path / "c.txt").touch()
    (tmp_path / "d.pdf").mkdir()
    assert [p.name for p in modulo_cli.trova_file(tmp_path, ".pdf")] == [
        "a.PDF",
        "b.pdf",
    ]


def test_valida_copione_corretto(tmp_path: Path):
    file = tmp_path / "prova.copione.txt"
    file.write_text(
        "---\ntitolo: T\nlingua: it\npersonaggi: A, B\n---\n"
        "A: Uno\nB: Due\nA e B: Tre\n",
        encoding="utf-8",
    )
    risultato = CliRunner().invoke(modulo_cli.cli, ["valida", str(file)])
    assert risultato.exit_code == 0, risultato.output
    assert "  A: 2\n  B: 2\n" in risultato.output
    assert "Nessun errore." in risultato.output


def test_valida_copione_con_errori(tmp_path: Path):
    file = tmp_path / "prova.copione.txt"
    file.write_text(
        "---\ntitolo: T\nlingua: it\npersonaggi: A\n---\nC: Chi?\n",
        encoding="utf-8",
    )
    risultato = CliRunner().invoke(modulo_cli.cli, ["valida", str(file)])
    assert risultato.exit_code == 1
    assert "riga 6: personaggio 'C' non dichiarato" in risultato.output


COPIONE = """\
---
titolo: T
lingua: it
personaggi: A, B
---
# Scena 1
B: Ciao a te.
A: (ride) Ciao.
# Scena 2
B: Solo io.
"""


def test_genera(tmp_path: Path, monkeypatch, finto_tts):
    monkeypatch.setattr(modulo_cli, "crea_motore", lambda: finto_tts)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prova.copione.txt").write_text(COPIONE, encoding="utf-8")

    risultato = CliRunner().invoke(
        modulo_cli.cli,
        ["genera", "prova.copione.txt", "-p", "A", "--voce", "B=altra"],
    )

    assert risultato.exit_code == 0, risultato.output
    assert "B: altra" in risultato.output
    assert (tmp_path / "audio" / "prova.A.mp3").is_file()
    # Senza didascalie: "Ciao a te." e "Ciao." (per la pausa), mai "(ride)".
    assert sorted(t for t, _ in finto_tts.richieste) == ["Ciao a te.", "Ciao."]


def test_genera_rifiuta_copione_con_errori(tmp_path: Path):
    file = tmp_path / "rotto.copione.txt"
    file.write_text(COPIONE + "C: Chi?\n", encoding="utf-8")
    risultato = CliRunner().invoke(modulo_cli.cli, ["genera", str(file), "-p", "A"])
    assert risultato.exit_code == 1
    assert "1 errori" in risultato.output


def test_genera_personaggio_sconosciuto(tmp_path: Path, monkeypatch, finto_tts):
    monkeypatch.setattr(modulo_cli, "crea_motore", lambda: finto_tts)
    file = tmp_path / "prova.copione.txt"
    file.write_text(COPIONE, encoding="utf-8")
    risultato = CliRunner().invoke(modulo_cli.cli, ["genera", str(file), "-p", "Z"])
    assert risultato.exit_code == 2
    assert "'Z' non presente" in risultato.output
