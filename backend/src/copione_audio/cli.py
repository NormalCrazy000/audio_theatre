"""
CLI sottile sopra il core. Le cartelle predefinite (`pdf_folder/`, `input/`,
`audio/`) sono relative alla cartella corrente.
"""

import asyncio
from collections import Counter
from pathlib import Path

import click

from copione_audio.copione import analizza
from copione_audio.conversione.pdf import estrai_testo
from copione_audio.piano import NARRATORE, Opzioni, crea_piano
from copione_audio.render import render
from copione_audio.tts import TTSEngine, Voce, assegna_voci
from copione_audio.tts.cache import CacheTTS
from copione_audio.tts.edge import EdgeTTS

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
    Strumenti per studiare un copione: estrazione del testo dai PDF,
    controllo del formato e generazione dell'audio di allenamento.
    """


def crea_motore() -> TTSEngine:
    """Il motore TTS usato dalla CLI: edge-tts con cache su disco."""
    return CacheTTS(EdgeTTS())


def _leggi_voci(valori: tuple[str, ...]) -> dict[str, Voce]:
    """Legge le opzioni `--voce NOME=voce`."""
    voci = {}
    for valore in valori:
        nome, uguale, voce = valore.partition("=")
        if not uguale or not nome.strip() or not voce.strip():
            raise click.BadParameter(f"atteso NOME=voce, non '{valore}'", param_hint="--voce")
        voci[nome.strip()] = Voce(voce.strip())
    return voci


def _leggi_contesto(valore: str) -> int | None:
    """Legge `--contesto`: un numero di battute oppure "tutto"."""
    if valore == "tutto":
        return None
    if valore.isdigit():
        return int(valore)
    raise click.BadParameter(f"atteso un numero o 'tutto', non '{valore}'", param_hint="--contesto")


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


@cli.command(name="valida")
@click.argument(
    "file", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
def valida_copione(file: Path):
    """
    Controlla un file .copione.txt: stampa un riepilogo e gli errori.
    Esce con codice 1 se ci sono errori.
    """
    copione, errori = analizza(file.read_text(encoding="utf-8"))

    click.echo(f"Titolo: {copione.titolo}  Lingua: {copione.lingua}")
    click.echo(f"Scene: {len(copione.scene)}  Battute: {len(copione.battute)}")
    # Una battuta detta insieme conta per ognuno dei personaggi.
    conteggio = Counter(n for b in copione.battute for n in b.personaggi)
    for nome in copione.personaggi:
        click.echo(f"  {nome}: {conteggio[nome]}")

    if errori:
        click.echo(f"\n{len(errori)} errori:", err=True)
        for errore in errori:
            click.echo(f"  {errore}", err=True)
        raise SystemExit(1)
    click.echo("\nNessun errore.")


@cli.command(name="genera")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-p", "--personaggio", required=True, help="Il personaggio da studiare.")
@click.option(
    "--includi",
    multiple=True,
    help="Personaggio da far sentire (ripetibile). Di default tutti.",
)
@click.option(
    "--modalita",
    type=click.Choice(["muta", "letta"]),
    default="muta",
    show_default=True,
    help="muta: al posto della tua battuta solo la pausa. letta: la battuta "
    "viene letta, poi la pausa per ripeterla.",
)
@click.option(
    "--contesto",
    default="3",
    show_default=True,
    help="Battute precedenti da sentire prima di ogni tua battuta, "
    "oppure 'tutto' per la scena intera.",
)
@click.option("--moltiplicatore", default=1.2, show_default=True, help="Durata della pausa rispetto alla lettura della battuta.")
@click.option("--pausa-min", default=1.5, show_default=True, help="Pausa minima in secondi.")
@click.option("--pausa-max", default=30.0, show_default=True, help="Pausa massima in secondi.")
@click.option("--stacco", default=1.5, show_default=True, help="Silenzio tra i blocchi, in secondi.")
@click.option("--scena", "scene", multiple=True, type=click.IntRange(min=1), help="Numero della scena da includere (ripetibile, da 1). Di default tutte.")
@click.option("--leggi-didascalie", is_flag=True, help="Legge anche le didascalie, con la voce del narratore.")
@click.option("--voce", "voci", multiple=True, help="Voce di un personaggio, es. GIULIA=it-IT-ElsaNeural (ripetibile).")
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    help="File mp3 di uscita. Di default audio/<copione>.<personaggio>.mp3.",
)
def genera(
    file: Path,
    personaggio: str,
    includi: tuple[str, ...],
    modalita: str,
    contesto: str,
    moltiplicatore: float,
    pausa_min: float,
    pausa_max: float,
    stacco: float,
    scene: tuple[int, ...],
    leggi_didascalie: bool,
    voci: tuple[str, ...],
    output: Path | None,
):
    """
    Genera l'mp3 per studiare la parte di un personaggio da un file .copione.txt.
    """
    copione, errori = analizza(file.read_text(encoding="utf-8"))
    if errori:
        click.echo(f"Il copione ha {len(errori)} errori; controllalo con 'valida'.", err=True)
        raise SystemExit(1)

    opzioni = Opzioni(
        personaggio=personaggio,
        personaggi_inclusi=frozenset(includi) if includi else None,
        modalita_battuta=modalita,
        moltiplicatore=moltiplicatore,
        pausa_min_s=pausa_min,
        pausa_max_s=pausa_max,
        contesto=_leggi_contesto(contesto),
        stacco_s=stacco,
        scene=frozenset(n - 1 for n in scene) if scene else None,
        leggi_didascalie=leggi_didascalie,
    )
    try:
        segmenti = crea_piano(copione, opzioni)
    except ValueError as e:
        raise click.BadParameter(str(e), param_hint="--personaggio")
    if not segmenti:
        click.echo("Nessuna battuta da studiare con queste opzioni.", err=True)
        raise SystemExit(1)

    motore = crea_motore()
    disponibili = asyncio.run(motore.voci(copione.lingua))
    assegnate = assegna_voci(copione.personaggi + [NARRATORE], disponibili)
    assegnate |= _leggi_voci(voci)
    for nome in copione.personaggi:
        voce = assegnate[nome]
        click.echo(f"  {nome}: {voce.nome} {voce.tono}")

    with click.progressbar(length=0, label="Sintesi") as barra:
        def progresso(fatte: int, totali: int):
            barra.length = totali
            barra.update(1)

        audio = asyncio.run(render(segmenti, assegnate, motore, progresso))

    if output is None:
        nome = file.name.removesuffix(".txt").removesuffix(".copione")
        output = Path("audio") / f"{nome}.{personaggio}.mp3"
    output.parent.mkdir(parents=True, exist_ok=True)
    audio.export(output, format="mp3")
    click.echo(f"Audio salvato in '{output}' ({len(audio) / 60000:.1f} minuti).")


@cli.command(name="voci")
@click.option("--lingua", default="it", show_default=True, help="Codice della lingua.")
def elenca_voci(lingua: str):
    """
    Elenca le voci disponibili per una lingua.
    """
    for voce in asyncio.run(crea_motore().voci(lingua)):
        click.echo(f"{voce.nome}  ({voce.genere}, {voce.lingua})")
