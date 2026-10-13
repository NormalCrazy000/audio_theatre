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
| TTS | **edge-tts**, con una voce diversa per ogni personaggio, dietro un'interfaccia comune per poter aggiungere in futuro un motore offline (es. Piper) |

## Ordine delle fasi

L'ordine segue le dipendenze: prima il formato dei dati, poi la logica (testabile senza interfaccia), poi l'API e infine la UI. I punti della richiesta originale sono indicati tra parentesi.

1. **Fase 0 – Pulizia e ristrutturazione**
2. **Fase 1 – Formato standard e parser** (punto 2)
3. **Fase 2 – Conversione con skill Claude** (punto 2)
4. **Fase 3 – Motore di generazione**: personaggio da studiare (5), personaggi inclusi (2), oscuramento (4), pause (3), contesto (6)
5. **Fase 4 – API FastAPI**
6. **Fase 5 – Frontend Svelte** (punto 1)
7. **Fase 6 – Opzionale**: eseguibile ovunque (punto 1), modello locale, TTS offline

---

### Fase 0 – Pulizia e ristrutturazione

- Rinominare "test" in "text" ovunque (`TestToAudio`, `test_to_audio`).
- Spostare la logica in un pacchetto (struttura sotto) e separarla da I/O e CLI.
- Correggere i bug noti:
  - `os.listdir(input)` prende anche file che non sono `.txt`;
  - l'output si chiama `nome.txt.mp3`;
  - `input("Premi INVIO")` blocca l'uso non interattivo;
  - le cartelle di input/output di `pdf_to_text` e `text_to_audio` non sono coerenti (vedi `TODO.md`).
- La CLI resta come wrapper sottile sopra il core: è utile per i test e per l'uso da script.

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
    cli.py
  tests/
frontend/         Svelte + Vite
.claude/skills/converti-copione/SKILL.md
```

### Fase 1 – Formato standard del copione

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
- **Override della pausa**: `NOME [pausa=SECONDI]: testo`.
- **Scena**: una riga che inizia con `#`. Serve a scegliere le scene e ad azzerare il contesto.
- **Didascalia**: una riga tra parentesi `( … )`. Di default non viene letta (diventa un'opzione).
- Le righe vuote vengono ignorate.
- Il validator segnala nomi non dichiarati, battute vuote e righe non riconosciute, indicando il numero di riga. La UI mostra questi errori.

Da fare: un parser con test, e la specifica copiata in `docs/formato-copione.md`, così diventa il riferimento sia per la skill sia per il modello locale.

### Fase 2 – Conversione PDF/testo → formato standard

- `conversione/pdf.py`: estrazione del testo grezzo dal PDF (riusa l'attuale `pdf_to_text.py`).
- **Skill Claude** `.claude/skills/converti-copione/`: riceve PDF o testo grezzo e produce un `.copione.txt` valido. Deve:
  - riconoscere i personaggi;
  - unire le battute spezzate a fine pagina;
  - togliere numeri di pagina e intestazioni;
  - convertire le didascalie.

  Alla fine esegue il validator e corregge gli eventuali errori.
- Interfaccia `Converter` (`testo_grezzo -> str copione`). La skill viene usata fuori dall'app; il futuro `OllamaConverter` la implementerà dentro l'app, con lo stesso prompt e lo stesso validator.

### Fase 3 – Motore di generazione

Si divide in due passi:

1. **Piano** (`piano.py`): funzione pura `(copione, opzioni) -> lista di segmenti`, dove un segmento è `Parla(personaggio, testo)` oppure `Silenzio(ms)`. Si testa senza TTS.
2. **Render** (`render.py`): sintetizza i segmenti con il TTS (con cache su disco per `(voce, testo)`) e li unisce in un mp3.

Opzioni:

| Opzione | Punto | Descrizione |
| :--- | :--- | :--- |
| `personaggio` | 5 | Il personaggio da studiare. |
| `personaggi_inclusi` | 2 | Le battute degli altri personaggi da far sentire. Le battute degli esclusi vengono saltate del tutto. Di default tutti. |
| `modalita_battuta` | 4 | `muta`: al posto della battuta c'è solo silenzio. `letta`: la battuta viene letta e poi c'è la pausa per ripeterla. In futuro anche `verifica`: prima la pausa, poi la battuta letta. |
| `pausa` | 3 | Durata = durata TTS della mia battuta (calcolata anche se è muta) × `moltiplicatore` (default 1.2), limitata tra `min_s` e `max_s`. Il `[pausa=N]` scritto nel file ha la precedenza. |
| `contesto` | 6 | `N` oppure `tutto`. Con N: per ogni mia battuta si sentono le N battute udibili precedenti, poi la mia battuta, poi lo `stacco_blocchi` (es. 1,5 s o un breve segnale). Con `tutto`: la scena intera in ordine, una volta sola. Il contesto non attraversa i confini di scena. |
| `scene` | – | Quali scene includere. Di default tutte. |
| `leggi_didascalie` | – | Di default no. |
| `voci` | – | Associazione personaggio → voce edge-tts, assegnata in automatico e modificabile. |

### Fase 4 – API FastAPI

- `POST /copioni/analizza`: riceve un `.copione.txt` e restituisce i personaggi, le scene, il numero di battute e gli errori di validazione.
- `POST /copioni/pdf`: riceve un PDF e restituisce il testo grezzo. Più avanti, con il modello locale, restituirà direttamente il copione convertito.
- `GET /voci?lingua=it`: le voci edge-tts disponibili.
- `POST /audio`: riceve copione e opzioni, genera l'mp3 e lo restituisce da scaricare. La generazione può richiedere tempo: si valuta un job asincrono con stato e progresso.
- In produzione FastAPI serve anche la build statica di Svelte, così c'è un solo processo.

### Fase 5 – Frontend Svelte

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

- **Eseguibile ovunque**: un `Dockerfile` unico, ed eventualmente il deploy su un servizio gratuito (Render, Fly.io, Hugging Face Spaces).
- **Modello locale**: `OllamaConverter` integrato nell'upload del PDF.
- **TTS offline**: un motore Piper dietro `TTSEngine`.
- **Player interattivo** nel browser.

---

## Domande aperte

- Si può studiare **più di un personaggio** alla volta, per esempio due ruoli piccoli?
- Come si gestiscono le battute dette insieme (`TUTTI:`, `ROMEO e GIULIETTA:`)?
- L'app resta solo in locale o va pubblicata online? Se va online servono limiti di uso e forse un login.
- Lo stacco tra i blocchi deve essere silenzio o un segnale sonoro?
