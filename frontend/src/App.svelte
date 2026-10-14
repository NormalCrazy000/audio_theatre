<script lang="ts">
  import * as api from './lib/api'
  import type { Analisi, InfoVoce, Opzioni, Voce } from './lib/api'
  import Carica from './lib/Carica.svelte'
  import Configura from './lib/Configura.svelte'
  import Controlla from './lib/Controlla.svelte'
  import Genera from './lib/Genera.svelte'
  import { leggiOpzioni, leggiScelte, salvaOpzioni, salvaScelte } from './lib/impostazioni'

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
  $effect(() => {
    if (analisi && personaggio)
      salvaScelte(analisi.titolo, $state.snapshot({ personaggio, esclusi, voci }))
  })

  async function carica(contenuto: string, nome: string) {
    testo = contenuto
    nomeFile = nome
    titoloPreparato = null
    await analizzaTesto()
  }

  async function analizzaTesto() {
    inAnalisi = true
    errore = null
    try {
      const risultato = await api.analizza(testo)
      if (risultato.titolo !== titoloPreparato) await prepara(risultato)
      else scene = scene.filter((i) => i < risultato.scene.length)
      analisi = risultato
    } catch (e) {
      errore = e instanceof Error ? e.message : String(e)
    } finally {
      inAnalisi = false
    }
  }

  /** Imposta personaggio, scene e voci per un copione appena caricato. */
  async function prepara(nuova: Analisi) {
    const salvate = leggiScelte(nuova.titolo)
    const nomi = nuova.personaggi
    // Di default il personaggio salvato, altrimenti quello con più battute.
    personaggio =
      salvate.personaggio && nomi.includes(salvate.personaggio)
        ? salvate.personaggio
        : [...nomi].sort((a, b) => nuova.battute_per_personaggio[b] - nuova.battute_per_personaggio[a])[0] ?? ''
    esclusi = (salvate.esclusi ?? []).filter((n) => nomi.includes(n))
    scene = nuova.scene.map((s) => s.indice)
    titoloPreparato = nuova.titolo

    if (!nuova.lingua || nomi.length === 0) return
    try {
      const [elenco, assegnate] = await Promise.all([
        api.voci(nuova.lingua),
        api.assegnaVoci(nuova.lingua, nomi),
      ])
      const disponibili = new Set(elenco.map((v) => v.nome))
      const valide = Object.entries(salvate.voci ?? {}).filter(
        ([nome, voce]) => nome in assegnate && disponibili.has(voce.nome),
      )
      elencoVoci = elenco
      voci = { ...assegnate, ...Object.fromEntries(valide) }
    } catch (e) {
      elencoVoci = []
      voci = {}
      errore = `Voci non disponibili: ${e instanceof Error ? e.message : e}`
    }
  }
</script>

<header>
  <h1>Copione Audio</h1>
  <p class="tenue">Carica un copione, scegli la tua parte e ascolta le battute degli altri.</p>
</header>

<main>
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
        bind:generali
        bind:voci
        {elencoVoci}
      />
    </section>

    <section class="scheda">
      <h2><span class="numero-passo">4</span> Genera</h2>
      <Genera {testo} {opzioni} {voci} {blocco} />
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
