# CLAUDE.md

Note per chi sviluppa (persone e Claude).

## Scopo

Strumento per **studiare un copione**: genera un audio in cui il TTS legge le battute degli altri personaggi e lascia una pausa (o legge la battuta) per il personaggio che l'utente sta imparando.

## Stato attuale

Il progetto è **in refactor**. Il piano, le decisioni prese e l'ordine delle fasi sono in [`REFACTOR.md`](REFACTOR.md). Va letto prima di qualsiasi modifica strutturale e aggiornato quando una decisione cambia o una fase è completata.

Codice attuale (CLI, da sostituire):

- `main.py`: gruppo `click` con i comandi `test_to_audio` e `pdf_to_text`.
- `text_to_audio.py`: classe `TestToAudio` con metodi statici. Divide il testo su `&`, genera un mp3 per pezzo con gTTS in `temp/` (nomi `00001.mp3`…), li unisce con pydub aggiungendo silenzio e scrive in `audio/`.
- `pdf_to_text.py`: estrae il testo dai PDF in `pdf_folder/` con pypdf e scrive i `.txt` nella stessa cartella.

Bug noti, da correggere nella Fase 0 di `REFACTOR.md`:

- vengono letti tutti i file di `input/`, non solo i `.txt`;
- l'output si chiama `nome.txt.mp3`;
- il prompt `input()` blocca l'uso non interattivo;
- le cartelle di input/output dei due comandi non sono coerenti.

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
uv sync                               # dipendenze
uv run main.py test_to_audio --split=True
uv run main.py pdf_to_text
```

Servono FFmpeg installato e una connessione internet (il TTS è online).

## Convenzioni

- Python 3.14, gestito con `uv`. Le dipendenze vanno in `pyproject.toml`.
- Lingua del progetto: **italiano**. Messaggi all'utente, docstring e documentazione sono in italiano; i nomi nel codice nuovo possono essere in italiano, purché coerenti.
- Commit in stile Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`).
- La logica del piano audio deve restare testabile senza TTS né rete: il TTS si usa solo in `render.py`.
- Per Svelte usare il server MCP `svelte` (documentazione e autofixer).
