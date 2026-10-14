# CLAUDE.md

Note per chi sviluppa (persone e Claude).

## Scopo

Strumento per **studiare un copione**: genera un audio in cui il TTS legge le battute degli altri personaggi e lascia una pausa (o legge la battuta) per il personaggio che l'utente sta imparando.

## Stato attuale

Il progetto è **in refactor**. Il piano, le decisioni prese e l'ordine delle fasi sono in [`REFACTOR.md`](REFACTOR.md). Va letto prima di qualsiasi modifica strutturale e aggiornato quando una decisione cambia o una fase è completata.

Fasi 0–4 completate. Codice attuale in `backend/src/copione_audio/`:

- `api/main.py`: FastAPI, `crea_app()`. Endpoint sotto `/api`; l'audio è un job asincrono (`POST /api/audio` → stato → `/mp3`). Il TTS arriva dalla dipendenza `motore_tts`, che nei test si sostituisce con `dependency_overrides`. Se esiste `frontend/dist` (o `$COPIONE_AUDIO_FRONTEND`) viene servito su `/`.
- `piano.py`: `crea_piano(copione, Opzioni) -> [Parla | Silenzio | Pausa]`, una funzione pura. Toglie le didascalie tra parentesi dal testo letto, salvo `leggi_didascalie`. `Pausa` dipende dalla durata della lettura e viene risolta dal render.
- `render.py`: `async render(segmenti, voci, motore)`. Sintetizza ogni (personaggio, testo) una volta sola, in parallelo, poi monta l'audio.
- `tts/`: interfaccia `TTSEngine` e `Voce`, motore `EdgeTTS`, `CacheTTS` (cache in `~/.cache/copione-audio/`) e `assegna_voci`. Nei test si usa `FintoTTS` (`tests/conftest.py`), che è offline.
- `copione/`: formato standard del copione (specifica in [`docs/formato-copione.md`](docs/formato-copione.md)). `analizza(testo) -> (Copione, errori)` unisce il parser (sintassi) e il validator (contenuto); gli errori hanno il numero di riga.
- `conversione/pdf.py`: `estrai_testo(percorso) -> str` con pypdf.
- `conversione/base.py`: interfaccia `Converter`. Le regole di conversione sono in `conversione/istruzioni.md`, l'unica fonte per la skill `converti-copione` e per il futuro convertitore locale: se cambiano, si aggiornano lì.

## Architettura obiettivo (in breve)

- `backend/`: FastAPI con un pacchetto `copione_audio`, diviso in:
  - parser del formato `NOME: battuta`;
  - `piano.py`, una funzione **pura** `(copione, opzioni) -> segmenti`;
  - `render.py`, che dai segmenti produce l'mp3;
  - TTS dietro l'interfaccia `TTSEngine` (edge-tts);
  - conversione dietro l'interfaccia `Converter`.
- `frontend/`: Svelte + Vite (SPA). In produzione è servito da FastAPI.
- `.claude/skills/converti-copione/`: skill che converte PDF o testo grezzo nel formato standard. In futuro sarà affiancata da un modello locale (Ollama) dietro la stessa interfaccia `Converter`.

## Comandi

```bash
cd backend && uv sync && uv run pytest              # dipendenze e test
uv run --project backend uvicorn copione_audio.api.main:app --reload   # dalla radice; API su :8000, docs su /docs
uv run --project backend python .claude/skills/converti-copione/valida.py FILE.copione.txt  # controlla un copione
```

Servono FFmpeg installato e una connessione internet (il TTS è online).

## Convenzioni

- Python 3.14, gestito con `uv`. Le dipendenze vanno in `backend/pyproject.toml`.
- Lingua del progetto: **italiano**. Messaggi all'utente, docstring e documentazione sono in italiano; i nomi nel codice nuovo possono essere in italiano, purché coerenti.
- Commit in stile Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- La logica del piano audio deve restare testabile senza TTS né rete: il TTS si usa solo in `render.py`.
- Per Svelte usare il server MCP `svelte` (documentazione e autofixer).
