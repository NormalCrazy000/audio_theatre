import click
import lib


@click.command()
@click.option(
    "--split",
    default=False,
    type=bool,
    show_default=True,
    help="Vuoi splittare le frasi nel file",
)
@click.option(
    "--out-audio",
    default="mp3",
    show_default=True,
    type=str,
    help="""Formato dell'audio generato""",
)
@click.option(
    "--silent-time-ms",
    default=10000,
    show_default=True,
    type=int,
    help="Silenzio da aggiungere tra le frasi slittate in un file",
)
@click.option(
    "--language",
    default="it",
    show_default=True,
    type=str,
    help="Lingua del file di testo",
)
@click.option(
    "--row-sep",
    default="&",
    show_default=True,
    type=str,
    help="Carattere da usare per splittare il file in più frasi",
)
def test_to_audio(split, out_audio, silent_time_ms, language, row_sep):
    print("Valori delle variabili:")
    print(f"split = {split}")
    print(f"out_audio = {out_audio}")
    print(f"silent_time_ms = {silent_time_ms}")
    print(f"language = {language}")
    print(f"row_sep = {row_sep}")
    # TODO
    input("Premi INVIO per iniziare")
    lib.test_to_audio(split, out_audio, silent_time_ms, language, row_sep)


if __name__ == "__main__":
    test_to_audio()
