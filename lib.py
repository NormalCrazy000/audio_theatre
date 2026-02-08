import os
from pydub import AudioSegment
from gtts import gTTS

TEMP_DIRECTORY = "temp"
AUDIO_DIRECTORY = "audio"
INPUT_DIRECTORY = "input"
AUDIO_FORMAT = "mp3"


class TestToAudio:
    """
    Classe principale per la gestione della conversione da testo ad audio.
    Gestisce la creazione delle directory, la generazione dell'audio e la combinazione dei file.
    """

    @staticmethod
    def __create_utility_directory():
        """
        Crea le directory necessarie per il funzionamento dello script se non esistono.
        - audio: destinazione file finali
        - temp: file temporanei
        - input: file di testo da leggere
        """
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
        """
        Rimuove tutti i file presenti nella cartella temporanea 'temp'.
        Viene chiamato alla fine del processo per pulizia.
        """
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
        """
        Combina i file audio temporanei in un unico file finale.
        Se 'split' è True, aggiunge uno spezzone di silenzio tra le parti.

        :param split: Se True, aggiunge silenzio tra i segmenti.
        :param silent_time_ms: Durata del silenzio in millisecondi.
        :param input_file_name: Nome del file originale (usato per l'output).
        :param out_audio_format: Formato del file audio in uscita (es. mp3).
        """
        print("Inizio combinazione audio")
        # Ordina i file per assicurare la sequenza corretta
        temp_files = sorted(os.listdir(TEMP_DIRECTORY))
        combined_audio = AudioSegment.empty()

        for temp_file in temp_files:
            file_path = os.path.join(TEMP_DIRECTORY, temp_file)
            # Carica il segmento audio (attualmente assume che i temp siano mp3)
            audio_segment = AudioSegment.from_mp3(file_path)
            combined_audio += audio_segment
            # Aggiunge silenzio se richiesto
            if split:
                silent_segment = AudioSegment.silent(duration=silent_time_ms)
                combined_audio += silent_segment

        # Salva il file combinato finale nella cartella audio
        combined_file_path = os.path.join(
            AUDIO_DIRECTORY, f"{input_file_name}.{out_audio_format}"
        )
        combined_audio.export(combined_file_path, format=out_audio_format)
        print("Fine combinazione audio")

    @staticmethod
    def __generate_audio(
        input_file_name: str, split: bool, row_separator: str, language: str
    ):
        """
        Legge il file di testo e genera i singoli file audio temporanei usando gTTS.

        :param input_file_name: Nome del file di testo da leggere.
        :param split: Se True, divide il testo in base al separatore.
        :param row_separator: Carattere usato per separare il testo.
        :param language: Lingua per la sintesi vocale.
        """
        print("Inizio lettura delle frasi")
        with open(
            os.path.join(INPUT_DIRECTORY, input_file_name), "r", encoding="utf-8"
        ) as file:
            text = file.read()

        # Decide se splittare il testo o tenerlo intero
        if split:
            print("Splitta le frasi attraverso " + row_separator)
            rows = text.split(row_separator)
        else:
            rows = [text]
            print("Le frasi non saranno splittate")
        print("Fine lettura delle frasi")

        print("Inizio generazione audio delle frasi")
        # Itera su ogni segmento di testo e genera l'audio
        for i, row in enumerate(rows, start=1):     
            # Usa 'i' per ordinare i file temporanei (es. 00001.mp3, 00002.mp3...)
            audio_file_path = os.path.join(TEMP_DIRECTORY, f"{i:05d}.{AUDIO_FORMAT}")
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
        """
        Metodo principale pubblico che orchestra l'intero processo.

        :param split: Abilita divisione del testo.
        :param out_audio_format: Formato output.
        :param silent_time_ms: Millisecondi di silenzio.
        :param language: Lingua testo.
        :param row_separator: Separatore testo.
        """
        TestToAudio.__create_utility_directory()
        TestToAudio.__clear_temp_files()
        input_files = os.listdir(INPUT_DIRECTORY)

        # Processa ogni file presente nella cartella input
        for input_file in input_files:
            print("Lettura file", input_file)
            TestToAudio.__generate_audio(input_file, split, row_separator, language)
            TestToAudio.__combine_audio(
                split, silent_time_ms, input_file, out_audio_format
            )
            TestToAudio.__clear_temp_files()
