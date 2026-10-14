# Text To Audio – allenamento sul copione

Applicazione Python per **studiare un copione**: trasforma il testo in un file audio in cui le battute vengono lette dalla sintesi vocale (TTS) e, dove tocca a te, c'è una pausa di silenzio in cui recitare la tua battuta a memoria.

Si usa da un'interfaccia web: carichi il copione, scegli il personaggio, le battute da ascoltare, le pause e le voci, e scarichi l'mp3. Il piano del progetto è in [`REFACTOR.md`](REFACTOR.md).

## Prerequisiti

- **Python** 3.14 o superiore
- **uv** come gestore pacchetti
- **Node.js** 20 o superiore (solo per compilare l'interfaccia)
- **FFmpeg**, necessario a `pydub`:
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: scaricalo e aggiungilo al PATH
- **Connessione internet**: la sintesi vocale usa edge-tts (voci neurali Microsoft)

## Installazione

```bash
cd backend && uv sync && cd ..
cd frontend && npm install && npm run build && cd ..
```

## Come si usa

### 1. Prepara il copione

Serve un file `.copione.txt` nel formato standard (vedi [`docs/formato-copione.md`](docs/formato-copione.md)). Puoi:

- scriverlo a mano;
- partire da un PDF e chiedere a Claude Code di convertirlo con la skill `converti-copione`.

### 2. Avvia l'app

Dalla radice del progetto:

```bash
uv run --project backend uvicorn copione_audio.api.main:app
```

Apri <http://127.0.0.1:8000>. La pagina guida in quattro passi:

1. **Carica** il `.copione.txt`.
2. **Controlla** gli errori; puoi correggerli nell'editor integrato e scaricare il copione corretto.
3. **Configura**: personaggio, battuta muta o letta, battute precedenti o scena intera, pause, personaggi da ascoltare, scene e voci (con anteprima ▶).
4. **Genera**: barra di avanzamento, poi ascolto e download dell'mp3.

Le impostazioni vengono ricordate nel browser; personaggio e voci per ogni copione.

### Sviluppo dell'interfaccia

In due terminali:

```bash
uv run --project backend uvicorn copione_audio.api.main:app --reload
cd frontend && npm run dev
```

Apri l'indirizzo mostrato da Vite (di solito <http://localhost:5173>): le chiamate a `/api` vengono inoltrate al backend.

### API

La documentazione interattiva è su <http://127.0.0.1:8000/docs>.

| Endpoint | Descrizione |
| :--- | :--- |
| `POST /api/copioni/analizza` | `{"testo": …}`: personaggi, scene, battute ed errori |
| `POST /api/copioni/pdf` | Upload di un PDF: testo grezzo |
| `GET /api/voci?lingua=it` | Voci disponibili |
| `POST /api/voci/assegna` | `{"lingua", "personaggi"}`: assegnazione automatica delle voci |
| `POST /api/voci/anteprima` | `{"voce", "testo"}`: mp3 di prova di una voce |
| `POST /api/audio` | `{"testo", "opzioni", "voci"}`: avvia la generazione e restituisce un `id` |
| `GET /api/audio/{id}` | Stato e progresso |
| `GET /api/audio/{id}/mp3` | Scarica l'mp3 |

Le battute sintetizzate vengono salvate in `~/.cache/copione-audio/`: rigenerare con opzioni diverse è molto più veloce.

## Test

```bash
cd backend && uv run pytest        # backend, senza rete
cd frontend && npm run check       # tipi e componenti Svelte
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
- `frontend/`: interfaccia Svelte 5 + Vite (`src/App.svelte` e i passi in `src/lib/`)
- `docs/formato-copione.md`: specifica del formato del copione
- `.claude/skills/converti-copione/`: skill che converte un PDF nel formato standard
- `pdf_folder/`, `input/`, `audio/`: cartelle di lavoro (ignorate da git)
- `REFACTOR.md`: piano della nuova versione
- `CLAUDE.md`: note per chi sviluppa
