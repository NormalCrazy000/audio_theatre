# Text To Audio – allenamento sul copione

Applicazione Python per **studiare un copione**: trasforma il testo in un file audio in cui le battute vengono lette dalla sintesi vocale (TTS) e, dove tocca a te, c'è una pausa di silenzio in cui recitare la tua battuta a memoria.

Si usa da un'interfaccia web: carichi il copione, scegli il personaggio, le battute da ascoltare, le pause e le voci, e scarichi l'mp3. Il piano del progetto è in [`REFACTOR.md`](REFACTOR.md).

## Avvio rapido

Tutti i comandi vanno lanciati dalla **cartella del progetto** (quella che contiene questo README).

### 1. Installa i programmi necessari (una volta sola)

| Programma | A cosa serve | Come installarlo |
| :--- | :--- | :--- |
| **uv** | Gestisce Python e le librerie del backend. Scarica da solo Python 3.14: non serve installarlo a parte | `curl -LsSf https://astral.sh/uv/install.sh \| sh` ([altri sistemi](https://docs.astral.sh/uv/getting-started/installation/)) |
| **Node.js** 20.19+ o 22.12+ | Compila l'interfaccia web | <https://nodejs.org> (o il gestore pacchetti del sistema) |
| **FFmpeg** | Crea e unisce i file audio | Ubuntu/Debian: `sudo apt install ffmpeg` · macOS: `brew install ffmpeg` · Windows: scaricalo e aggiungilo al PATH |

Per controllare che ci siano: `uv --version`, `node --version`, `ffmpeg -version`.

### 2. Installa le dipendenze e compila l'interfaccia

Una volta sola, e di nuovo ogni volta che aggiorni il codice (per esempio dopo un `git pull`):

```bash
cd backend && uv sync && cd ..
cd frontend && npm install && npm run build && cd ..
```

### 3. Avvia l'app

```bash
uv run --project backend uvicorn copione_audio.api.main:app
```

Quando nel terminale compare `Uvicorn running on http://127.0.0.1:8000`, apri **<http://127.0.0.1:8000>** nel browser.

Per fermarla premi `Ctrl+C` nel terminale. Le volte successive basta ripetere solo questo passo.

La scelta tra voci online e offline, e tutte le altre impostazioni, si fanno poi dalla pagina (vedi [Come si usa](#come-si-usa)).

## Con Docker (alternativa)

Se hai Docker non servono uv, Node.js né FFmpeg. Dalla cartella del progetto:

```bash
docker build -t copione-audio .        # la prima volta e dopo ogni aggiornamento del codice
docker run -p 8000:8000 -v copione-audio-cache:/data/cache -v copione-audio-voci:/data/voci copione-audio
```

Poi apri <http://localhost:8000>. I due volumi conservano tra un avvio e l'altro le battute già sintetizzate e le voci offline aggiunte dall'interfaccia. Se Docker risponde `permission denied`, usa `sudo docker …` oppure aggiungi il tuo utente al gruppo `docker` (`sudo usermod -aG docker $USER`, poi esci e rientra).

## Problemi comuni

| Sintomo | Causa e soluzione |
| :--- | :--- |
| Su <http://127.0.0.1:8000> compare `{"detail":"Not Found"}` | L'interfaccia non è stata compilata: esegui `cd frontend && npm run build`, poi riavvia l'app |
| `address already in use` all'avvio | La porta 8000 è occupata (forse l'app è già avviata in un altro terminale). Chiudi l'altra o usa un'altra porta: `… uvicorn copione_audio.api.main:app --port 8001` |
| Il browser non apre la pagina («impossibile raggiungere il sito») | L'app non è in esecuzione: avviala (passo 3) e aspetta il messaggio `Uvicorn running` |
| «Voci non disponibili» con la sintesi online | Manca la connessione a internet: riprova, oppure passa alla sintesi offline |
| «Voci non disponibili» con la sintesi offline | Non ci sono voci installate: aggiungile da «Gestisci voci offline» |
| Errore che cita `ffmpeg` o `ffprobe` durante la generazione | FFmpeg non è installato o non è nel PATH (passo 1) |

## Come si usa

### Prepara il copione

Serve un file `.copione.txt` nel formato standard (vedi [`docs/formato-copione.md`](docs/formato-copione.md)). Puoi:

- scriverlo a mano;
- partire da un PDF e chiedere a Claude Code di convertirlo con la skill `converti-copione`.

### La pagina

In cima ci sono le **Impostazioni**, che valgono per qualsiasi copione e si possono scegliere anche prima di caricarlo: sintesi vocale online o offline (con la gestione delle voci offline), battuta muta o letta, battute precedenti o scena intera, pause, stacco tra i blocchi e lettura delle didascalie.

Poi quattro passi:

1. **Carica** il `.copione.txt`.
2. **Controlla** gli errori; puoi correggerli nell'editor integrato e scaricare il copione corretto.
3. **Configura** ciò che dipende dal copione: personaggio da studiare, personaggi da ascoltare, scene e voci dei personaggi (con anteprima ▶).
4. **Genera**: barra di avanzamento, poi ascolto e download dell'mp3.

Tutto viene ricordato nel browser: le impostazioni in generale, personaggio e voci per ogni copione (le voci separatamente per ciascun motore).

### Sintesi offline

Nelle **Impostazioni** si sceglie tra due motori:

| | Online (edge-tts) | Offline (Piper) |
| :--- | :--- | :--- |
| Qualità | Voci neurali Microsoft, più naturali | Più semplici e meno espressive |
| Voci italiane | 4 (2 maschili, 2 femminili) | 3 (paola, serena, riccardo; solo riccardo è maschile ed è la meno curata) |
| Internet | Sempre | Solo per scaricare le voci, una volta |
| Il testo del copione | Viene inviato a Microsoft | Resta sul computer |

L'app non scarica niente da sola. Per usare Piper, nelle **Impostazioni** apri **Gestisci voci offline**:

1. per ogni voce che vuoi, scarica dai link **tutti e due i file**: il modello `.onnx` e la configurazione `.onnx.json` (dal [repository ufficiale](https://huggingface.co/rhasspy/piper-voices); le italiane pesano 30–115 MB l'una);
2. trascinali nel riquadro: l'app li controlla e li salva nella cartella `voci/` del progetto (esclusa da git), oppure in quella indicata da `$COPIONE_AUDIO_PIPER`. In alternativa copiali a mano in quella cartella e premi «aggiorna l'elenco».

Dalla stessa sezione si vedono le voci installate, quelle incomplete (manca uno dei due file) e si eliminano. Piper non ha toni diversi: il tono viene spostato dopo la sintesi.

## Sviluppo

### Interfaccia con ricarica automatica

In due terminali, dalla cartella del progetto:

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
| `GET /api/voci/piper?lingua=it` | Voci offline: cartella, installate e catalogo con i link |
| `POST /api/voci/piper` | Upload dei file `.onnx` e `.onnx.json` di una o più voci |
| `DELETE /api/voci/piper/{nome}` | Elimina una voce offline |
| `POST /api/audio` | `{"testo", "opzioni", "voci", "motore"}`: avvia la generazione e restituisce un `id` |
| `GET /api/audio/{id}` | Stato e progresso |
| `GET /api/audio/{id}/mp3` | Scarica l'mp3 |

Le battute sintetizzate vengono salvate nella cartella `cache/` del progetto (esclusa da git; oppure in `$COPIONE_AUDIO_CACHE`): rigenerare con opzioni diverse è molto più veloce. Si può cancellare in qualsiasi momento.

### Test

```bash
cd backend && uv run pytest        # backend, senza rete
cd frontend && npm run check       # tipi e componenti Svelte
```

I test non usano la rete: il TTS viene sostituito da un finto sintetizzatore.

### Struttura

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
