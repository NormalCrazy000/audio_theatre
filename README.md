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
- **Connessione internet**: la sintesi vocale usa edge-tts (voci neurali Microsoft)

## Installazione

Il codice Python è in `backend/`:

```bash
cd backend
uv sync
```

## Come si usa

### 1. Prepara il copione

Serve un file `.copione.txt` nel formato standard (vedi [`docs/formato-copione.md`](docs/formato-copione.md)). Puoi:

- scriverlo a mano;
- partire da un PDF e chiedere a Claude Code di convertirlo con la skill `converti-copione`.

### 2. Avvia il server

Dalla radice del progetto:

```bash
uv run --project backend uvicorn copione_audio.api.main:app
```

Il server ascolta su <http://127.0.0.1:8000>. La documentazione interattiva dell'API è su <http://127.0.0.1:8000/docs>.

| Endpoint | Descrizione |
| :--- | :--- |
| `POST /api/copioni/analizza` | `{"testo": …}`: personaggi, scene, battute ed errori |
| `POST /api/copioni/pdf` | Upload di un PDF: testo grezzo |
| `GET /api/voci?lingua=it` | Voci disponibili |
| `POST /api/audio` | `{"testo", "opzioni", "voci"}`: avvia la generazione e restituisce un `id` |
| `GET /api/audio/{id}` | Stato e progresso |
| `GET /api/audio/{id}/mp3` | Scarica l'mp3 |

Le battute sintetizzate vengono salvate in `~/.cache/copione-audio/`: rigenerare con opzioni diverse è molto più veloce.

## Test

```bash
cd backend
uv run pytest
```

I test non usano la rete: il TTS viene sostituito da un finto sintetizzatore.

## Struttura

- `backend/src/copione_audio/`: pacchetto Python
  - `api/`: API FastAPI
  - `copione/`: modello, parser e validator del formato standard del copione
  - `piano.py`: dal copione e dalle opzioni calcola la sequenza di segmenti (funzione pura)
  - `render.py`: dai segmenti produce l'audio
  - `tts/`: interfaccia `TTSEngine`, edge-tts, cache su disco e assegnazione delle voci
  - `conversione/`: estrazione del testo dai PDF, interfaccia `Converter` e regole di conversione (`istruzioni.md`)
- `backend/tests/`: test (pytest)
- `docs/formato-copione.md`: specifica del formato del copione
- `.claude/skills/converti-copione/`: skill che converte un PDF nel formato standard
- `pdf_folder/`, `input/`, `audio/`: cartelle di lavoro (ignorate da git)
- `REFACTOR.md`: piano della nuova versione
- `CLAUDE.md`: note per chi sviluppa
