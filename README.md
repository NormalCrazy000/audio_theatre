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

Il codice Python è in `backend/`:

```bash
cd backend
uv sync
```

## Come si usa

I comandi si lanciano **dalla radice del progetto**. Le cartelle di lavoro formano una catena:

```
pdf_folder/  --pdf-to-text-->  input/  --text-to-audio-->  audio/
```

Tutte e tre vengono create se mancano e si possono cambiare con `--input-dir` e `--output-dir`.

### 1. (Opzionale) Da PDF a testo

Metti i PDF in `pdf_folder/` ed esegui:

```bash
uv run --project backend copione-audio pdf-to-text
```

I file `.txt` vengono scritti in `input/`, pronti per il passo successivo.

### 2. Prepara il testo

Nel file `.txt` in `input/` inserisci il separatore `&` nei punti in cui vuoi una pausa, cioè dove tocca a te parlare. Vengono letti solo i file `.txt`.

### 3. Genera l'audio

```bash
uv run --project backend copione-audio text-to-audio --split
```

Per ogni `nome.txt` viene creato `audio/nome.mp3`.

### Opzioni di `text-to-audio`

| Opzione | Tipo | Default | Descrizione |
| :--- | :--- | :--- | :--- |
| `--split` / `--no-split` | flag | `--no-split` | Divide il testo sul separatore e inserisce le pause. |
| `--out-audio-format` | `str` | `mp3` | Formato di uscita (`mp3`, `wav`, …). |
| `--silent-time-ms` | `int` | `10000` | Durata di ogni pausa in millisecondi. |
| `--language` | `str` | `it` | Lingua della sintesi vocale (`it`, `en`, …). |
| `--row-separator` | `str` | `&` | Carattere che separa le parti. |
| `--input-dir` | cartella | `input` | Dove leggere i `.txt`. |
| `--output-dir` | cartella | `audio` | Dove salvare gli audio. |

Esempio: testo in inglese, separatore `|`, pause di 2 secondi.

```bash
uv run --project backend copione-audio text-to-audio --language=en --split --row-separator="|" --silent-time-ms=2000
```

### Controllare un copione

Per convertire un PDF nel formato standard (`docs/formato-copione.md`) chiedi a Claude Code di usare la skill `converti-copione`. Per controllare un file `.copione.txt`:

```bash
uv run --project backend copione-audio valida "pdf_folder/Titolo.copione.txt"
```

Stampa scene, battute per personaggio ed errori con il numero di riga.

## Test

```bash
cd backend
uv run pytest
```

I test non usano la rete: il TTS viene sostituito da un finto sintetizzatore.

## Struttura

- `backend/src/copione_audio/`: pacchetto Python
  - `cli.py`: CLI (`click`)
  - `copione/`: modello, parser e validator del formato standard del copione
  - `testo_audio.py`: generazione dell'audio dal testo con separatori (provvisorio, vedi Fase 3)
  - `conversione/`: estrazione del testo dai PDF, interfaccia `Converter` e regole di conversione (`istruzioni.md`)
- `backend/tests/`: test (pytest)
- `docs/formato-copione.md`: specifica del formato del copione
- `.claude/skills/converti-copione/`: skill che converte un PDF nel formato standard
- `pdf_folder/`, `input/`, `audio/`: cartelle di lavoro (ignorate da git)
- `REFACTOR.md`: piano della nuova versione
- `CLAUDE.md`: note per chi sviluppa
