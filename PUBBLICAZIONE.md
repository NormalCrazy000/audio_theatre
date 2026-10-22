# Piano di pubblicazione

Obiettivo: rendere **pubblico il repository** su GitHub, con una licenza e senza problemi di diritto d'autore o di privacy. Si pubblica il **codice**, non un servizio: l'app resta da avviare in locale (vedi la decisione "Uso" in [`REFACTOR.md`](REFACTOR.md)).

## Decisioni prese

| Tema | Decisione |
| :--- | :--- |
| Cosa si pubblica | Il repository (codice, Dockerfile, documentazione). Niente istanza online, niente immagine Docker su un registry |
| Licenza | **GPL-3.0-or-later**: `piper-tts` è GPL-3.0-or-later e viene importato direttamente, quindi serve una licenza compatibile. Le altre dipendenze (edge-tts LGPL-3; FastAPI, pydub, onnxruntime MIT; pypdf, uvicorn BSD; python-multipart Apache-2.0; audioop-lts PSF) sono compatibili |
| Contributi | Nessun documento per chi contribuisce (CONTRIBUTING, template per le issue), almeno per ora |
| Storia git | Si riscrive **prima** di rendere pubblico il repository, finché è ancora privato |

## Ordine delle fasi

Le fasi 1 e 2 sono bloccanti: vanno fatte prima del cambio di visibilità, perché dopo non si possono più rimediare del tutto (fork, cache).

1. **Fase 1 – Pulizia della storia git** (bloccante) ✅
2. **Fase 2 – Email personale nei commit** (bloccante) ✅
3. **Fase 3 – Licenza** ✅
4. **Fase 4 – Trasparenza su servizi esterni e diritto d'autore** ✅
5. **Fase 5 – Sicurezza e impostazioni del repository** ✅
6. **Fase 6 – Controllo finale e pubblicazione**

---

### Fase 1 – Pulizia della storia git ✅

> Completata. Oltre a `battute.txt` e `audio/` c'era `frasi.txt`, la prima versione dello stesso copione: tolto anche quello. Il repository è stato ricreato su GitHub come `audio_theatre`, così sul server non resta nessun commit vecchio.

