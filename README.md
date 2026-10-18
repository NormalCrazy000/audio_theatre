# Text To Audio – allenamento sul copione

Applicazione Python per **studiare un copione**: trasforma il testo in un file audio in cui le battute vengono lette dalla sintesi vocale (TTS) e, dove tocca a te, c'è una pausa di silenzio in cui recitare la tua battuta a memoria.

Si usa da un'interfaccia web: carichi il copione, scegli il personaggio, le battute da ascoltare, le pause e le voci, e scarichi l'mp3. Il piano del progetto è in [`REFACTOR.md`](REFACTOR.md).

## Con Docker (il modo più semplice)

Serve solo Docker. Dalla radice del progetto:

```bash
docker build -t copione-audio .
docker run -p 8000:8000 -v copione-audio-cache:/data/cache -v copione-audio-voci:/data/voci copione-audio
```

Apri <http://localhost:8000>. Il volume `copione-audio-cache` conserva le battute già sintetizzate tra un avvio e l'altro. La sintesi online richiede internet; per usare quella offline scarica una volta le voci nel volume `copione-audio-voci`:

```bash
docker run --rm -v copione-audio-voci:/data/voci copione-audio python -m copione_audio.tts.piper
```

## Senza Docker

### Prerequisiti

- **Python** 3.14 o superiore
- **uv** come gestore pacchetti
- **Node.js** 20 o superiore (solo per compilare l'interfaccia)
- **FFmpeg**, necessario a `pydub`:
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: scaricalo e aggiungilo al PATH
- **Connessione internet** per la sintesi online, edge-tts (voci neurali Microsoft). In alternativa c'è quella offline, vedi sotto

### Installazione

```bash
cd backend && uv sync && cd ..
cd frontend && npm install && npm run build && cd ..
```

### Sintesi offline (facoltativa)

Nel passo **Configura** si sceglie tra due motori:

| | Online (edge-tts) | Offline (Piper) |
| :--- | :--- | :--- |
| Qualità | Voci neurali Microsoft, più naturali | Più semplici e meno espressive |
| Voci italiane | 4 (2 maschili, 2 femminili) | 3 (paola, serena, riccardo; solo riccardo è maschile ed è la meno curata) |
| Internet | Sempre | Solo per scaricare le voci, una volta |
| Il testo del copione | Viene inviato a Microsoft | Resta sul computer |

Per usare Piper scarica le voci italiane (circa 150 MB) nella cartella `voci/` del progetto (esclusa da git), oppure in quella indicata da `$COPIONE_AUDIO_PIPER`:

```bash
uv run --project backend python -m copione_audio.tts.piper
```

Le voci si possono anche scegliere a mano, per esempio `… -m copione_audio.tts.piper it_IT-serena-high` ([elenco delle voci](https://huggingface.co/rhasspy/piper-voices)). Piper non ha toni diversi: il tono viene spostato dopo la sintesi.

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
3. **Configura**: personaggio, battuta muta o letta, battute precedenti o scena intera, pause, sintesi online o offline, personaggi da ascoltare, scene e voci (con anteprima ▶).
4. **Genera**: barra di avanzamento, poi ascolto e download dell'mp3.

Le impostazioni vengono ricordate nel browser; personaggio e voci per ogni copione (le voci separatamente per ciascun motore).

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
| `GET /api/voci?lingua=it&motore=edge` | Voci disponibili (`motore`: `edge` o `piper`; per Piper quelle installate) |
| `POST /api/voci/assegna` | `{"lingua", "personaggi", "motore"}`: assegnazione automatica delle voci |
| `POST /api/voci/anteprima` | `{"voce", "testo", "motore"}`: mp3 di prova di una voce |
| `POST /api/audio` | `{"testo", "opzioni", "voci", "motore"}`: avvia la generazione e restituisce un `id` |
| `GET /api/audio/{id}` | Stato e progresso |
| `GET /api/audio/{id}/mp3` | Scarica l'mp3 |

Le battute sintetizzate vengono salvate nella cartella `cache/` del progetto (esclusa da git; oppure in `$COPIONE_AUDIO_CACHE`): rigenerare con opzioni diverse è molto più veloce. Si può cancellare in qualsiasi momento.

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
  - `tts/`: interfaccia `TTSEngine`, edge-tts (online), Piper (offline), cache su disco e assegnazione delle voci
  - `conversione/`: estrazione del testo dai PDF, interfaccia `Converter` e regole di conversione (`istruzioni.md`)
- `backend/tests/`: test (pytest)
- `frontend/`: interfaccia Svelte 5 + Vite (`src/App.svelte` e i passi in `src/lib/`)
- `docs/formato-copione.md`: specifica del formato del copione
- `.claude/skills/converti-copione/`: skill che converte un PDF nel formato standard
- `pdf_folder/`: cartella di lavoro per PDF e copioni (ignorata da git)
- `voci/`: voci Piper scaricate per la sintesi offline (ignorata da git)
- `cache/`: battute già sintetizzate, si può cancellare (ignorata da git)
- `REFACTOR.md`: piano della nuova versione
- `CLAUDE.md`: note per chi sviluppa
