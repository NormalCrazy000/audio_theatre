<script lang="ts">
  type Props = {
    /** Chiamata con il contenuto di un file di testo caricato. */
    oncaricato: (testo: string, nomeFile: string) => void
  }

  let { oncaricato }: Props = $props()

  let sopra = $state(false)
  let pdf = $state<string | null>(null)
  let input: HTMLInputElement

  async function apri(file: File | undefined) {
    if (!file) return
    if (file.name.toLowerCase().endsWith('.pdf')) {
      pdf = file.name
      return
    }
    pdf = null
    oncaricato(await file.text(), file.name)
  }

  function ondrop(evento: DragEvent) {
    evento.preventDefault()
    sopra = false
    apri(evento.dataTransfer?.files[0])
  }
</script>

<button
  type="button"
  class="area"
  class:sopra
  onclick={() => input.click()}
  ondragover={(e) => {
    e.preventDefault()
    sopra = true
  }}
  ondragleave={() => (sopra = false)}
  {ondrop}
>
  <span class="icona" aria-hidden="true">⇪</span>
  <strong>Trascina qui il copione</strong>
  <span class="tenue">oppure clicca per scegliere un file <code>.copione.txt</code></span>
</button>
<input
  bind:this={input}
  type="file"
  accept=".txt,.pdf,text/plain,application/pdf"
  hidden
  onchange={(e) => apri(e.currentTarget.files?.[0])}
/>

{#if pdf}
  <div class="avviso" role="status">
    <p>
      <strong>{pdf}</strong> è un PDF: prima va convertito nel formato del copione.
    </p>
    <ol>
      <li>Mettilo nella cartella <code>pdf_folder/</code> del progetto.</li>
      <li>
        In Claude Code chiedi: <em>«converti pdf_folder/{pdf} con la skill converti-copione»</em>.
      </li>
      <li>Carica qui il file <code>.copione.txt</code> che viene creato.</li>
    </ol>
  </div>
{/if}

<style>
  .area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.35rem;
    width: 100%;
    padding: 2.5rem 1rem;
    border: 2px dashed var(--bordo-forte);
    border-radius: var(--raggio);
    background: var(--superficie);
    color: inherit;
    font: inherit;
    cursor: pointer;
    transition:
      border-color 0.15s,
      background 0.15s;
  }

  .area:hover,
  .area.sopra {
    border-color: var(--accento);
    background: var(--accento-tenue);
  }

  .icona {
    font-size: 2rem;
    color: var(--accento);
  }

  .avviso {
    margin-top: 1rem;
  }

  .avviso ol {
    margin: 0.5rem 0 0;
    padding-left: 1.25rem;
  }
</style>
