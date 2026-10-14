<script lang="ts">
  import type { Analisi } from './api'

  type Props = {
    analisi: Analisi
    /** Il testo del copione, modificabile nell'editor. */
    testo: string
    nomeFile: string
    inAnalisi: boolean
    onrianalizza: () => void
  }

  let { analisi, testo = $bindable(), nomeFile, inAnalisi, onrianalizza }: Props = $props()

  let editor = $state<HTMLTextAreaElement>()
  // Con errori l'editor si apre da solo; l'utente può comunque aprirlo e chiuderlo.
  let aperto = $derived(analisi.errori.length > 0)
  let modificato = $state(false)

  const totaleBattute = $derived(analisi.scene.reduce((somma, s) => somma + s.battute, 0))

  /** Porta l'editor alla riga indicata (da 1) e la seleziona. */
  function vaiARiga(riga: number) {
    aperto = true
    requestAnimationFrame(() => {
      if (!editor) return
      const righe = testo.split('\n')
      const inizio = righe.slice(0, riga - 1).reduce((n, r) => n + r.length + 1, 0)
      editor.focus()
      editor.setSelectionRange(inizio, inizio + (righe[riga - 1]?.length ?? 0))
      // Scorre in modo che la riga sia visibile.
      const altezzaRiga = editor.scrollHeight / righe.length
      editor.scrollTop = Math.max(0, (riga - 4) * altezzaRiga)
    })
  }

  function scarica() {
    const url = URL.createObjectURL(new Blob([testo], { type: 'text/plain;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = nomeFile.endsWith('.copione.txt') ? nomeFile : `${analisi.titolo || 'copione'}.copione.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  function rianalizza() {
    modificato = false
    onrianalizza()
  }
</script>

<div class="riepilogo">
  <div>
    <h3>{analisi.titolo || 'Senza titolo'}</h3>
    <p class="tenue">
      {nomeFile} · lingua <code>{analisi.lingua || '?'}</code> · {analisi.scene.length} scene ·
      {totaleBattute} battute
    </p>
  </div>
  {#if analisi.errori.length === 0}
    <span class="etichetta ok">Nessun errore</span>
  {:else}
    <span class="etichetta errore">{analisi.errori.length} errori</span>
  {/if}
</div>

<div class="personaggi">
  {#each analisi.personaggi as nome (nome)}
    <span class="chip">{nome} <span class="tenue">{analisi.battute_per_personaggio[nome]}</span></span>
  {/each}
</div>

{#if analisi.errori.length}
  <ul class="errori">
    {#each analisi.errori as errore, i (i)}
      <li>
        {#if errore.riga}
          <button type="button" class="link" onclick={() => vaiARiga(errore.riga!)}>
            riga {errore.riga}
          </button>
        {/if}
        {errore.messaggio}
      </li>
    {/each}
  </ul>
{/if}

<details open={aperto} ontoggle={(e) => (aperto = e.currentTarget.open)}>
  <summary>Modifica il testo</summary>
  <textarea
    bind:this={editor}
    bind:value={testo}
    oninput={() => (modificato = true)}
    spellcheck="false"
    rows="16"
    aria-label="Testo del copione"
  ></textarea>
  <div class="azioni">
    <button type="button" onclick={rianalizza} disabled={inAnalisi}>
      {inAnalisi ? 'Analisi…' : 'Rianalizza'}
    </button>
    <button type="button" class="secondario" onclick={scarica}>Scarica il copione</button>
    {#if modificato}
      <span class="tenue">Modifiche non ancora analizzate</span>
    {/if}
  </div>
</details>

<style>
  .riepilogo {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
  }

  h3 {
    margin: 0;
  }

  .riepilogo p {
    margin: 0.25rem 0 0;
  }

  .personaggi {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 1rem 0;
  }

  .errori {
    margin: 0 0 1rem;
    padding: 0.75rem 1rem 0.75rem 2rem;
    border-radius: var(--raggio);
    background: var(--errore-tenue);
    max-height: 14rem;
    overflow: auto;
  }

  .errori li + li {
    margin-top: 0.25rem;
  }

  summary {
    cursor: pointer;
    font-weight: 600;
  }

  textarea {
    width: 100%;
    margin-top: 0.75rem;
    font-family: var(--mono);
    font-size: 0.85rem;
    line-height: 1.45;
    resize: vertical;
  }

  .azioni {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
  }
</style>
