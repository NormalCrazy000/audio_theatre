import os
from pydub import AudioSegment
from gtts import gTTS


# File ( le frasi devono essere separate da &)
tempDirectory = "temp"
audioDirectory="audio"
inputDirectory = "input"
format = "mp3"
silentTimeMs = 10000
language = "it"
rowSep = "&"
splitFile = False

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

    
    with open(os.path.join(inputDirectory, inputFileName), 'r', encoding="utf-8") as file:
        rows = file.read()
    # Splitta le righe se settato a True  
    if(splitFile == True):
        print("Splitta le frasi attraverso " + rowSep);
        rows = rows.split(rowSep)
    else:
        rows = [rows]
        print("Le frasi non saranno splittate");
    print("Fine lettura delle frasi")


    # Genera gli audio temporanei
    print("Inizio gnerazione audio delle frasi")
    i = 0
    for row in rows:
        i = i + 1
        audioRowFilePath = tempDirectory + '/' + str(i) + '.' + format
        if(row != ''):
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
        if(splitFile == True):
            silent = AudioSegment.silent(silentTimeMs)
            combinationAudio += silent
        
    combinationAudioFilePath = os.path.join(audioDirectory, f"{inputFileName}.{format}")
    combinationAudio.export(combinationAudioFilePath, format=format)
    print("Fine combinazione audio ")


    print("Inizio cancellazione file temporanei")
    for audioRowFileName in audioRowFileNameList:
        rowAudioFilePath = os.path.join(tempDirectory, audioRowFileName)
        os.remove(rowAudioFilePath)
    print("Fine cancellazione file temporanei")
