# Text To Audio – allenamento sul copione

Applicazione Python per **studiare un copione**: trasforma il testo in un file audio in cui le battute vengono lette dalla sintesi vocale (TTS) e, dove tocca a te, c'è una pausa di silenzio in cui recitare la tua battuta a memoria.

> **Il progetto è in fase di refactor.** È in arrivo un'interfaccia web (niente più riga di comando) con un formato standard del copione, la scelta del personaggio da studiare, dei personaggi da ascoltare, delle pause, dell'oscuramento della propria battuta e del numero di battute precedenti da ascoltare. Il piano completo è in [`REFACTOR.md`](REFACTOR.md).
>
> Questo README descrive **la versione attuale (CLI)**.

## Prerequisiti

- **Python** 3.14 o superiore
- **uv** come gestore pacchetti (consigliato)
- **FFmpeg**, necessario a `pydub`:
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: scaricalo e aggiungilo al PATH
- **Connessione internet**: la sintesi vocale usa gTTS (Google)

## Installazione

```bash
uv sync
```

## Come si usa

### 1. (Opzionale) Da PDF a testo

Metti i PDF in `pdf_folder/` ed esegui:

```bash
uv run main.py pdf_to_text
```

I file `.txt` vengono creati **nella stessa cartella `pdf_folder/`**. Spostali in `input/` per il passo successivo.

### 2. Prepara il testo

Nel file di testo inserisci il separatore `&` nei punti in cui vuoi una pausa, cioè dove tocca a te parlare. Metti i file in `input/`; la cartella viene creata al primo avvio.

### 3. Genera l'audio

```bash
uv run main.py test_to_audio --split=True
```

Lo script mostra i parametri e aspetta che premi INVIO. Gli audio vengono salvati in `audio/`.

### Opzioni di `test_to_audio`

| Opzione | Tipo | Default | Descrizione |
| :--- | :--- | :--- | :--- |
| `--split` | `bool` | `False` | Divide il testo sul separatore e inserisce le pause. |
| `--out-audio-format` | `str` | `mp3` | Formato di uscita (`mp3`, `wav`, …). |
| `--silent-time-ms` | `int` | `10000` | Durata di ogni pausa in millisecondi. |
| `--language` | `str` | `it` | Lingua della sintesi vocale (`it`, `en`, …). |
| `--row-separator` | `str` | `&` | Carattere che separa le parti. |

Esempio: testo in inglese, separatore `|`, pause di 2 secondi.

```bash
uv run main.py test_to_audio --language="en" --split=True --row-separator="|" --silent-time-ms=2000
```

## Struttura

- `main.py`: CLI (`click`)
- `text_to_audio.py`: generazione e unione degli audio
- `pdf_to_text.py`: estrazione del testo dai PDF
- `input/`, `pdf_folder/`, `audio/`, `temp/`: cartelle di lavoro (ignorate da git)
- `REFACTOR.md`: piano della nuova versione
- `CLAUDE.md`: note per chi sviluppa
