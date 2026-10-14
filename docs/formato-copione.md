# Formato standard del copione

Riferimento unico per chi scrive un copione a mano, per la skill `converti-copione` e per il futuro modello locale. Il parser è in `backend/src/copione_audio/copione/`.

Un copione è un file di testo **UTF-8** con estensione `.copione.txt`.

## Esempio

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
ROMEO e GIULIETTA: Addio!
```

## Regole

### Intestazione

Il file inizia con un'intestazione tra due righe `---`, con tre chiavi tutte obbligatorie:

| Chiave | Contenuto |
| :--- | :--- |
| `titolo` | Il titolo dell'opera. |
| `lingua` | Il codice della lingua per il TTS, per esempio `it` o `en`. |
| `personaggi` | L'elenco completo dei nomi ammessi, separati da virgole. |

### Corpo

| Elemento | Come si scrive | Note |
| :--- | :--- | :--- |
| **Battuta** | `NOME: testo` a inizio riga | Il nome va scritto esattamente come nell'intestazione: maiuscole e minuscole contano. |
| **Continuazione** | Riga che inizia con spazio o tab | Continua l'ultima battuta. Le righe vengono unite con uno spazio. |
| **Battuta detta insieme** | `ROMEO e GIULIETTA: testo` oppure `ROMEO, BALIA e GIULIETTA: testo` | Nomi separati da virgole e/o da ` e ` minuscola. Ogni nome deve essere dichiarato. Se tra i nomi c'è il personaggio studiato, la battuta è sua. |
| **Pausa personalizzata** | `NOME [pausa=SECONDI]: testo` | Accetta anche i decimali (`2.5` o `2,5`). Ha la precedenza sulla pausa calcolata. |
| **Scena** | Riga che inizia con `#` | Serve a scegliere le scene e azzera il contesto. Le battute prima del primo `#` formano una scena senza titolo. |
| **Didascalia** | Riga intera tra parentesi `( … )` | Di default non viene letta. Una didascalia dentro una battuta resta parte del testo. |
| **Riga vuota** | — | Ignorata. Non interrompe una battuta, che può continuare dopo una riga vuota. |

## Errori segnalati

Il parser non si ferma al primo errore: li raccoglie tutti, con il numero di riga quando c'è.

- Intestazione: mancante, non chiusa, chiave sconosciuta o ripetuta, chiave obbligatoria mancante, personaggio ripetuto.
- Riga non riconosciuta, cioè che non è né battuta, né scena, né didascalia.
- Riga indentata fuori da una battuta.
- Opzione tra `[ ]` non valida.
- Titolo di scena vuoto.
- Personaggio non dichiarato nell'intestazione.
- Battuta vuota.
- Copione senza battute.
