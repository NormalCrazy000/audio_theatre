import pyttsx3
import os
from pydub import AudioSegment

# Generazione audio per riga

# Initialize the TTS engine
engine = pyttsx3.init()

# Set the rate at which the text should be spoken
rate = engine.getProperty('rate')
engine.setProperty('rate', rate-50)

# Set the volume of the spoken text
volume = engine.getProperty('volume')
engine.setProperty('volume', volume+0.25)

# Set the voice to use
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[2].id)


# Read file (phrase are separated by &)
file_path = 'battute.txt'
with open(file_path, 'r',encoding="utf-8") as file:
    file_content = file.read()
array = file_content.split("&")

# Run audio
i = 0
for x in array:
  i = i +1
  print(x)
  s = 'audio/output' + str(i) +  '.mp3'
  if(x!=''):
    engine.save_to_file(x, s)

engine.runAndWait()


# combinazione audio


# Cartella contenente i file audio
cartella = "audio"

# Formato dei file audio da combinare (ad esempio 'mp3' o 'wav')
formato = "mp3"

# Lista di tutti i file nella cartella con l'estensione desiderata
file_audio = [f for f in os.listdir(cartella) if f.endswith(f".{formato}")]

# Ordina i file in ordine crescente
file_audio.sort()

# Inizializza l'audio combinato con un segmento vuoto
audio_combinato = AudioSegment.empty()

# Cicla su tutti i file e li aggiunge
for file in file_audio:
    
    percorso_file = os.path.join(cartella, file)
    audio = AudioSegment.from_mp3(percorso_file)
    silent = AudioSegment.silent(10000)
    audio_combinato +=silent
    audio_combinato += audio

# Esporta il file combinato
# audio_combinato.export(os.path.join(cartella, f"audio_combinato.{formato}"), format=formato)

print("Tutti i file sono stati combinati con successo!")

