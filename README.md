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

I comandi si lanciano **dalla radice del progetto**.

### 1. Prepara il copione

Serve un file `.copione.txt` nel formato standard (vedi [`docs/formato-copione.md`](docs/formato-copione.md)). Puoi:

- scriverlo a mano;
- partire da un PDF e chiedere a Claude Code di convertirlo con la skill `converti-copione`.

Per controllarlo:

```bash
uv run --project backend copione-audio valida "pdf_folder/Titolo.copione.txt"
```

Stampa scene, battute per personaggio ed errori con il numero di riga.

### 2. Genera l'audio

```bash
uv run --project backend copione-audio genera "pdf_folder/Titolo.copione.txt" -p LAURA
```

Crea `audio/Titolo.LAURA.mp3`. Per ogni battuta di LAURA si sentono le 3 battute precedenti, poi c'è una pausa per dirla. Le didascalie, anche quelle tra parentesi dentro le battute, non vengono lette.

### Opzioni di `genera`

| Opzione | Default | Descrizione |
| :--- | :--- | :--- |
| `-p`, `--personaggio` | (obbligatoria) | Il personaggio da studiare. |
| `--includi NOME` | tutti | Personaggi da far sentire (ripetibile). Le battute degli altri vengono saltate. |
| `--modalita` | `muta` | `muta`: solo la pausa. `letta`: la battuta viene letta, poi c'è la pausa per ripeterla. |
| `--contesto` | `3` | Battute precedenti da sentire prima di ogni tua battuta, oppure `tutto` per ascoltare la scena intera una volta. |
| `--moltiplicatore` | `1.2` | Durata della pausa rispetto alla lettura della tua battuta. |
| `--pausa-min`, `--pausa-max` | `1.5`, `30` | Limiti della pausa in secondi. `[pausa=N]` nel copione ha la precedenza. |
| `--stacco` | `1.5` | Silenzio tra un blocco e l'altro, in secondi. |
| `--scena N` | tutte | Scene da includere, numerate da 1 (ripetibile). |
| `--leggi-didascalie` | no | Legge anche le didascalie. |
| `--voce NOME=VOCE` | automatica | Voce di un personaggio, es. `GIULIA=it-IT-ElsaNeural` (ripetibile). |
| `-o`, `--output` | `audio/…mp3` | File di uscita. |

Le voci vengono assegnate in automatico. Il genere del personaggio non è noto, quindi conviene indicarle con `--voce`. Per vedere le voci disponibili:

```bash
uv run --project backend copione-audio voci --lingua it
```

Le battute sintetizzate vengono salvate in `~/.cache/copione-audio/`: rigenerare con opzioni diverse è molto più veloce.

### Server (API)

```bash
uv run --project backend copione-audio server
```

Avvia l'API su <http://127.0.0.1:8000>. La documentazione interattiva è su <http://127.0.0.1:8000/docs>. L'interfaccia web (in arrivo) userà questa API.

| Endpoint | Descrizione |
| :--- | :--- |
| `POST /api/copioni/analizza` | `{"testo": …}`: personaggi, scene, battute ed errori |
| `POST /api/copioni/pdf` | Upload di un PDF: testo grezzo |
| `GET /api/voci?lingua=it` | Voci disponibili |
| `POST /api/audio` | `{"testo", "opzioni", "voci"}`: avvia la generazione e restituisce un `id` |
| `GET /api/audio/{id}` | Stato e progresso |
| `GET /api/audio/{id}/mp3` | Scarica l'mp3 |

### Da PDF a testo grezzo

```bash
uv run --project backend copione-audio pdf-to-text
```

Estrae il testo dei PDF di `pdf_folder/` in `input/`. Di solito non serve: lo fa già la skill.

## Test

```bash
cd backend
uv run pytest
```

I test non usano la rete: il TTS viene sostituito da un finto sintetizzatore.

## Struttura

- `backend/src/copione_audio/`: pacchetto Python
  - `cli.py`: CLI (`click`)
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
