import os
import click
from pydub import AudioSegment
from gtts import gTTS


# Fisse
tempDirectory = "temp"
audioDirectory = "audio"
inputDirectory = "input"
format = "mp3"


# Variabili
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
    input("Premi INVIO per iniziare a leggere i file...")

    print("Inizio generazione cartelle necessarie")
    if not os.path.exists(audioDirectory):
        os.makedirs(audioDirectory)
    if not os.path.exists(tempDirectory):
        os.makedirs(tempDirectory)
    if not os.path.exists(inputDirectory):
        os.makedirs(inputDirectory)
    print("Fine generazione cartelle necessarie")
    inputFileNameList = [f for f in os.listdir(inputDirectory)]

    for inputFileName in inputFileNameList:
        print("Lettura file ", inputFileName)

        print("Inizio lettura delle frasi")

        with open(
            os.path.join(inputDirectory, inputFileName), "r", encoding="utf-8"
        ) as file:
            rows = file.read()
        # Splitta le righe se settato a True
        if split == True:
            print("Splitta le frasi attraverso " + row_sep)
            rows = rows.split(row_sep)
        else:
            rows = [rows]
            print("Le frasi non saranno splittate")
        print("Fine lettura delle frasi")

        # Genera gli audio temporanei
        print("Inizio gnerazione audio delle frasi")
        i = 0
        for row in rows:
            i = i + 1
            audioRowFilePath = tempDirectory + "/" + str(i) + "." + format
            if row != "":
                tts = gTTS(text=row, lang=language)
                tts.save(audioRowFilePath)
        print("Fine generazione audio delle frasi")

        # combinazione audio
        print("Inizio combinazione audio")
        audioRowFileNameList = [f for f in os.listdir(tempDirectory)]
        audioRowFileNameList.sort()
        combinationAudio = AudioSegment.empty()
        for audioRowFileName in audioRowFileNameList:
            audioRowFilePath = os.path.join(tempDirectory, audioRowFileName)
            audioRow = AudioSegment.from_mp3(audioRowFilePath)
            combinationAudio += audioRow
            if split == True:
                silent = AudioSegment.silent(silent_time_ms)
                combinationAudio += silent

        combinationAudioFilePath = os.path.join(
            audioDirectory, f"{inputFileName}.{out_audio}"
        )
        combinationAudio.export(combinationAudioFilePath, format=out_audio)
        print("Fine combinazione audio ")

        print("Inizio cancellazione file temporanei")
        for audioRowFileName in audioRowFileNameList:
            rowAudioFilePath = os.path.join(tempDirectory, audioRowFileName)
            os.remove(rowAudioFilePath)
        print("Fine cancellazione file temporanei")


if __name__ == "__main__":
    test_to_audio()
