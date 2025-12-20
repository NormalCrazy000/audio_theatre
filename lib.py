import os
from pydub import AudioSegment
from gtts import gTTS

TEMP_DIRECTORY = "temp"
AUDIO_DIRECTORY = "audio"
INPUT_DIRECTORY = "input"
AUDIO_FORMAT = "mp3"


class TestToAudio:
    @staticmethod
    def __create_utility_directory():
        print("Inizio generazione cartelle necessarie")
        if not os.path.exists(AUDIO_DIRECTORY):
            os.makedirs(AUDIO_DIRECTORY)
        if not os.path.exists(TEMP_DIRECTORY):
            os.makedirs(TEMP_DIRECTORY)
        if not os.path.exists(INPUT_DIRECTORY):
            os.makedirs(INPUT_DIRECTORY)
        print("Fine generazione cartelle necessarie")

    @staticmethod
    def __clear_temp_files():
        print("Inizio cancellazione file temporanei")
        temp_files = [f for f in os.listdir(TEMP_DIRECTORY)]
        for temp_file in temp_files:
            file_path = os.path.join(TEMP_DIRECTORY, temp_file)
            os.remove(file_path)
        print("Fine cancellazione file temporanei")

    @staticmethod
    def __combine_audio(
        split: bool, silent_time_ms: int, input_file_name: str, out_audio_format: str
    ):
        print("Inizio combinazione audio")
        temp_files = sorted(os.listdir(TEMP_DIRECTORY))
        combined_audio = AudioSegment.empty()

        for temp_file in temp_files:
            file_path = os.path.join(TEMP_DIRECTORY, temp_file)
            audio_segment = AudioSegment.from_mp3(file_path)
            combined_audio += audio_segment
            if split:
                silent_segment = AudioSegment.silent(duration=silent_time_ms)
                combined_audio += silent_segment

        combined_file_path = os.path.join(
            AUDIO_DIRECTORY, f"{input_file_name}.{out_audio_format}"
        )
        combined_audio.export(combined_file_path, format=out_audio_format)
        print("Fine combinazione audio")

    @staticmethod
    def __generate_audio(
        input_file_name: str, split: bool, row_separator: str, language: str
    ):
        print("Inizio lettura delle frasi")
        with open(
            os.path.join(INPUT_DIRECTORY, input_file_name), "r", encoding="utf-8"
        ) as file:
            text = file.read()

        if split:
            print("Splitta le frasi attraverso " + row_separator)
            rows = text.split(row_separator)
        else:
            rows = [text]
            print("Le frasi non saranno splittate")
        print("Fine lettura delle frasi")

        print("Inizio generazione audio delle frasi")
        for i, row in enumerate(rows, start=1):
            audio_file_path = os.path.join(TEMP_DIRECTORY, f"{i}.{AUDIO_FORMAT}")
            if row.strip() != "":
                tts = gTTS(text=row, lang=language)
                tts.save(audio_file_path)
        print("Fine generazione audio delle frasi")

    @staticmethod
    def test_to_audio(
        split: bool,
        out_audio_format: str,
        silent_time_ms: int,
        language: str,
        row_separator: str,
    ):
        TestToAudio.__create_utility_directory()
        input_files = os.listdir(INPUT_DIRECTORY)

        for input_file in input_files:
            print("Lettura file", input_file)
            TestToAudio.__generate_audio(input_file, split, row_separator, language)
            TestToAudio.__combine_audio(
                split, silent_time_ms, input_file, out_audio_format
            )
            TestToAudio.__clear_temp_files()
