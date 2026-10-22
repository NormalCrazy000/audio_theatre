<script lang="ts">
  import * as api from './lib/api'
  import type { Analisi, InfoVoce, Motore, Opzioni, Voce } from './lib/api'
  import Carica from './lib/Carica.svelte'
  import Configura from './lib/Configura.svelte'
  import Controlla from './lib/Controlla.svelte'
  import Genera from './lib/Genera.svelte'
  import Impostazioni from './lib/Impostazioni.svelte'
  import {
    leggiMotore,
    leggiOpzioni,
    leggiScelte,
    salvaMotore,
    salvaOpzioni,
    salvaScelte,
    type SceltePerCopione,
  } from './lib/impostazioni'

  let testo = $state('')
  let nomeFile = $state('')
  let analisi = $state<Analisi | null>(null)
  let inAnalisi = $state(false)
  let errore = $state<string | null>(null)

  let generali = $state(leggiOpzioni())
  let personaggio = $state('')
  let esclusi = $state<string[]>([])
  let scene = $state<number[]>([])
  let voci = $state<Record<string, Voce>>({})
  let elencoVoci = $state<InfoVoce[]>([])
  const motoreIniziale = leggiMotore()
  let motore = $state<Motore>(motoreIniziale)
  let caricamentoVoci = $state(false)
  let erroreVoci = $state<string | null>(null)

  // Le voci scelte per ogni motore, per ritrovarle cambiando motore.
  let vociPerMotore: NonNullable<SceltePerCopione['vociPerMotore']> = {}
  // Solo l'ultima richiesta di voci conta, se si cambia motore più volte.
  let richiestaVoci = 0
  // L'ultimo motore scelto: `motore` cambia solo quando le sue voci sono caricate.
  let motoreVoluto: Motore = motoreIniziale

  // Il copione (titolo) per cui sono state preparate le scelte: rianalizzare
  // lo stesso copione dopo una correzione non le azzera.
  let titoloPreparato: string | null = null

  const pronto = $derived(analisi !== null && analisi.errori.length === 0)

  const opzioni = $derived.by((): Opzioni | null => {
    if (!analisi) return null
    const esclusiAltri = esclusi.filter((n) => n !== personaggio)
    return {
      ...generali,
      personaggio,
      personaggi_inclusi: esclusiAltri.length
        ? analisi.personaggi.filter((n) => !esclusiAltri.includes(n))
        : null,
      scene: scene.length === analisi.scene.length ? null : scene,
    }
  })

  const blocco = $derived.by(() => {
    if (!analisi) return 'Carica un copione'
    if (Object.keys(voci).length === 0) return 'Voci non disponibili'
    const sceneMie = analisi.scene.filter((s) => s.personaggi.includes(personaggio))
    if (!sceneMie.some((s) => scene.includes(s.indice)))
      return `Scegli almeno una scena in cui parla ${personaggio}`
    if (generali.pausa_min_s > generali.pausa_max_s) return 'La pausa minima supera la massima'
    return null
  })

  // Le impostazioni si ricordano nel browser.
  $effect(() => salvaOpzioni($state.snapshot(generali)))
  $effect(() => salvaMotore(motore))
  $effect(() => {
    if (!analisi || !personaggio) return
    if (Object.keys(voci).length > 0)
      vociPerMotore = { ...vociPerMotore, [motore]: $state.snapshot(voci) }
    salvaScelte(analisi.titolo, { personaggio, esclusi: $state.snapshot(esclusi), vociPerMotore })
  })

  async function carica(contenuto: string, nome: string) {
    testo = contenuto
    nomeFile = nome
    titoloPreparato = null
    await analizzaTesto()
  }

  // Dopo l'ultima `await` lo stato cambia tutto insieme: gli effetti che
  // salvano le scelte non vedono mai un copione nuovo con le voci del vecchio.
  async function analizzaTesto() {
    inAnalisi = true
    errore = null
    try {
      const risultato = await api.analizza(testo)
      if (risultato.titolo !== titoloPreparato) {
        const salvate = leggiScelte(risultato.titolo)
        // Annulla un eventuale cambio di motore in corso: le voci si caricano qui.
        const richiesta = ++richiestaVoci
        const m = motoreVoluto
        const caricate = await vociDelMotore(risultato, m, salvate.vociPerMotore ?? {})
        prepara(risultato, salvate)
        const motoreCambiato = richiesta !== richiestaVoci
        if (!motoreCambiato) applicaVoci(m, caricate)
        analisi = risultato
        // Il motore è cambiato durante il caricamento: si ricaricano le sue voci.
        if (motoreCambiato) cambiaMotore(motoreVoluto)
      } else {
        scene = scene.filter((i) => i < risultato.scene.length)
        analisi = risultato
      }
    } catch (e) {
      errore = e instanceof Error ? e.message : String(e)
    } finally {
      inAnalisi = false
    }
  }

  /** Imposta personaggio e scene per un copione appena caricato. */
  function prepara(nuova: Analisi, salvate: SceltePerCopione) {
    const nomi = nuova.personaggi
    // Di default il personaggio salvato, altrimenti quello con più battute.
    personaggio =
      salvate.personaggio && nomi.includes(salvate.personaggio)
        ? salvate.personaggio
        : [...nomi].sort((a, b) => nuova.battute_per_personaggio[b] - nuova.battute_per_personaggio[a])[0] ?? ''
    esclusi = (salvate.esclusi ?? []).filter((n) => nomi.includes(n))
    scene = nuova.scene.map((s) => s.indice)
    vociPerMotore = salvate.vociPerMotore ?? {}
    titoloPreparato = nuova.titolo
  }

  type VociCaricate = { elenco: InfoVoce[]; voci: Record<string, Voce>; errore: string | null }

  /** Le voci del motore e la loro assegnazione, con le scelte salvate ancora valide. */
  async function vociDelMotore(
    copione: Analisi,
    m: Motore,
    salvate: NonNullable<SceltePerCopione['vociPerMotore']>,
  ): Promise<VociCaricate> {
    if (!copione.lingua || copione.personaggi.length === 0)
      return { elenco: [], voci: {}, errore: null }
    try {
      const [elenco, assegnate] = await Promise.all([
        api.voci(copione.lingua, m),
        api.assegnaVoci(copione.lingua, copione.personaggi, m),
      ])
      const disponibili = new Set(elenco.map((v) => v.nome))
      const valide = Object.entries(salvate[m] ?? {}).filter(
        ([nome, voce]) => nome in assegnate && disponibili.has(voce.nome),
      )
      return { elenco, voci: { ...assegnate, ...Object.fromEntries(valide) }, errore: null }
    } catch (e) {
      const messaggio = e instanceof Error ? e.message : String(e)
      return { elenco: [], voci: {}, errore: `Voci non disponibili: ${messaggio}` }
    }
  }

  function applicaVoci(m: Motore, caricate: VociCaricate) {
    motore = m
    elencoVoci = caricate.elenco
    voci = caricate.voci
    erroreVoci = caricate.errore
    caricamentoVoci = false
  }

  async function cambiaMotore(nuovo: Motore) {
    motoreVoluto = nuovo
    if (!analisi) {
      // Senza copione non ci sono voci da caricare: si caricheranno con il copione.
      richiestaVoci++
      applicaVoci(nuovo, { elenco: [], voci: {}, errore: null })
      return
    }
    const richiesta = ++richiestaVoci
    caricamentoVoci = true
    const caricate = await vociDelMotore(analisi, nuovo, vociPerMotore)
    if (richiesta !== richiestaVoci) return
    applicaVoci(nuovo, caricate)
  }
