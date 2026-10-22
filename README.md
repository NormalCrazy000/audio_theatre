# Text To Audio – allenamento sul copione

Applicazione Python per **studiare un copione**: trasforma il testo in un file audio in cui le battute vengono lette dalla sintesi vocale (TTS) e, dove tocca a te, c'è una pausa di silenzio in cui recitare la tua battuta a memoria.

Si usa da un'interfaccia web: carichi il copione, scegli il personaggio, le battute da ascoltare, le pause e le voci, e scarichi l'mp3.

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
docker compose up --build
```

Quando compare `Uvicorn running on http://0.0.0.0:8000`, apri **<http://localhost:8000>**. `--build` costruisce l'immagine la prima volta e la ricostruisce se il codice è cambiato (altrimenti è quasi immediato).

| Per… | Comando |
| :--- | :--- |
| Fermare l'app | `Ctrl+C`, oppure `docker compose down` da un altro terminale |
| Avviarla in background | `docker compose up --build -d` (poi `docker compose logs -f` per i messaggi, `docker compose down` per fermarla) |

Tutte le impostazioni stanno in [`compose.yaml`](compose.yaml):

- la porta `8000`, raggiungibile solo da questo computer;
- le cartelle `cache/` e `voci/` del progetto, condivise con il container: battute già sintetizzate e voci offline sono le stesse dell'app avviata senza Docker, e restano tra un avvio e l'altro.

Se Docker risponde `permission denied`, usa `sudo docker compose …` oppure aggiungi il tuo utente al gruppo `docker` (`sudo usermod -aG docker $USER`, poi esci e rientra).

## Problemi comuni

| Sintomo | Causa e soluzione |
| :--- | :--- |
| Su <http://127.0.0.1:8000> compare `{"detail":"Not Found"}` | L'interfaccia non è stata compilata: esegui `cd frontend && npm run build`, poi riavvia l'app |
| `address already in use` all'avvio | La porta 8000 è occupata (forse l'app è già avviata in un altro terminale, o con Docker). Chiudi l'altra o usa un'altra porta: `… uvicorn copione_audio.api.main:app --port 8001`; con Docker cambia `127.0.0.1:8000:8000` in `127.0.0.1:8001:8000` in `compose.yaml` |
| Il browser non apre la pagina («impossibile raggiungere il sito») | L'app non è in esecuzione: avviala (passo 3) e aspetta il messaggio `Uvicorn running` |
| «Voci non disponibili» con la sintesi online | Manca la connessione a internet: riprova, oppure passa alla sintesi offline |
| «Voci non disponibili» con la sintesi offline | Non ci sono voci installate: aggiungile da «Gestisci voci offline» |
| «richiesta rifiutata: l'app accetta solo richieste da questo computer» | Hai aperto l'app con un indirizzo diverso da `localhost` o `127.0.0.1`: usa uno di questi, oppure vedi [Sicurezza](#sicurezza) |
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

## Privacy e servizi esterni

L'app gira sul tuo computer: non ha account, non raccoglie statistiche e non manda dati a nessuno, salvo nei casi elencati qui. Le impostazioni restano nel browser (`localStorage`), le battute sintetizzate in `cache/` e le voci offline in `voci/`.

| Quando | Cosa esce dal computer | Verso |
| :--- | :--- | :--- |
| Sintesi online (edge-tts) | Il testo delle battute da leggere e l'elenco delle voci richiesto | Microsoft |
| Sintesi offline (Piper) | Niente | — |
| Conversione di un PDF con la skill `converti-copione` | Il testo del copione, letto da Claude | Anthropic, secondo le condizioni del tuo account Claude Code |

Se il copione non deve uscire dal computer, usa la sintesi offline e converti il PDF a mano.

**edge-tts.** Il motore online usa la libreria [edge-tts](https://github.com/rany2/edge-tts), che si collega al servizio di lettura ad alta voce di Microsoft Edge. Non è un'API ufficiale: questo progetto non è affiliato a Microsoft né approvato da Microsoft, e il servizio può cambiare o smettere di funzionare in qualsiasi momento.

**Voci Piper.** Ogni voce ha una licenza propria, che dipende dalle registrazioni con cui è stata addestrata; alcune ammettono solo usi di ricerca o non commerciali. La trovi nella scheda della voce (`MODEL_CARD`), raggiungibile dai link in **Gestisci voci offline**. L'app non contiene né distribuisce voci.

## Copioni e diritto d'autore

I copioni teatrali sono in genere protetti dal diritto d'autore. L'app li elabora solo sul tuo computer, per lo studio personale: sei tu responsabile di avere il diritto di usare i testi che carichi e di non diffondere copioni o audio generati senza il permesso di chi ne detiene i diritti. Questo repository non contiene copioni.

## Sicurezza

L'app non ha login: chi la raggiunge può usarla e anche aggiungere o cancellare le voci offline. Per questo:

- è pensata per girare solo sul tuo computer (con Docker la porta è pubblicata solo su `127.0.0.1`), e **non va esposta su internet**;
- accetta solo richieste indirizzate a `localhost`, `127.0.0.1` o `::1` e provenienti dalle sue pagine, così un sito aperto nel browser non può usarla di nascosto;
- ha dei limiti: testi fino a 2 milioni di caratteri, PDF fino a 50 MB, file delle voci fino a 200 MB, al massimo due generazioni alla volta.

Per usarla da un altro dispositivo della rete di casa, avviala con `--host 0.0.0.0` e metti in `COPIONE_AUDIO_HOST` il nome o l'indirizzo con cui la raggiungi, separati da virgole (es. `COPIONE_AUDIO_HOST=192.168.1.5`). Chiunque sia sulla stessa rete potrà usarla.

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
- `Dockerfile`, `compose.yaml`: immagine Docker e avvio con Docker Compose
- `docs/decisioni.md`: decisioni di progetto e comportamento del piano audio
- `TODO.md`: cose da fare
- `CLAUDE.md`: note per chi sviluppa
- `LICENSE`: testo della licenza (GPL-3.0)

## Licenza

Copyright © 2025–2026 NormalCrazy000.

Questo programma è software libero, distribuito con la [GNU General Public License](LICENSE), versione 3 o (a tua scelta) successiva (`GPL-3.0-or-later`). Puoi usarlo, studiarlo, modificarlo e ridistribuirlo; se distribuisci una versione modificata, deve avere la stessa licenza e va reso disponibile il codice sorgente. È fornito **senza alcuna garanzia**: i dettagli sono nel file [`LICENSE`](LICENSE).

La licenza è GPL perché il progetto usa [Piper](https://github.com/OHF-Voice/piper1-gpl), che è GPL-3.0. Le altre dipendenze hanno licenze compatibili (MIT, BSD, Apache-2.0, LGPL-3.0).
