"""
CLI sottile sopra il core. Le cartelle seguono la catena
`pdf_folder/` → `input/` → `audio/` e sono relative alla cartella corrente.
"""

from pathlib import Path

import click

from copione_audio.conversione.pdf import estrai_testo
from copione_audio.testo_audio import testo_ad_audio

CARTELLA_PDF = Path("pdf_folder")
CARTELLA_TESTI = Path("input")
CARTELLA_AUDIO = Path("audio")

TipoCartella = click.Path(file_okay=False, path_type=Path)


def trova_file(cartella: Path, estensione: str) -> list[Path]:
    """
    Restituisce i file della cartella con l'estensione indicata, in ordine.

    :param cartella: La cartella in cui cercare.
    :param estensione: L'estensione, punto compreso (es. ".txt"); maiuscole ignorate.
    """
    return sorted(
        f
        for f in cartella.iterdir()
        if f.is_file() and f.suffix.lower() == estensione
    )


@click.group()
def cli():
    """
    Strumenti per studiare un copione: estrazione del testo dai PDF e
    generazione dell'audio di allenamento.
    """


@cli.command(name="text-to-audio")
@click.option(
    "--split/--no-split",
    default=False,
    show_default=True,
    help="Divide il testo sul separatore e inserisce le pause.",
)
@click.option(
    "--out-audio-format",
    default="mp3",
    show_default=True,
    help="Formato dell'audio generato.",
)
@click.option(
    "--silent-time-ms",
    default=10000,
    show_default=True,
    type=int,
    help="Durata di ogni pausa in millisecondi.",
)
@click.option(
    "--language",
    default="it",
    show_default=True,
    help="Lingua della sintesi vocale.",
)
@click.option(
    "--row-separator",
    default="&",
    show_default=True,
    help="Separatore delle frasi.",
)
@click.option(
    "--input-dir",
    default=CARTELLA_TESTI,
    show_default=True,
    type=TipoCartella,
    help="Cartella con i file .txt.",
)
@click.option(
    "--output-dir",
    default=CARTELLA_AUDIO,
    show_default=True,
    type=TipoCartella,
    help="Cartella in cui salvare gli audio.",
)
def text_to_audio(
    split: bool,
    out_audio_format: str,
    silent_time_ms: int,
    language: str,
    row_separator: str,
    input_dir: Path,
    output_dir: Path,
):
    """
    Converte i file .txt della cartella di input in file audio.
    """
    click.echo(
        f"split={split} formato={out_audio_format} silenzio_ms={silent_time_ms} "
        f"lingua={language} separatore={row_separator!r}"
    )
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_testo = trova_file(input_dir, ".txt")
    if not file_testo:
        click.echo(f"Nessun file .txt in '{input_dir}'.")
        return

    for percorso in file_testo:
        click.echo(f"Lettura di '{percorso}'...")
        audio = testo_ad_audio(
            percorso.read_text(encoding="utf-8"),
            lingua=language,
            separatore=row_separator if split else None,
            silenzio_ms=silent_time_ms,
        )
        uscita = output_dir / f"{percorso.stem}.{out_audio_format}"
        audio.export(uscita, format=out_audio_format)
        click.echo(f"Audio salvato in '{uscita}'.")


@cli.command(name="pdf-to-text")
@click.option(
    "--input-dir",
    default=CARTELLA_PDF,
    show_default=True,
    type=TipoCartella,
    help="Cartella con i file PDF.",
)
@click.option(
    "--output-dir",
    default=CARTELLA_TESTI,
    show_default=True,
    type=TipoCartella,
    help="Cartella in cui salvare i .txt.",
)
def pdf_to_text(input_dir: Path, output_dir: Path):
    """
    Estrae il testo dai PDF della cartella di input e lo salva in file .txt.
    """
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_pdf = trova_file(input_dir, ".pdf")
    if not file_pdf:
        click.echo(f"Nessun file PDF in '{input_dir}'.")
        return

    for percorso in file_pdf:
        uscita = output_dir / f"{percorso.stem}.txt"
        try:
            uscita.write_text(estrai_testo(percorso), encoding="utf-8")
        except Exception as e:
            click.echo(f"Errore con '{percorso}': {e}", err=True)
        else:
            click.echo(f"'{percorso}' → '{uscita}'")
