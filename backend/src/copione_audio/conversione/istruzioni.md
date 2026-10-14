# Istruzioni per convertire un copione nel formato standard

Ricevi il testo grezzo di un copione teatrale, di solito estratto da un PDF. Devi produrre un file nel formato standard descritto in `docs/formato-copione.md`. Il risultato deve passare la validazione senza errori.

## Obiettivo

Conservare **tutte le battute, nell'ordine e con le parole originali**. Il file serve a un attore per studiare la parte: una battuta persa, spezzata male o attribuita al personaggio sbagliato è l'errore più grave. Non correggere, riassumere o modernizzare il testo.

## Intestazione

- `titolo`: il titolo dell'opera, come compare nel copione.
- `lingua`: il codice della lingua del testo (`it`, `en`, …).
- `personaggi`: i nomi **esattamente come compaiono davanti alle battute**, separati da virgole, nell'ordine dell'elenco dei personaggi del copione se c'è. Se l'elenco iniziale scrive `Alberto` e le battute `ALBERTO:`, usa `ALBERTO`. Non mettere ruoli, descrizioni o nomi degli attori.

## Da togliere

- Copertina, autore, elenco dei personaggi con ruoli e attori, tabelle riassuntive, indici.
- Numeri di pagina, intestazioni e piè di pagina ripetuti.
- Righe con soli segni grafici o vuote.

## Da convertire

| Nel testo grezzo | Nel formato standard |
| :--- | :--- |
| Titolo di atto o di scena (`ATTO PRIMO`, `SCENA 1 (GIULIA, ALBERTO)`) | Una riga `# …`: `# Atto primo – Scena 1`. Ogni scena ha il suo `#`. Un atto senza scene diventa una scena. L'elenco dei presenti tra parentesi si può togliere. |
| Battuta `NOME: testo`, `NOME. testo`, `NOME – testo`, nome su una riga e testo sotto | `NOME: testo` |
| Battuta che va a capo, anche a cavallo di un cambio pagina | Righe di continuazione **indentate con due spazi** sotto la riga del nome. Un numero di pagina in mezzo va tolto. |
| Didascalia su righe proprie (in corsivo, tra parentesi, dopo `---` o `—`) | Una sola riga `(testo)`. Se è su più righe, uniscile in una. Non lasciare mai una riga che inizia con `---`. |
| Didascalia dentro una battuta: `GIULIA: (ride) Ciao` | Lasciala dov'è, tra parentesi. |
| Battuta di soli gesti: `ALBERTO: (annuisce)` | Lasciala com'è: per l'attore è comunque un'entrata. |
| Battuta detta da più personaggi (`ROMEO E GIULIETTA:`, `ROMEO-GIULIETTA:`) | `ROMEO e GIULIETTA:`, con la `e` minuscola o le virgole. Tutti i nomi devono essere nell'intestazione. |
| `TUTTI:` o un gruppo generico | I nomi dei presenti in scena, se si capiscono dal contesto. Altrimenti aggiungi `TUTTI` all'elenco dei personaggi. |
| Descrizione iniziale della scenografia | Una didascalia `( … )` subito dopo la prima scena, oppure toglila. |

## Controllo finale

1. Valida il risultato e correggi ogni errore segnalato, riga per riga.
2. Se il copione dichiara quante battute ha ogni personaggio, confronta i numeri con quelli calcolati e indaga le differenze.
3. Controlla a campione l'inizio, la fine e qualche cambio di pagina: nessuna battuta deve essere tagliata o fusa con la successiva.
