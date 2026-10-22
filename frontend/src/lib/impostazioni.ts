// Impostazioni ricordate nel browser (localStorage). Ogni accesso è protetto:
// in navigazione privata o con lo storage bloccato l'app funziona lo stesso.

import type { Motore, Opzioni, Voce } from './api'

/** Le opzioni che valgono per qualsiasi copione. */
export type OpzioniGenerali = Omit<Opzioni, 'personaggio' | 'personaggi_inclusi' | 'scene'>

/** Le scelte legate a un copione (per titolo). */
export type SceltePerCopione = {
  personaggio?: string
  esclusi?: string[]
  /** Le voci di ogni motore: i nomi delle voci cambiano da un motore all'altro. */
  vociPerMotore?: Partial<Record<Motore, Record<string, Voce>>>
  /** Formato precedente: voci di edge-tts. */
  voci?: Record<string, Voce>
}

export const OPZIONI_PREDEFINITE: OpzioniGenerali = {
  modalita_battuta: 'muta',
  moltiplicatore: 1.2,
  pausa_min_s: 1.5,
  pausa_max_s: 30,
  contesto: 3,
  stacco_s: 1.5,
  respiro_s: 0.4,
  leggi_didascalie: false,
}

const CHIAVE_OPZIONI = 'audio-theatre:opzioni'
const CHIAVE_MOTORE = 'audio-theatre:motore'
const chiaveCopione = (titolo: string) => `audio-theatre:copione:${titolo}`

function leggi<T>(chiave: string): T | null {
  try {
    const valore = localStorage.getItem(chiave)
    return valore ? (JSON.parse(valore) as T) : null
  } catch {
    return null
  }
}

function scrivi(chiave: string, valore: unknown) {
  try {
    localStorage.setItem(chiave, JSON.stringify(valore))
  } catch {
    // Storage non disponibile: le impostazioni non verranno ricordate.
  }
}

export const leggiOpzioni = (): OpzioniGenerali => ({
  ...OPZIONI_PREDEFINITE,
  ...leggi<Partial<OpzioniGenerali>>(CHIAVE_OPZIONI),
})

export const salvaOpzioni = (opzioni: OpzioniGenerali) => scrivi(CHIAVE_OPZIONI, opzioni)

export const leggiMotore = (): Motore => (leggi<Motore>(CHIAVE_MOTORE) === 'piper' ? 'piper' : 'edge')

export const salvaMotore = (motore: Motore) => scrivi(CHIAVE_MOTORE, motore)

export function leggiScelte(titolo: string): SceltePerCopione {
  const { voci, ...scelte } = leggi<SceltePerCopione>(chiaveCopione(titolo)) ?? {}
  return voci && !scelte.vociPerMotore ? { ...scelte, vociPerMotore: { edge: voci } } : scelte
}

export const salvaScelte = (titolo: string, scelte: SceltePerCopione) =>
  scrivi(chiaveCopione(titolo), scelte)
