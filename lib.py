import os
from pydub import AudioSegment
from gtts import gTTS

tempDirectory = "temp"
audioDirectory = "audio"
inputDirectory = "input"
format = "mp3"


def test_to_audio(
    split: bool, out_audio: str, silent_time_ms: int, language: str, row_sep: str
):
    create_utility_directory()
    inputFileNameList = [f for f in os.listdir(inputDirectory)]

    for input_file_name in inputFileNameList:
        print("Lettura file ", input_file_name)
        generate_audio(input_file_name, split, row_sep, language)
        combine_audio(split, silent_time_ms, input_file_name, out_audio)
        clear_temp_files()


# TODO create private method!!!!!!!!!!!!!!!!!!!!!!!!!!
def create_utility_directory():
    print("Inizio generazione cartelle necessarie")
    if not os.path.exists(audioDirectory):
        os.makedirs(audioDirectory)
    if not os.path.exists(tempDirectory):
        os.makedirs(tempDirectory)
    if not os.path.exists(inputDirectory):
        os.makedirs(inputDirectory)
    print("Fine generazione cartelle necessarie")


def clear_temp_files():
    print("Inizio cancellazione file temporanei")
    audioRowFileNameList = [f for f in os.listdir(tempDirectory)]
    for audioRowFileName in audioRowFileNameList:
        rowAudioFilePath = os.path.join(tempDirectory, audioRowFileName)
        os.remove(rowAudioFilePath)
    print("Fine cancellazione file temporanei")


def combine_audio(
    split: bool, silent_time_ms: int, input_file_name: str, out_audio: str
):
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
        audioDirectory, f"{input_file_name}.{out_audio}"
    )
    combinationAudio.export(combinationAudioFilePath, format=out_audio)
    print("Fine combinazione audio ")


def generate_audio(input_file_name: str, split: bool, row_sep: str, language: str):
    print("Inizio lettura delle frasi")
    with open(
        os.path.join(inputDirectory, input_file_name), "r", encoding="utf-8"
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
