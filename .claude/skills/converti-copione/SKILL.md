---
name: converti-copione
description: Converte un copione teatrale (PDF o testo grezzo) nel formato standard `.copione.txt` del progetto, e lo valida finché non ha errori. Usala quando l'utente chiede di convertire, importare o preparare un copione o un PDF di un copione per generare l'audio.
---

# Converti un copione nel formato standard

Prima di iniziare leggi:

- `docs/formato-copione.md`: il formato di arrivo;
- `backend/src/copione_audio/conversione/istruzioni.md`: le regole di conversione. Sono condivise con il futuro convertitore locale (Ollama), quindi se migliori una regola aggiornala lì, non qui.

Tutti i comandi vanno lanciati dalla radice del progetto.

## Procedimento

### 1. Ottieni il testo grezzo

Se l'input è un PDF:

```bash
uv run --project backend python .claude/skills/converti-copione/estrai.py "percorso/copione.pdf" > <scratchpad>/grezzo.txt
```

Se è già testo, usalo così com'è.

Se il testo estratto ha **parole spezzate** (`sc ena`, `persona ggi`) o non si distinguono parlato e didascalie, prova gli strumenti di poppler:

- `pdftotext -layout FILE.pdf out.txt`: parole intere e rientri conservati;
- `pdftohtml -xml -i -q FILE.pdf out`: ogni riga con posizione e stile (`<b>`, `<i>`). Molti copioni scrivono i nomi in grassetto e le didascalie in corsivo: classificare per font è molto più affidabile che per posizione. Le righe con `top` vicini (entro pochi pixel) sono la stessa riga.

### 2. Studia la struttura

Leggi l'inizio, una parte centrale e la fine del testo grezzo. Annota:

- come sono scritti i nomi davanti alle battute (`NOME:`, `NOME.`, …) e l'elenco completo dei personaggi;
- come sono indicati atti e scene;
- come sono indicate le didascalie su righe proprie;
- i numeri di pagina, le intestazioni ripetute e le parti iniziali da togliere;
- eventuali conteggi delle battute per personaggio, utili al controllo finale.

### 3. Converti

- **Copione lungo e regolare** (più di qualche pagina, con un formato ripetitivo): scrivi nello scratchpad uno script Python su misura per quel copione, che applichi le regole di `istruzioni.md`. Lo script è usa e getta: **non va salvato nel progetto**. Poi correggi a mano i casi che lo script non gestisce.
- **Copione breve o irregolare**: riscrivilo direttamente nel formato standard.

Salva il risultato accanto all'originale, con lo stesso nome ed estensione `.copione.txt` (es. `pdf_folder/Titolo.pdf` → `pdf_folder/Titolo.copione.txt`), salvo diversa indicazione dell'utente.

### 4. Valida e correggi

```bash
uv run --project backend python .claude/skills/converti-copione/valida.py "percorso/Titolo.copione.txt"
```

Lo script stampa le battute per personaggio e per scena e gli errori con il numero di riga, ed esce con codice 1 se ci sono errori. Correggi e ripeti finché non dice `Nessun errore.`

Correggi la causa nello script quando un errore si ripete; usa le modifiche a mano solo per i casi isolati.

### 5. Controlla il contenuto

Un file senza errori può comunque essere sbagliato. Prima di consegnare:

1. Se il copione ha un conteggio delle battute (per personaggio o per scena), confrontalo con quello di `valida.py`. Spiega ogni differenza: controlla anche nel testo grezzo, perché il conteggio del copione può essere sbagliato o vecchio. Se non c'è, conta le righe di nome nel testo grezzo (per esempio i grassetti) e confrontale.
2. Verifica che nessuna parola del parlato sia andata persa: confronta le parole del parlato nel testo grezzo con quelle delle battute (senza le parti tra parentesi).
3. Confronta a campione con il testo grezzo l'inizio, la fine e almeno tre cambi di pagina.
4. Cerca battute sospette: molto lunghe (due battute fuse), che contengono `NOME:` di un altro personaggio, o che finiscono a metà frase.

### 6. Riferisci all'utente

- il file creato;
- il numero di scene e le battute per personaggio;
- le scelte non ovvie (per esempio come hai trattato `TUTTI:` o una didascalia ambigua);
- le differenze rimaste con il conteggio del copione e i punti da ricontrollare a mano.
