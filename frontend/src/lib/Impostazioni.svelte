<script lang="ts">
  import type { Motore } from './api'
  import type { OpzioniGenerali } from './impostazioni'
  import VociOffline from './VociOffline.svelte'

  type Props = {
    generali: OpzioniGenerali
    motore: Motore
    /** Lingua delle voci offline da proporre: quella del copione, se è caricato. */
    lingua: string
    caricamentoVoci: boolean
    erroreVoci: string | null
    oncambiamotore: (motore: Motore) => void
  }

  let {
    generali = $bindable(),
    motore,
    lingua,
    caricamentoVoci,
    erroreVoci,
    oncambiamotore,
  }: Props = $props()

  // Ultimo numero di battute scelto, per ritrovarlo tornando da "scena intera".
  let ultimoContesto = $state(3)
  let gestioneAperta = $state(false)

  function cambiaContesto(scenaIntera: boolean) {
    if (scenaIntera) {
      if (generali.contesto !== null) ultimoContesto = generali.contesto
      generali.contesto = null
    } else {
      generali.contesto = ultimoContesto
    }
  }

  function apriGestione() {
    gestioneAperta = true
    document.getElementById('voci-offline')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  /** Dopo un cambio nella cartella delle voci, ricarica le voci se il motore è Piper. */
  function vociOfflineAggiornate() {
    if (motore === 'piper') oncambiamotore('piper')
  }
</script>

<div class="griglia">
  <fieldset class="campo">
    <legend>Sintesi vocale</legend>
    <label class="scelta">
      <input
        type="radio"
        name="motore"
        checked={motore === 'edge'}
        disabled={caricamentoVoci}
        onchange={() => oncambiamotore('edge')}
      />
      <span><strong>Online</strong> — voci Microsoft, più naturali</span>
    </label>
    <label class="scelta">
      <input
        type="radio"
        name="motore"
        checked={motore === 'piper'}
        disabled={caricamentoVoci}
        onchange={() => oncambiamotore('piper')}
      />
      <span><strong>Offline</strong> — Piper, senza internet</span>
    </label>
    {#if caricamentoVoci}
      <p class="tenue nota">Caricamento delle voci…</p>
    {:else if erroreVoci}
      <p class="testo-errore nota" role="alert">{erroreVoci}</p>
    {/if}
    {#if motore === 'piper'}
      <button type="button" class="link nota" onclick={apriGestione}>Gestisci voci offline</button>
    {/if}
  </fieldset>

  <fieldset class="campo">
    <legend>La tua battuta</legend>
    <label class="scelta">
      <input type="radio" bind:group={generali.modalita_battuta} value="muta" />
      <span><strong>Muta</strong> — solo la pausa per dirla</span>
    </label>
    <label class="scelta">
      <input type="radio" bind:group={generali.modalita_battuta} value="letta" />
      <span><strong>Letta</strong> — la senti, poi la ripeti</span>
    </label>
  </fieldset>

  <fieldset class="campo">
    <legend>Prima di ogni tua battuta</legend>
    <label class="scelta">
      <input
        type="radio"
        name="contesto"
        checked={generali.contesto !== null}
        onchange={() => cambiaContesto(false)}
      />
      <span>
        le
        <input
          class="numero"
          type="number"
          min="0"
          max="50"
          disabled={generali.contesto === null}
          value={generali.contesto ?? ultimoContesto}
          oninput={(e) => (generali.contesto = Math.max(0, e.currentTarget.valueAsNumber || 0))}
          aria-label="Numero di battute precedenti"
        />
        battute precedenti
      </span>
    </label>
    <label class="scelta">
      <input
        type="radio"
        name="contesto"
        checked={generali.contesto === null}
        onchange={() => cambiaContesto(true)}
      />
      <span>la scena intera, una volta sola</span>
    </label>
  </fieldset>

  <fieldset class="campo">
    <legend>Pausa per dire la battuta</legend>
    <label class="riga">
      <span>Durata rispetto alla lettura</span>
      <span class="valore">
        <input type="range" min="0.5" max="3" step="0.1" bind:value={generali.moltiplicatore} />
        <output>×{generali.moltiplicatore.toFixed(1)}</output>
      </span>
    </label>
    <label class="riga">
      <span>Minimo (s)</span>
      <input class="numero" type="number" min="0" step="0.5" bind:value={generali.pausa_min_s} />
    </label>
    <label class="riga">
      <span>Massimo (s)</span>
      <input class="numero" type="number" min="1" step="1" bind:value={generali.pausa_max_s} />
    </label>
    <label class="riga">
      <span>Stacco tra i blocchi (s)</span>
      <input class="numero" type="number" min="0" step="0.5" bind:value={generali.stacco_s} />
    </label>
  </fieldset>
</div>

<label class="scelta didascalie">
  <input type="checkbox" bind:checked={generali.leggi_didascalie} />
  <span>Leggi anche le didascalie (voce del narratore)</span>
</label>

<VociOffline {lingua} bind:aperta={gestioneAperta} onaggiornate={vociOfflineAggiornate} />

<style>
  .griglia {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
    gap: 1rem 1.5rem;
    margin-bottom: 1rem;
  }

  .campo {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin: 0;
    padding: 0;
    border: 0;
    min-width: 0;
  }

  legend {
    font-weight: 600;
    padding: 0;
    margin-bottom: 0.2rem;
  }

  .scelta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
  }

  .didascalie {
    margin-bottom: 0.75rem;
  }

  .riga {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
  }

  .valore {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .valore input {
    width: 7rem;
  }

  output {
    min-width: 2.5rem;
    font-variant-numeric: tabular-nums;
  }

  .numero {
    width: 4.5rem;
  }

  .nota {
    align-self: flex-start;
    margin: 0.2rem 0 0;
    overflow-wrap: anywhere;
  }
</style>
