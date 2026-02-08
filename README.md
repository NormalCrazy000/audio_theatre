# Test To Audio

Applicazione Python per leggere file di testo e trasformarli in file audio utilizzando la sintesi vocale (TTS).

## Descrizione

Questo script permette di convertire uno o più file di testo posizionati nella cartella `input` in file audio (default MP3).  
È possibile decidere se convertire l'intero testo in un unico blocco oppure "splittarlo" in base a un separatore specificato, inserendo del silenzio tra le parti.

## Prerequisiti

*   **Python**: Versione 3.14 o superiore (come indicato nel `pyproject.toml`).
*   **Gestore Pacchetti**: Si consiglia l'uso di `uv` (o `poetry`/`pip`).
*   **FFmpeg**: Necessario per la manipolazione audio tramite `pydub`.
    *   Su Ubuntu/Debian: `sudo apt install ffmpeg`
    *   Su macOS: `brew install ffmpeg`
    *   Su Windows: Scaricare ed aggiungere al PATH.

## Installazione

1.  Clona il repository.
2.  Installa le dipendenze. Se usi `uv`:
    ```bash
    uv sync
    ```
    Altrimenti con `pip`:
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: se non hai un requirements.txt, le dipendenze principali sono `click`, `gtts`, `pydub`, `audioop-lts`).*

## Come si usa

1.  **Prepara i file**: Inserisci i file di testo (`.txt`) che vuoi convertire nella cartella `input`. Se la cartella non esiste, verrà creata al primo avvio.

2.  **Esegui lo script**:
    
    Esempio base (con `uv`):
    ```bash
    uv run main.py
    ```

    Oppure direttamente con Python (se l'ambiente è attivo):
    ```bash
    python main.py
    ```

3.  **Output**: Troverai i file audio generati nella cartella `audio`.

### Opzioni da riga di comando

Puoi personalizzare l'esecuzione usando i seguenti argomenti (flag):

| Opzione | Tipo | Default | Descrizione |
| :--- | :--- | :--- | :--- |
| `--split` | `bool` | `False` | Se `true`, divide il testo in base al separatore. |
| `--out-audio-format` | `str` | `mp3` | Formato del file audio in uscita (es. `wav`, `mp3`). |
| `--silent-time-ms` | `int` | `10000` | Millisecondi di silenzio da aggiungere tra le parti (se split è attivo). Default 10 secondi. |
| `--language` | `str` | `it` | Codice della lingua per la sintesi vocale (es. `en`, `it`). |
| `--row-separator` | `str` | `&` | Carattere usato per separare le frasi nel testo se `--split` è attivo. |

### Esempio Avanzato

Convertire un testo in inglese, splittando le frasi dove trova il carattere `|` e inserendo solo 2 secondi di pausa:

```bash
uv run main.py --language="en" --split=True --row-separator="|" --silent-time-ms=2000
```

## Struttura del Progetto

*   `input/`: Cartella dove inserire i file di testo da leggere.
*   `audio/`: Cartella dove verranno salvati i file audio generati.
*   `temp/`: Cartella temporanea utilizzata durante l'elaborazione (viene pulita automaticamente).
*   `main.py`: Punto di ingresso dello script (CLI).
*   `lib.py`: Contiene la logica di conversione audio.