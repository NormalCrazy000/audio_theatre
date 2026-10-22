# Decisioni di progetto

Le scelte che non si ricavano dal codice, con il motivo. Se una cambia, va aggiornata qui.

## Generali

| Tema | Decisione |
| :--- | :--- |
| Uso | **Solo in locale**: niente istanza online, quindi niente login né account. I lavori stanno in memoria. L'API accetta solo richieste locali (vedi la sezione Sicurezza del README) |
| Stack | Backend FastAPI, frontend Svelte (SPA con Vite) servito da FastAPI in produzione. Nessuna CLI: l'app si usa dall'interfaccia web, la skill ha i suoi script |
| Formato del copione | Testo `NOME: battuta` con intestazione dei personaggi ([`formato-copione.md`](formato-copione.md)) |
| Conversione da PDF | La skill Claude `converti-copione`; in futuro un modello locale dietro la stessa interfaccia `Converter` ([`modello-locale.md`](modello-locale.md)). Le regole sono in un solo file, `conversione/istruzioni.md` |
| Output | Un **mp3 da scaricare**. Scartato un player interattivo nel browser |
| TTS | edge-tts (online) e Piper (offline) dietro `TTSEngine`, scelti dall'utente. Le voci si scelgono nell'interfaccia, non nel copione: l'assegnazione automatica non conosce il genere dei personaggi |
| Voci Piper | **L'app non scarica nulla**: mostra i link, l'utente scarica i file e li trascina nell'interfaccia |
| Più personaggi studiati insieme | Scartato: si studia un personaggio alla volta |

## Comportamento del piano audio

- **Contesto**: con N, per ogni mia battuta si sentono le N battute altrui udibili precedenti, poi la mia, poi lo stacco. Con "tutto" si sente la scena intera una volta sola. Il contesto non attraversa i confini di scena. Le mie battute precedenti che cadono nel blocco si sentono solo in modalità `letta`, senza pausa.
- **Pausa**: durata della lettura della mia battuta (calcolata anche se è muta) × moltiplicatore, tra minimo e massimo. `[pausa=N]` nel copione ha la precedenza.
- **Battuta non oscurata** (`letta`): viene letta, poi segue la pausa per ripeterla.
- **Battute dette insieme**: se tra i nomi c'è il personaggio studiato, la battuta è sua; altrimenti la legge la voce del primo personaggio incluso.
- **Didascalie**: il testo tra parentesi non viene letto, salvo `leggi_didascalie`. Una battuta di soli gesti viene saltata se è di un altro personaggio; se è mia resta la pausa minima.
- **Scene** in cui il personaggio non parla: saltate.
- **Stacco tra i blocchi**: silenzio, nessun segnale sonoro.