</script>

<header>
  <h1>Audio Theatre</h1>
  <p class="tenue">Carica un copione, scegli la tua parte e ascolta le battute degli altri.</p>
</header>

<main>
  <section class="scheda">
    <h2><span class="numero-passo" aria-hidden="true">⚙</span> Impostazioni</h2>
    <Impostazioni
      bind:generali
      {motore}
      lingua={analisi?.lingua || 'it'}
      {caricamentoVoci}
      {erroreVoci}
      oncambiamotore={cambiaMotore}
    />
  </section>

  <section class="scheda">
    <h2><span class="numero-passo">1</span> Carica</h2>
    <Carica oncaricato={carica} />
    {#if inAnalisi && !analisi}
      <p class="tenue">Analisi in corso…</p>
    {/if}
    {#if errore}
      <p class="testo-errore" role="alert">{errore}</p>
    {/if}
  </section>

  {#if analisi}
    <section class="scheda">
      <h2><span class="numero-passo">2</span> Controlla</h2>
      <Controlla {analisi} bind:testo {nomeFile} {inAnalisi} onrianalizza={analizzaTesto} />
    </section>
  {/if}

  {#if analisi && pronto && opzioni}
    <section class="scheda">
      <h2><span class="numero-passo">3</span> Configura</h2>
      <Configura
        {analisi}
        bind:personaggio
        bind:esclusi
        bind:scene
        bind:voci
        {elencoVoci}
        {motore}
        leggiDidascalie={generali.leggi_didascalie}
      />
    </section>

    <section class="scheda">
      <h2><span class="numero-passo">4</span> Genera</h2>
      <Genera {testo} {opzioni} {voci} {motore} {blocco} />
    </section>
  {/if}
</main>

<style>
  header,
  main {
    width: min(52rem, 100% - 2rem);
    margin-inline: auto;
  }

  header {
    padding: 2.5rem 0 1.5rem;
  }

  h1 {
    margin: 0;
    font-size: 1.9rem;
    letter-spacing: -0.02em;
  }

  header p {
    margin: 0.4rem 0 0;
  }

  main {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    padding-bottom: 3rem;
  }

  h2 {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0 0 1rem;
    font-size: 1.15rem;
  }

  .numero-passo {
    display: inline-grid;
    place-items: center;
    width: 1.7rem;
    height: 1.7rem;
    border-radius: 50%;
    background: var(--accento);
    color: var(--su-accento);
    font-size: 0.9rem;
  }
</style>
