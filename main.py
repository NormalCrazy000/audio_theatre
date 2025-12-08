import os
from pydub import AudioSegment
from gtts import gTTS


# File ( le frasi devono essere separate da &)
inputFileName = 'input.txt'
tempDirectory = "temp"
audioDirectory="audio"
format = "mp3"
silentTimeMs = 10000
language = "it"
rowSep = "&"
combinationAudioFilePath = os.path.join(audioDirectory, f"combinationAudio.{format}")

print("Inizio generazione cartelle necessarie")
if not os.path.exists(audioDirectory):
    os.makedirs(audioDirectory)
if not os.path.exists(tempDirectory):
    os.makedirs(tempDirectory)
print("Fine generazione cartelle necessarie")


print("Inizio lettura delle frasi")
with open(inputFileName, 'r',encoding="utf-8") as file:
    rows = file.read()
rows = rows.split(rowSep)
print("Fine lettura delle frasi")


# Genera gli audio temporanei
print("Inizio gnerazione audio delle frasi")
i = 0
for row in rows:
  i = i +1
  audioRowFilePath = tempDirectory + '/' + str(i) +  '.' + format
#   print(row)
#   print(audioRowFilePath)
  if(row!=''):
    tts = gTTS(text=row, lang=language)
    tts.save(audioRowFilePath)
print("Fine gnerazione audio delle frasi")


# combinazione audio
print("Inizio combinazione audio")
audioRowFileNameList = [f for f in os.listdir(tempDirectory)]
audioRowFileNameList.sort()
combinationAudio = AudioSegment.empty()
for audioRowFileName in audioRowFileNameList:
    audioRowFilePath = os.path.join(tempDirectory, audioRowFileName)
    audioRow = AudioSegment.from_mp3(audioRowFilePath)
    combinationAudio += audioRow
    silent = AudioSegment.silent(silentTimeMs)
    combinationAudio +=silent
combinationAudio.export(combinationAudioFilePath, format=format)
print("Fine combinazione audio ")


print("Inizio cancellazione file temporanei")
for audioRowFileName in audioRowFileNameList:
    rowAudioFilePath = os.path.join(tempDirectory, audioRowFileName)
    os.remove(rowAudioFilePath)
print("Fine cancellazione file temporanei")