Nei commit vecchi ci sono ancora `battute.txt` (battute di un copione reale, protetto da diritto d'autore) e `audio/combinationAudio.mp3` (la sua lettura, circa 4,8 MB). Non sono più nell'albero, ma chi clona il repository li recupera dalla storia.

- [x] Backup del repository (clone `--mirror`).
- [x] Su un clone fresco: `git filter-repo --invert-paths --path battute.txt --path frasi.txt --path audio/ --path __pycache__/`.
- [x] Verificare con `git log --all --stat` che i file non ci siano più.
- [x] Repository ricreato su GitHub (al posto del `git push --force`) e copia di lavoro riallineata.

In alternativa: un repository nuovo con un solo commit iniziale, rinunciando alla storia.

### Fase 2 – Email personale nei commit ✅

Quasi tutti i commit hanno come autore l'email personale, che con il repository pubblico diventerebbe visibile.

- [x] Nello stesso passaggio di `git filter-repo`, `--mailmap` per sostituirla con l'indirizzo noreply di GitHub.
- [x] `git config user.email` con l'indirizzo noreply.
- [ ] Su GitHub (Settings → Emails): "Keep my email addresses private" e "Block command line pushes that expose my email".

### Fase 3 – Licenza ✅

> Completata. `license-files` non è stato aggiunto: il file della licenza sta nella radice, fuori da `backend/`, e non è previsto pubblicare il pacchetto su PyPI. Nell'immagine Docker la licenza è in `/app/LICENSE`.

- [x] File `LICENSE` con il testo della GPL-3.0.
- [x] `backend/pyproject.toml`: `license = "GPL-3.0-or-later"`.
- [x] `frontend/package.json`: `"license": "GPL-3.0-or-later"`.
- [x] `Dockerfile`: `LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"`.
- [x] README: sezione "Licenza".

### Fase 4 – Trasparenza su servizi esterni e diritto d'autore ✅

> Completata. Nel README ci sono le sezioni "Privacy e servizi esterni" e "Copioni e diritto d'autore". Nessun copione di esempio per ora. Il titolo del copione usato per il collaudo resta citato in `REFACTOR.md` e in una docstring: citare un titolo non è un problema.

Nel README:

- [x] **Privacy**: con la sintesi online (edge-tts) il testo del copione va ai server Microsoft; con Piper resta tutto sul computer. La skill `converti-copione` manda il copione ad Anthropic.
- [x] **edge-tts** usa il servizio di lettura ad alta voce di Edge, non un'API ufficiale: progetto non affiliato a Microsoft, il servizio può cambiare o smettere di funzionare.
- [x] **Voci Piper**: ognuna ha la sua licenza (alcune solo per ricerca o uso non commerciale), da controllare nella MODEL_CARD. L'app non le scarica né le distribuisce.
- [x] **Copioni**: chi usa l'app deve avere i diritti sui copioni che carica; l'app li elabora solo in locale.

Nel codice:

- [x] `.gitignore`: `*.pdf`, `*.mp3`, `*.copione.txt` e `audio/`, con eccezioni per eventuali esempi.
- [ ] (Rimandato) Se serve un copione di esempio, usarne uno di pubblico dominio (es. Goldoni) o scritto apposta.
- [x] Facoltativo: sostituire i nomi del copione reale (ora ROMEO e GIULIETTA) negli esempi di `conversione/istruzioni.md` e `docs/modello-locale.md`.

### Fase 5 – Sicurezza e impostazioni del repository ✅

Già a posto: nessun segreto nella storia, frontend senza chiamate esterne, porta pubblicata solo su `127.0.0.1`, container con utente non root.

- [x] README: l'app non ha login e non va esposta su internet (sezione "Sicurezza").
- [x] Limite alla dimensione degli upload (PDF e copione) e ai job in corso, per evitare che un file enorme blocchi l'app. Tolti anche i lavori vecchi (al massimo 20 in memoria).
- [x] Richieste accettate solo con `Host` e `Origin` locali (o in `$COPIONE_AUDIO_HOST`): senza login, un sito aperto nel browser poteva usare l'app (DNS rebinding, upload da un'altra origine).
- [ ] GitHub: Dependabot alerts, secret scanning con push protection, protezione di `main` (niente force push dopo la Fase 1). Spostato nella Fase 6: secret scanning e protezione dei branch sono gratuiti solo sui repository pubblici.
- [x] Decidere se tenere pubblici `CLAUDE.md`, `REFACTOR.md` e `TODO.md` (non contengono nulla di sensibile) e se disattivare le Issues: si tengono tutti, anche `PUBBLICAZIONE.md`, e le Issues restano attive.

### Fase 6 – Controllo finale e pubblicazione

- [ ] `gitleaks detect` (o `trufflehog git file://.`) sul repository riscritto.
- [ ] Clone fresco: test (`uv run pytest`), build del frontend e `docker compose up --build`.
- [ ] Settings → Change visibility → Public.
- [ ] Subito dopo: Dependabot alerts, secret scanning con push protection e una regola (ruleset) su `main` che vieta force push e cancellazione.

## Domande aperte

- **GPL o AGPL**: la AGPL-3.0 obbligherebbe a pubblicare le modifiche anche chi offre l'app come servizio web. Per uno strumento da usare in locale la GPL basta; da rivedere se un giorno si pensasse a un'istanza online.
- **Pubblicare un'istanza online**: fuori da questo piano. Servirebbero login, limiti d'uso, un'informativa privacy (GDPR, perché si trattano testi caricati dagli utenti) e una verifica sui termini d'uso del servizio dietro edge-tts.
