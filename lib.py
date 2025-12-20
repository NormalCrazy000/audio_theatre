import os
from pydub import AudioSegment
from gtts import gTTS

temp_directory = "temp"
audio_directory = "audio"
input_directory = "input"
audio_format = "mp3"

class TestToAudio:

    @staticmethod
    def __create_utility_directory():
        print("Inizio generazione cartelle necessarie")
        if not os.path.exists(audio_directory):
            os.makedirs(audio_directory)
        if not os.path.exists(temp_directory):
            os.makedirs(temp_directory)
        if not os.path.exists(input_directory):
            os.makedirs(input_directory)
        print("Fine generazione cartelle necessarie")

    @staticmethod
    def __clear_temp_files():
        print("Inizio cancellazione file temporanei")
        temp_file_list = [f for f in os.listdir(temp_directory)]
        for temp_file_name in temp_file_list:
            file_path = os.path.join(temp_directory, temp_file_name)
            os.remove(file_path)
        print("Fine cancellazione file temporanei")

    @staticmethod
    def __combine_audio(split: bool, silent_time_ms: int, input_file_name: str, out_audio: str):
        print("Inizio combinazione audio")
        temp_file_list = [f for f in os.listdir(temp_directory)]
        temp_file_list.sort()
        combined_audio = AudioSegment.empty()
        for temp_file_name in temp_file_list:
            temp_file_path = os.path.join(temp_directory, temp_file_name)
            audio_row = AudioSegment.from_mp3(temp_file_path)
            combined_audio += audio_row
            if split:
                silent = AudioSegment.silent(silent_time_ms)
                combined_audio += silent

        combined_audio_file_path = os.path.join(audio_directory, f"{input_file_name}.{out_audio}")
        combined_audio.export(combined_audio_file_path, format=out_audio)
        print("Fine combinazione audio")

    @staticmethod
    def __generate_audio(input_file_name: str, split: bool, row_sep: str, language: str):
        print("Inizio lettura delle frasi")
        with open(os.path.join(input_directory, input_file_name), "r", encoding="utf-8") as file:
            rows = file.read()

        if split:
            print("Splitta le frasi attraverso " + row_sep)
            rows = rows.split(row_sep)
        else:
            rows = [rows]
            print("Le frasi non saranno splittate")
        print("Fine lettura delle frasi")

        print("Inizio generazione audio delle frasi")
        for i, row in enumerate(rows, start=1):
            audio_row_file_path = os.path.join(temp_directory, f"{i}.{audio_format}")
            if row.strip() != "":
                tts = gTTS(text=row, lang=language)
                tts.save(audio_row_file_path)
        print("Fine generazione audio delle frasi")

    @staticmethod
    def test_to_audio(split: bool, out_audio: str, silent_time_ms: int, language: str, row_sep: str):
        TestToAudio.__create_utility_directory()
        input_file_list = [f for f in os.listdir(input_directory)]

        for input_file_name in input_file_list:
            print("Lettura file", input_file_name)
            TestToAudio.__generate_audio(input_file_name, split, row_sep, language)
            TestToAudio.__combine_audio(split, silent_time_ms, input_file_name, out_audio)
            TestToAudio.__clear_temp_files()
