# CLAUDE.md

Note per chi sviluppa (persone e Claude).

## Scopo

Strumento per **studiare un copione**: genera un audio in cui il TTS legge le battute degli altri personaggi e lascia una pausa (o legge la battuta) per il personaggio che l'utente sta imparando.

## Stato attuale

Il progetto è **in refactor**. Il piano, le decisioni prese e l'ordine delle fasi sono in [`REFACTOR.md`](REFACTOR.md). Va letto prima di qualsiasi modifica strutturale e aggiornato quando una decisione cambia o una fase è completata.

Fasi 0–5 completate. Codice attuale in `backend/src/copione_audio/`:

- `api/main.py`: FastAPI, `crea_app()`. Endpoint sotto `/api`; l'audio è un job asincrono (`POST /api/audio` → stato → `/mp3`). I motori TTS arrivano dalla dipendenza `motori_tts` (`{"edge": …, "piper": …}`), che nei test si sostituisce con `dependency_overrides`; ogni richiesta sceglie il motore con il campo `motore`. Se esiste `frontend/dist` (o `$COPIONE_AUDIO_FRONTEND`) viene servito su `/`.
- `piano.py`: `crea_piano(copione, Opzioni) -> [Parla | Silenzio | Pausa]`, una funzione pura. Toglie le didascalie tra parentesi dal testo letto, salvo `leggi_didascalie`. `Pausa` dipende dalla durata della lettura e viene risolta dal render.
- `render.py`: `async render(segmenti, voci, motore)`. Sintetizza ogni (personaggio, testo) una volta sola, in parallelo, poi monta l'audio.
- `tts/`: interfaccia `TTSEngine` e `Voce`, motori `EdgeTTS` (online) e `PiperTTS` (offline, voci in `voci/` nella radice del progetto o in `$COPIONE_AUDIO_PIPER`), `voci_piper.py` (catalogo con i link, elenco, aggiunta ed eliminazione dei file delle voci: l'app non scarica mai nulla, i file si scaricano a mano e si trascinano nell'interfaccia), `CacheTTS` (cache in `cache/` nella radice del progetto o in `$COPIONE_AUDIO_CACHE`) e `assegna_voci`. Nei test si usa `FintoTTS` (`tests/conftest.py`), che è offline.
- `copione/`: formato standard del copione (specifica in [`docs/formato-copione.md`](docs/formato-copione.md)). `analizza(testo) -> (Copione, errori)` unisce il parser (sintassi) e il validator (contenuto); gli errori hanno il numero di riga.
- `conversione/pdf.py`: `estrai_testo(percorso) -> str` con pypdf.
- `conversione/base.py`: interfaccia `Converter`. Le regole di conversione sono in `conversione/istruzioni.md`, l'unica fonte per la skill `converti-copione` e per il futuro convertitore locale: se cambiano, si aggiornano lì.

Frontend in `frontend/` (Svelte 5 con rune, Vite, TypeScript):

- `src/App.svelte` tiene lo stato e collega la scheda `src/lib/Impostazioni.svelte` (opzioni che non dipendono dal copione, motore TTS, `VociOffline.svelte`) e i quattro passi `src/lib/Carica|Controlla|Configura|Genera.svelte`;
- `src/lib/api.ts` contiene tipi e chiamate, allineati ai modelli di `api/main.py`. Se cambia l'API vanno aggiornati;
- `src/lib/impostazioni.ts` salva le impostazioni nel `localStorage`, con ogni accesso protetto da try/catch. Il motore TTS è una scelta globale; le voci di ogni copione sono salvate per motore;
- in sviluppo Vite inoltra `/api` a `127.0.0.1:8000`; in produzione FastAPI serve `frontend/dist`.

`Dockerfile` (radice, multi-stage): build del frontend con Node, dipendenze con `uv sync --frozen --no-dev --no-editable`, immagine finale `python:3.14-slim` con ffmpeg e utente non root. Il frontend arriva tramite `COPIONE_AUDIO_FRONTEND`; la cache TTS sta in `COPIONE_AUDIO_CACHE=/data/cache` e le voci Piper in `COPIONE_AUDIO_PIPER=/data/voci`, entrambi volumi. `compose.yaml` li collega alle cartelle `cache/` e `voci/` del progetto (tenute in git con un `.gitkeep`, perché se Docker le creasse sarebbero di root) e pubblica la porta solo su `127.0.0.1`.

## Architettura obiettivo (in breve)

- `backend/`: FastAPI con un pacchetto `copione_audio`, diviso in:
  - parser del formato `NOME: battuta`;
  - `piano.py`, una funzione **pura** `(copione, opzioni) -> segmenti`;
  - `render.py`, che dai segmenti produce l'mp3;
  - TTS dietro l'interfaccia `TTSEngine` (edge-tts online, Piper offline);
  - conversione dietro l'interfaccia `Converter`.
- `frontend/`: Svelte + Vite (SPA). In produzione è servito da FastAPI.
- `.claude/skills/converti-copione/`: skill che converte PDF o testo grezzo nel formato standard. In futuro sarà affiancata da un modello locale (Ollama) dietro la stessa interfaccia `Converter`.

## Comandi

```bash
cd backend && uv sync && uv run pytest              # dipendenze e test
uv run --project backend uvicorn copione_audio.api.main:app --reload   # dalla radice; API su :8000, docs su /docs
uv run --project backend python .claude/skills/converti-copione/valida.py FILE.copione.txt  # controlla un copione
cd frontend && npm run dev     # UI in sviluppo (serve anche il backend)
cd frontend && npm run check   # controllo tipi Svelte
cd frontend && npm run build   # build servita da FastAPI
docker compose up --build      # dalla radice, con Docker: app su localhost:8000, usa cache/ e voci/ del progetto
```

Serve FFmpeg installato. Il TTS online (edge-tts) richiede internet; quello offline (Piper) solo le voci scaricate.

## Convenzioni

- Python 3.14, gestito con `uv`. Le dipendenze vanno in `backend/pyproject.toml`.
- Lingua del progetto: **italiano**. Messaggi all'utente, docstring e documentazione sono in italiano; i nomi nel codice nuovo possono essere in italiano, purché coerenti.
- Commit in stile Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- La logica del piano audio deve restare testabile senza TTS né rete: il TTS si usa solo in `render.py`.
- Per Svelte usare il server MCP `svelte` (documentazione e autofixer).
