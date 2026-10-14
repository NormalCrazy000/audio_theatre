# CLAUDE.md

Note per chi sviluppa (persone e Claude).

## Scopo

Strumento per **studiare un copione**: genera un audio in cui il TTS legge le battute degli altri personaggi e lascia una pausa (o legge la battuta) per il personaggio che l'utente sta imparando.

## Stato attuale

Il progetto è **in refactor**. Il piano, le decisioni prese e l'ordine delle fasi sono in [`REFACTOR.md`](REFACTOR.md). Va letto prima di qualsiasi modifica strutturale e aggiornato quando una decisione cambia o una fase è completata.

Fase 0 completata. Codice attuale in `backend/src/copione_audio/`:

- `cli.py`: gruppo `click` con i comandi `text-to-audio` e `pdf-to-text`. Le cartelle formano la catena `pdf_folder/` → `input/` → `audio/`, relative alla cartella corrente.
- `testo_audio.py`: divide il testo sul separatore `&` e lo legge con gTTS, tutto in memoria, aggiungendo il silenzio. È provvisorio: lo sostituiranno `piano.py` e `render.py` (Fase 3).
- `conversione/pdf.py`: `estrai_testo(percorso) -> str` con pypdf.

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
uv run --project backend copione-audio text-to-audio --split   # dalla radice
uv run --project backend copione-audio pdf-to-text
```

Servono FFmpeg installato e una connessione internet (il TTS è online).

## Convenzioni

- Python 3.14, gestito con `uv`. Le dipendenze vanno in `backend/pyproject.toml`.
- Lingua del progetto: **italiano**. Messaggi all'utente, docstring e documentazione sono in italiano; i nomi nel codice nuovo possono essere in italiano, purché coerenti.
- Commit in stile Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- La logica del piano audio deve restare testabile senza TTS né rete: il TTS si usa solo in `render.py`.
- Per Svelte usare il server MCP `svelte` (documentazione e autofixer).
