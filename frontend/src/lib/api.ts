// Tipi e chiamate dell'API (backend/src/copione_audio/api/main.py).

export type Errore = { riga: number | null; messaggio: string }

export type Scena = {
  indice: number
  titolo: string | null
  battute: number
  personaggi: string[]
}

export type Analisi = {
  titolo: string
  lingua: string
  personaggi: string[]
  battute_per_personaggio: Record<string, number>
  scene: Scena[]
  errori: Errore[]
}

export type Voce = { nome: string; tono: string; velocita: string }

export type InfoVoce = { nome: string; genere: string; lingua: string }

/** Le opzioni del piano audio (dataclass `Opzioni` in piano.py). */
export type Opzioni = {
  personaggio: string
  /** null = tutti. */
  personaggi_inclusi: string[] | null
  modalita_battuta: 'muta' | 'letta'
  moltiplicatore: number
  pausa_min_s: number
  pausa_max_s: number
  /** null = scena intera. */
  contesto: number | null
  stacco_s: number
  respiro_s: number
  /** Indici da 0; null = tutte. */
  scene: number[] | null
  leggi_didascalie: boolean
}

export type StatoLavoro = {
  id: string
  stato: 'in_corso' | 'completato' | 'errore'
  fatte: number
  totali: number
  errore: string | null
  durata_s: number | null
  nome_file: string
}

export const NARRATORE = 'NARRATORE'

/** Errore dell'API con il messaggio da mostrare e, se ci sono, gli errori del copione. */
export class ErroreApi extends Error {
  errori: Errore[]

  constructor(message: string, errori: Errore[] = []) {
    super(message)
    this.errori = errori
  }
}

async function chiama(percorso: string, init?: RequestInit): Promise<Response> {
  let risposta: Response
  try {
    risposta = await fetch(percorso, init)
  } catch {
    throw new ErroreApi('Server non raggiungibile: è avviato?')
  }
  if (!risposta.ok) {
    const corpo = await risposta.json().catch(() => null)
    const dettaglio = corpo?.detail
    if (typeof dettaglio === 'string') throw new ErroreApi(dettaglio)
    if (dettaglio?.messaggio) throw new ErroreApi(dettaglio.messaggio, dettaglio.errori ?? [])
    if (Array.isArray(dettaglio)) {
      // Errore di validazione di FastAPI: elenco di {loc, msg}.
      throw new ErroreApi(dettaglio.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join('; '))
    }
    throw new ErroreApi(`Errore ${risposta.status}`)
  }
  return risposta
}

async function json<T>(percorso: string, corpo?: unknown): Promise<T> {
  const init: RequestInit | undefined =
    corpo === undefined
      ? undefined
      : {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(corpo),
        }
  return (await chiama(percorso, init)).json()
}

export const analizza = (testo: string) => json<Analisi>('/api/copioni/analizza', { testo })

export const voci = (lingua: string) =>
  json<InfoVoce[]>(`/api/voci?lingua=${encodeURIComponent(lingua)}`)

export const assegnaVoci = (lingua: string, personaggi: string[]) =>
  json<Record<string, Voce>>('/api/voci/assegna', { lingua, personaggi })

/** L'audio di anteprima di una voce, come URL da riprodurre. */
export async function anteprima(voce: Voce, testo: string): Promise<string> {
  const risposta = await chiama('/api/voci/anteprima', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ voce, testo }),
  })
  return URL.createObjectURL(await risposta.blob())
}

export const avviaAudio = (testo: string, opzioni: Opzioni, voci: Record<string, Voce>) =>
  json<StatoLavoro>('/api/audio', { testo, opzioni, voci })

export const statoAudio = (id: string) => json<StatoLavoro>(`/api/audio/${id}`)

export const urlMp3 = (id: string) => `/api/audio/${id}/mp3`
