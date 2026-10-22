# Modello locale (Ollama) – piano

Voce di [`TODO.md`](../TODO.md): convertire un PDF nel formato del copione direttamente dall'app, con un modello che gira sul computer. **Stato: da fare**, niente codice scritto finora. Serve una GPU: sulla CPU un copione intero richiederebbe decine di minuti.

## Come l'app parla con il modello

Ollama è un server locale con un'API HTTP su `http://127.0.0.1:11434`. L'app non carica il modello in Python: gli manda richieste HTTP.

```
Browser ──PDF──▶ FastAPI ──estrae il testo (pypdf)──▶ OllamaConverter ──HTTP──▶ Ollama (qwen3)
                    ▲                                        │
                    └──── copione .copione.txt ◀── ricomposto dal codice + validator
```

- `OllamaConverter` implementa l'interfaccia `Converter` (`conversione/base.py`) e usa le regole di `conversione/istruzioni.md`, le stesse della skill.
- **Il modello classifica le righe, non riscrive il copione.** Riceve il testo a blocchi di circa 100 righe numerate e risponde in JSON (con lo schema imposto tramite il parametro `format` di Ollama):

  ```json
  {"righe": [{"n": 12, "tipo": "battuta", "personaggio": "ROMEO"},
             {"n": 13, "tipo": "continua"},
             {"n": 14, "tipo": "didascalia"},
             {"n": 15, "tipo": "scarta"}]}
  ```

  Il copione viene ricomposto dal codice con il testo originale delle righe. Motivo: un modello da 8B che riscrive un copione intero salta o altera le battute, inaccettabile per chi deve impararle a memoria; le risposte brevi sono anche molto più veloci.
- Una prima passata sull'inizio del testo ricava l'elenco dei personaggi e il modo in cui sono indicate le scene: fa da contesto per tutti i blocchi.
- Alla fine passa il validator; il risultato arriva nell'editor del passo **Controlla**, con gli errori cliccabili.
- Job asincrono con avanzamento, come per l'audio: `POST /api/conversioni` → stato → risultato.
- Va impostato `num_ctx` in ogni richiesta: il servizio Ollama usa un contesto predefinito di 4096 token.

## Come si avvia il modello

"Avviare il modello" vuol dire: server Ollama acceso (su Linux di solito parte già come servizio di sistema) + modello caricato in memoria.

Scelta all'avvio dell'app, con una variabile o uno script:

```bash
AUDIO_THEATRE_MODELLO=qwen3 uv run --project backend uvicorn audio_theatre.api.main:app
./avvia.sh --modello-locale   # proposta: script che imposta la variabile
```

Con il modello attivo, nel lifespan di FastAPI e in background (l'app parte subito):

1. controlla che Ollama risponda; se non risponde lancia `ollama serve` come processo figlio e lo ferma alla chiusura;
2. controlla che il modello sia scaricato; se manca lo segnala nell'interfaccia (niente download automatico di 5 GB);
3. lo precarica e lo tiene in memoria (`keep_alive`) finché l'app è aperta; alla chiusura lo scarica (`keep_alive: 0`).

In Docker l'app non avvia Ollama: si collega a quello del computer su `host.docker.internal:11434` (su Linux serve `extra_hosts: ["host.docker.internal:host-gateway"]` in `compose.yaml`).

Su Linux Ollama non ha un'interfaccia grafica ufficiale (l'app desktop esiste solo per macOS e Windows). Non serve: lo stato del modello (in caricamento, pronto, mancante) lo mostra la nostra pagina.

## Interfaccia

Nel passo **Carica**, con un PDF:

- modello attivo e pronto: pulsante «Converti con il modello locale», barra di avanzamento («blocco 7 di 20»), poi il copione nel passo Controlla;
- modello non attivo: la spiegazione attuale per convertirlo con la skill;
- modello in caricamento o mancante: un messaggio che dice cosa fare.

## Passi di sviluppo

1. `conversione/ollama.py`: client HTTP, prompt da `istruzioni.md`, classificazione a blocchi, ricomposizione; test con un finto Ollama.
2. Avvio e arresto nel lifespan: controllo del server, `ollama serve` se serve, precaricamento, stato.
3. API: `GET /api/conversione/stato`, `POST /api/conversioni` con stato e risultato.
4. Frontend: pulsante, avanzamento, risultato nell'editor.
5. Collaudo su un copione già convertito con la skill, confrontando i conteggi di scene e battute.
6. `avvia.sh`, Docker, documentazione.

## Domande ancora aperte

- **Modello predefinito**: `qwen3` 8B (circa 5 GB, buono con italiano e JSON) oppure `qwen3:14b` (circa 9 GB, più affidabile, serve una GPU da 12–16 GB). Resta comunque configurabile.
- **Scelta all'avvio o interruttore nell'interfaccia** per caricare e scaricare il modello senza riavviare. Richiesta iniziale: scelta all'avvio.
- Conferma della strategia «il modello classifica, il codice ricompone».
