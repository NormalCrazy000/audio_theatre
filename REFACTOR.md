# Piano di refactor

Obiettivo: passare da uno script CLI che legge un testo con separatori `&` inseriti a mano a una **web app** che, partendo da un copione in un formato standard, genera un **mp3 di allenamento** su misura per il personaggio da studiare.

## Decisioni prese

| Tema | Decisione |
| :--- | :--- |
| Stack | Backend **FastAPI** (Python, riusa il codice attuale) + frontend **Svelte** (SPA con Vite) |
| Formato input | Testo semplice `NOME: battuta` con intestazione dei personaggi (vedi sotto) |
| Conversione PDF → formato | Subito una **skill Claude**; dietro un'interfaccia comune, così in futuro si aggiunge un **modello locale** (es. Ollama), che è la soluzione preferita |
| Output | **File mp3 da scaricare** (il player interattivo nel browser è un'idea per dopo) |
| Contesto (battute precedenti) | **Blocchi**: per ogni mia battuta si sentono le N battute precedenti, poi la mia. Con "tutto" si sente la scena intera una sola volta |
| Pause | **Proporzionali** alla lunghezza della battuta, con moltiplicatore regolabile, più un **override per singola battuta** scritto nel file |
| Battuta non oscurata | Viene letta, poi segue una pausa per ripeterla |
| Battute dette insieme | `ROMEO e GIULIETTA: testo` (ammesse anche le virgole: `A, B e C:`). Se tra i nomi c'è il personaggio studiato, la battuta è sua |
| Più personaggi studiati insieme | Non ora: TODO futuro (Fase 6) |
| TTS | **edge-tts**, con una voce diversa per ogni personaggio, dietro un'interfaccia comune per poter aggiungere in futuro un motore offline (es. Piper) |
| Uso | **Solo in locale**: niente pubblicazione online, quindi niente limiti d'uso né login. I job in memoria vanno bene |
| Stacco tra i blocchi | **Silenzio** (`stacco_blocchi`), nessun segnale sonoro |

## Ordine delle fasi

L'ordine segue le dipendenze: prima il formato dei dati, poi la logica (testabile senza interfaccia), poi l'API e infine la UI. I punti della richiesta originale sono indicati tra parentesi.

1. **Fase 0 – Pulizia e ristrutturazione** ✅
2. **Fase 1 – Formato standard e parser** (punto 2) ✅
3. **Fase 2 – Conversione con skill Claude** (punto 2) ✅
4. **Fase 3 – Motore di generazione**: personaggio da studiare (5), personaggi inclusi (2), oscuramento (4), pause (3), contesto (6) ✅
5. **Fase 4 – API FastAPI** ✅
6. **Fase 5 – Frontend Svelte** (punto 1) ✅
7. **Fase 6 – Opzionale**: eseguibile ovunque (punto 1), modello locale, TTS offline

---

### Fase 0 – Pulizia e ristrutturazione ✅

> Completata. Note: `testo_audio.py` conserva la logica col separatore `&` finché non arriva la Fase 3 (poi rimosso, insieme a gTTS); la catena delle cartelle è `pdf_folder/` → `input/` → `audio/`; il file temporaneo su disco non serve più (l'audio resta in memoria).

- Rinominare "test" in "text" ovunque (`TestToAudio`, `test_to_audio`).
- Spostare la logica in un pacchetto (struttura sotto) e separarla da I/O e CLI.
- Correggere i bug noti:
  - `os.listdir(input)` prende anche file che non sono `.txt`;
  - l'output si chiama `nome.txt.mp3`;
  - `input("Premi INVIO")` blocca l'uso non interattivo;
  - le cartelle di input/output di `pdf_to_text` e `text_to_audio` non sono coerenti (vedi `TODO.md`).
- ~~La CLI resta come wrapper sottile sopra il core.~~ Decisione cambiata dopo la Fase 4: **la CLI è stata rimossa**, l'app si usa dall'interfaccia web. La skill `converti-copione` ha i suoi script (`estrai.py`, `valida.py`).

Struttura proposta:

```
backend/
  pyproject.toml
  src/copione_audio/
    copione/      model.py (Copione, Battuta, Didascalia), parser.py, validator.py
    conversione/  base.py (interfaccia Converter), pdf.py (estrazione testo), ollama.py (futuro)
    tts/          base.py (interfaccia TTSEngine), edge.py, cache.py
    piano.py      dal copione e dalle opzioni calcola la sequenza di segmenti audio
    render.py     dai segmenti produce l'mp3 (pydub)
    api/          main.py (FastAPI)
  tests/
frontend/         Svelte + Vite
.claude/skills/converti-copione/SKILL.md
```

### Fase 1 – Formato standard del copione ✅

> Completata. La specifica di riferimento ora è [`docs/formato-copione.md`](docs/formato-copione.md): se cambia il formato, va aggiornata lì. Il codice è in `backend/src/copione_audio/copione/` (`model.py`, `parser.py`, `validator.py`; `analizza(testo)` fa entrambe le cose). Precisazioni emerse: una riga vuota non interrompe una battuta; le battute prima del primo `#` formano una scena senza titolo; i nomi vanno scritti esattamente come nell'intestazione.

File di testo UTF-8 con estensione `.copione.txt`:

```text
---
titolo: Romeo e Giulietta
lingua: it
personaggi: ROMEO, GIULIETTA, BALIA
---

# Atto I – Scena 5

(Una sala in casa Capuleti)

ROMEO: Se profano con la mia mano indegna
  questo sacro altare, il peccato è gentile.
GIULIETTA: Buon pellegrino, fate torto alla vostra mano.
BALIA [pausa=4]: Signora, vostra madre vuole parlarvi.
```

Regole:

- **Intestazione** tra `---`: `titolo`, `lingua` (codice per il TTS) e `personaggi`, cioè l'elenco completo dei nomi ammessi.
- **Battuta**: `NOME: testo` a inizio riga. Le righe successive indentate continuano la stessa battuta.
- **Battuta detta insieme**: `ROMEO e GIULIETTA: testo`, oppure `ROMEO, BALIA e GIULIETTA: testo`. Ogni nome deve essere dichiarato.
- **Override della pausa**: `NOME [pausa=SECONDI]: testo`.
- **Scena**: una riga che inizia con `#`. Serve a scegliere le scene e ad azzerare il contesto.
- **Didascalia**: una riga tra parentesi `( … )`. Di default non viene letta (diventa un'opzione).
- Le righe vuote vengono ignorate.
- Il validator segnala nomi non dichiarati, battute vuote e righe non riconosciute, indicando il numero di riga. La UI mostra questi errori.

Da fare: un parser con test, e la specifica copiata in `docs/formato-copione.md`, così diventa il riferimento sia per la skill sia per il modello locale.

### Fase 2 – Conversione PDF/testo → formato standard ✅

> Completata. Le regole di conversione stanno in `backend/src/copione_audio/conversione/istruzioni.md` (fonte unica per la skill e per il futuro `OllamaConverter`); la skill aggiunge solo il procedimento. `valida.py` (nella cartella della skill) stampa errori e battute per personaggio e per scena. Collaudo su *Così non vale* (PDF di 48 pagine): 19 scene, 1109 battute, nessun errore; i conteggi per scena coincidono con il testo grezzo. Per copioni lunghi e regolari la skill scrive uno script usa e getta e corregge a mano il resto.

- `conversione/pdf.py`: estrazione del testo grezzo dal PDF (riusa l'attuale `pdf_to_text.py`).
- **Skill Claude** `.claude/skills/converti-copione/`: riceve PDF o testo grezzo e produce un `.copione.txt` valido. Deve:
  - riconoscere i personaggi;
  - unire le battute spezzate a fine pagina;
  - togliere numeri di pagina e intestazioni;
  - convertire le didascalie.

  Alla fine esegue il validator e corregge gli eventuali errori.
- Interfaccia `Converter` (`testo_grezzo -> str copione`). La skill viene usata fuori dall'app; il futuro `OllamaConverter` la implementerà dentro l'app, con lo stesso prompt e lo stesso validator.

### Fase 3 – Motore di generazione ✅

> Completata. Collaudo su *Così non vale*: LAURA, scena 4, 5,4 minuti di audio in circa 20 s; le esecuzioni successive usano la cache. Decisioni prese durante l'implementazione:
>
> - **Didascalie dentro le battute**: il testo tra parentesi viene tolto prima della lettura, salvo `leggi_didascalie`. Una battuta fatta solo di gesti (`A: (annuisce)`): se è di un altro personaggio viene saltata; se è la mia, resta la pausa minima.
> - **Contesto N**: conta solo le battute altrui che si sentono. Le mie battute precedenti che cadono nel blocco si sentono solo in modalità `letta`, senza pausa. Le scene in cui il personaggio non parla vengono saltate.
> - **Battuta detta insieme e altrui**: la legge la voce del primo personaggio incluso.
> - **Voci**: edge-tts ha 4 voci italiane (2 maschili e 2 femminili). L'assegnazione automatica alterna i generi e, quando le voci finiscono, cambia il tono. Il genere dei personaggi non è noto: si correggono con `--voce`.
> - **Valori predefiniti**: contesto 3, pausa minima 1,5 s, massima 30 s, stacco 1,5 s, 0,4 s di respiro dopo ogni battuta letta.
> - Lo stacco tra i blocchi è un silenzio (deciso: niente segnale sonoro).

Si divide in due passi:

1. **Piano** (`piano.py`): funzione pura `(copione, opzioni) -> lista di segmenti`, dove un segmento è `Parla(personaggio, testo)` oppure `Silenzio(ms)`. Si testa senza TTS.
2. **Render** (`render.py`): sintetizza i segmenti con il TTS (con cache su disco per `(voce, testo)`) e li unisce in un mp3.

Opzioni:

| Opzione | Punto | Descrizione |
| :--- | :--- | :--- |
| `personaggio` | 5 | Il personaggio da studiare. Una battuta detta insieme che lo include è sua. |
| `personaggi_inclusi` | 2 | Le battute degli altri personaggi da far sentire. Le battute degli esclusi vengono saltate del tutto. Di default tutti. |
| `modalita_battuta` | 4 | `muta`: al posto della battuta c'è solo silenzio. `letta`: la battuta viene letta e poi c'è la pausa per ripeterla. In futuro anche `verifica`: prima la pausa, poi la battuta letta. |
| `pausa` | 3 | Durata = durata TTS della mia battuta (calcolata anche se è muta) × `moltiplicatore` (default 1.2), limitata tra `min_s` e `max_s`. Il `[pausa=N]` scritto nel file ha la precedenza. |
| `contesto` | 6 | `N` oppure `tutto`. Con N: per ogni mia battuta si sentono le N battute udibili precedenti, poi la mia battuta, poi lo `stacco_blocchi` (1,5 s di silenzio). Con `tutto`: la scena intera in ordine, una volta sola. Il contesto non attraversa i confini di scena. |
| `scene` | – | Quali scene includere. Di default tutte. |
| `leggi_didascalie` | – | Di default no. |
| `voci` | – | Associazione personaggio → voce edge-tts, assegnata in automatico e modificabile. |

### Fase 4 – API FastAPI ✅

> Completata (`backend/src/copione_audio/api/main.py`, avvio con `uvicorn copione_audio.api.main:app`; documentazione interattiva su `/docs`). Rispetto al piano:
>
> - tutti gli endpoint stanno sotto **`/api`** (es. `POST /api/copioni/analizza`), così non si scontrano con il frontend servito su `/`;
> - `analizza` e `audio` ricevono il copione come JSON `{"testo": …}`: il frontend legge il file nel browser;
> - `analizza` restituisce anche, per ogni scena, chi parla;
> - l'audio è un **job asincrono**: `POST /api/audio` (202, con `id`; errori di copione e opzioni subito come 422) → `GET /api/audio/{id}` (stato, `fatte`/`totali`) → `GET /api/audio/{id}/mp3`;
> - le opzioni sono il dataclass `Opzioni` del piano (stessi nomi e default, `contesto: null` = tutto, `scene` con indici da 0); `voci` è facoltativo e i personaggi mancanti ricevono una voce automatica;
> - i lavori stanno in memoria e gli mp3 in una cartella temporanea: si perdono al riavvio (va bene per l'uso in locale).

- `POST /copioni/analizza`: riceve un `.copione.txt` e restituisce i personaggi, le scene, il numero di battute e gli errori di validazione.
- `POST /copioni/pdf`: riceve un PDF e restituisce il testo grezzo. Più avanti, con il modello locale, restituirà direttamente il copione convertito.
- `GET /voci?lingua=it`: le voci edge-tts disponibili.
- `POST /audio`: riceve copione e opzioni, genera l'mp3 e lo restituisce da scaricare. La generazione può richiedere tempo: si valuta un job asincrono con stato e progresso.
- In produzione FastAPI serve anche la build statica di Svelte, così c'è un solo processo.

### Fase 5 – Frontend Svelte ✅

> Completata (`frontend/`). Provata end-to-end in Chrome headless sul copione reale: caricamento, scelta di personaggio e scena, generazione, ascolto e download; tema chiaro e scuro, larghezza telefono senza scroll orizzontale, nessun errore in console. Rispetto al piano:
>
> - **editor del testo** nel passo "Controlla": gli errori sono cliccabili e portano alla riga, si rianalizza senza ricaricare il file e si può scaricare il copione corretto;
> - due endpoint in più per le voci: `POST /api/voci/assegna` (precompila i menu) e `POST /api/voci/anteprima` (▶);
> - le scene in cui il personaggio non parla sono mostrate ma disattivate (il piano le salta comunque);
> - si ricordano nel browser le opzioni generali e, per ogni copione (per titolo), personaggio, esclusi e voci.

Decisione: le **voci si scelgono qui**, non nell'intestazione del copione. L'assegnazione automatica non conosce il genere dei personaggi, quindi la UI deve rendere facile correggerla.

Flusso in una sola pagina:

1. **Carica**: `.copione.txt` oppure PDF. Per il PDF, nella prima versione si spiega come convertirlo con la skill.
2. **Controlla**: errori di validazione ed elenco di personaggi e scene.
3. **Configura**:
   - personaggio da studiare;
   - checkbox dei personaggi da includere;
   - muta o letta;
   - moltiplicatore e limiti della pausa;
   - contesto N o tutto;
   - scene;
   - voci, con anteprima.
4. **Genera**: barra di avanzamento, poi download dell'mp3.

Le impostazioni si ricordano nel browser.

### Fase 6 – Opzionale

- **Eseguibile ovunque**: un `Dockerfile` unico ✅ (multi-stage: Node per il frontend, uv per il backend, `python:3.14-slim` con ffmpeg; cache TTS nel volume `/data/cache`). Nessun deploy online: l'app resta in locale.
- **Modello locale**: `OllamaConverter` integrato nell'upload del PDF.
- **Più personaggi studiati insieme** (es. due ruoli piccoli): `personaggio` diventa un elenco.
- **TTS offline** ✅: `PiperTTS` dietro `TTSEngine`, scelto dall'interfaccia (Online/Offline) e passato all'API nel campo `motore`. Note:
  - voci italiane disponibili: paola e serena (femminili), riccardo (maschile, qualità `x_low`); `python -m copione_audio.tts.piper` scarica le tre consigliate (circa 150 MB) in `~/.local/share/copione-audio/piper` o `$COPIONE_AUDIO_PIPER`;
  - Piper non ha toni: il tono (in Hz, come per edge-tts) viene spostato dopo la sintesi con ffmpeg, rispetto a una voce media di 200 Hz; la velocità diventa `length_scale`;
  - l'audio viene salvato in mp3 a 64 kbit/s, così la cache resta piccola;
  - i modelli non dichiarano il genere: è scritto in `GENERI` per le voci note;
  - le voci scelte nel browser sono ricordate per motore; l'elenco delle voci Piper si rilegge ogni volta, quindi una voce appena scaricata compare senza riavviare;
  - collaudo: LAURA, scena 4 di *Così non vale*, 5,3 minuti di audio in 5 s (circa 20 s con edge-tts).
- **Player interattivo** nel browser.

---

## Domande aperte

Nessuna al momento.
