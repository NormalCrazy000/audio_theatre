import click
from lib import TestToAudio


@click.command()
@click.option(
    "--split",
    default=False,
    type=bool,
    show_default=True,
    help="Vuoi splittare le frasi nel file",
)
@click.option(
    "--out-audio-format",
    default="mp3",
    show_default=True,
    type=str,
    help="Formato dell'audio generato",
)
@click.option(
    "--silent-time-ms",
    default=10000,
    show_default=True,
    type=int,
    help="Silenzio da aggiungere tra le frasi splittate in un file",
)
@click.option(
    "--language",
    default="it",
    show_default=True,
    type=str,
    help="Lingua del file di testo",
)
@click.option(
    "--row-separator",
    default="&",
    show_default=True,
    type=str,
    help="Carattere da usare per splittare il file in più frasi",
)
def test_to_audio_cli(
    split: bool,
    out_audio_format: str,
    silent_time_ms: int,
    language: str,
    row_separator: str,
):
    """
    CLI per convertire file di testo in audio (TTS).

    Questa funzione viene invocata da riga di comando e passa i parametri
    alla classe TestToAudio che gestisce la logica di conversione.
    """
    print("Valori delle variabili:")
    print(f"split = {split}")
    print(f"out_audio_format = {out_audio_format}")
    print(f"silent_time_ms = {silent_time_ms}")
    print(f"language = {language}")
    print(f"row_separator = {row_separator}")

    # Pausa per permettere all'utente di leggere i parametri prima dell'avvio
    input("Premi INVIO per iniziare")

    TestToAudio.test_to_audio(
        split, out_audio_format, silent_time_ms, language, row_separator
    )


if __name__ == "__main__":
    test_to_audio_cli()
