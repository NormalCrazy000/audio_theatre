<script lang="ts">
  import { onDestroy } from 'svelte'
  import { avviaAudio, ErroreApi, statoAudio, urlMp3, type Opzioni, type StatoLavoro, type Voce } from './api'

  type Props = {
    testo: string
    opzioni: Opzioni
    voci: Record<string, Voce>
    /** Se presente, la generazione non è possibile e viene mostrato il motivo. */
    blocco: string | null
  }

  let { testo, opzioni, voci, blocco }: Props = $props()

  let lavoro = $state<StatoLavoro | null>(null)
  let errore = $state<string | null>(null)
  let timer: ReturnType<typeof setTimeout> | undefined

  const inCorso = $derived(lavoro?.stato === 'in_corso')
  const percentuale = $derived(
    lavoro && lavoro.totali ? Math.round((lavoro.fatte / lavoro.totali) * 100) : 0,
  )

  onDestroy(() => clearTimeout(timer))

  async function genera() {
    clearTimeout(timer)
    errore = null
    lavoro = null
    try {
      lavoro = await avviaAudio(testo, opzioni, voci)
      controlla()
    } catch (e) {
      errore = e instanceof ErroreApi || e instanceof Error ? e.message : String(e)
    }
  }

  async function controlla() {
    if (!lavoro) return
    try {
      lavoro = await statoAudio(lavoro.id)
    } catch (e) {
      errore = e instanceof Error ? e.message : String(e)
      return
    }
    if (lavoro.stato === 'in_corso') timer = setTimeout(controlla, 700)
    else if (lavoro.stato === 'errore') errore = `Generazione non riuscita: ${lavoro.errore}`
  }

  function durata(secondi: number) {
    const minuti = Math.floor(secondi / 60)
    return `${minuti}:${String(Math.round(secondi % 60)).padStart(2, '0')}`
  }
</script>

<div class="genera">
  <button type="button" class="grande" onclick={genera} disabled={inCorso || blocco !== null}>
    {inCorso ? 'Generazione in corso…' : 'Genera l’audio'}
  </button>
  {#if blocco}
    <span class="tenue">{blocco}</span>
  {/if}
</div>

{#if inCorso && lavoro}
  <div class="progresso" role="progressbar" aria-valuenow={percentuale} aria-valuemin={0} aria-valuemax={100}>
    <div class="barra" style:width="{percentuale}%"></div>
  </div>
  <p class="tenue">
    {lavoro.totali ? `Sintesi delle battute: ${lavoro.fatte} di ${lavoro.totali}` : 'Preparazione…'}
  </p>
{/if}

{#if errore}
  <p class="testo-errore" role="alert">{errore}</p>
{/if}

{#if lavoro?.stato === 'completato'}
  <div class="risultato">
    <p>
      <strong>{lavoro.nome_file}</strong>
      {#if lavoro.durata_s}<span class="tenue"> · {durata(lavoro.durata_s)}</span>{/if}
    </p>
    <audio controls src={urlMp3(lavoro.id)}></audio>
    <a class="pulsante" href={urlMp3(lavoro.id)} download={lavoro.nome_file}>Scarica l’mp3</a>
  </div>
{/if}

<style>
  .genera {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .progresso {
    height: 0.6rem;
    margin-top: 1rem;
    border-radius: 999px;
    background: var(--bordo);
    overflow: hidden;
  }

  .barra {
    height: 100%;
    background: var(--accento);
    transition: width 0.3s;
  }

  .risultato {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1rem;
    padding: 1rem;
    border-radius: var(--raggio);
    background: var(--accento-tenue);
  }

  .risultato p {
    margin: 0;
  }

  audio {
    width: 100%;
  }

  .risultato .pulsante {
    align-self: flex-start;
  }
</style>
