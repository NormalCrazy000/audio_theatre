<script lang="ts">
  import { aggiungiVociOffline, eliminaVoceOffline, vociOffline, type RisultatoAggiunta, type VociOffline } from './api'

  type Props = {
    /** Lingua del copione: il catalogo mostra le voci di questa lingua. */
    lingua: string
    aperta: boolean
    /** Chiamata quando le voci installate cambiano. */
    onaggiornate: () => void
  }

  let { lingua, aperta = $bindable(), onaggiornate }: Props = $props()

  let stato = $state<VociOffline | null>(null)
  let occupato = $state<string | null>(null)
  let errore = $state<string | null>(null)
  let esito = $state<RisultatoAggiunta | null>(null)
  let sopra = $state(false)
  let input: HTMLInputElement

  const GENERI: Record<string, string> = { Male: 'maschile', Female: 'femminile' }

  /** "it_IT-paola-medium" → "paola". */
  const speaker = (nome: string) => nome.split('-')[1] ?? nome

  async function esegui<T>(messaggio: string, azione: () => Promise<T>): Promise<T | null> {
    occupato = messaggio
    errore = null
    try {
      return await azione()
    } catch (e) {
      errore = e instanceof Error ? e.message : String(e)
      return null
    } finally {
      occupato = null
    }
  }

  async function aggiorna() {
    esito = null
    const nuovo = await esegui('Lettura della cartella…', () => vociOffline(lingua))
    if (nuovo) {
      stato = nuovo
      onaggiornate()
    }
  }

  async function aggiungi(elenco: FileList | null | undefined) {
    const file = [...(elenco ?? [])]
    if (file.length === 0) return
    esito = null
    const risultato = await esegui(`Copia di ${file.length} file…`, () => aggiungiVociOffline(file, lingua))
    if (risultato) {
      esito = risultato
      stato = risultato.voci
      if (risultato.aggiunti.length > 0) onaggiornate()
    }
  }

  async function elimina(nome: string) {
    if (!confirm(`Eliminare la voce ${nome}? I suoi file verranno cancellati dalla cartella.`)) return
    esito = null
    const nuovo = await esegui(`Eliminazione di ${nome}…`, () => eliminaVoceOffline(nome, lingua))
    if (nuovo) {
      stato = nuovo
      onaggiornate()
    }
  }

  function ondrop(evento: DragEvent) {
    evento.preventDefault()
    sopra = false
    aggiungi(evento.dataTransfer?.files)
  }
</script>

<details
  id="voci-offline"
  bind:open={aperta}
  ontoggle={(e) => {
    if (e.currentTarget.open && !stato) aggiorna()
  }}
>
  <summary>Gestisci voci offline</summary>

  <p class="tenue">
    L'app non scarica niente da sola. Per ogni voce scarica dai link <strong>tutti e due i file</strong>
    (modello <code>.onnx</code> e configurazione <code>.onnx.json</code>), poi trascinali nel riquadro qui
    sotto.
  </p>

  {#if stato}
    <h3>Voci disponibili ({lingua})</h3>
    {#if stato.catalogo.length === 0}
      <p class="tenue">Nessuna voce in catalogo per questa lingua: cercala nel repository qui sotto.</p>
    {/if}
    <ul class="elenco">
      {#each stato.catalogo as v (v.nome)}
        <li class="voce">
          <div class="intestazione">
            <strong>{speaker(v.nome)}</strong>
            <span class="tenue">{GENERI[v.genere] ?? ''} · qualità {v.qualita} · {v.mb} MB</span>
            {#if v.installata}<span class="etichetta ok">installata</span>{/if}
          </div>
          <div class="link">
            <a href={v.link_modello} rel="noreferrer">1. Modello <code>.onnx</code></a>
            <a href={v.link_configurazione} rel="noreferrer">2. Configurazione <code>.onnx.json</code></a>
            <a href={v.pagina} target="_blank" rel="noreferrer">Scheda e licenza ↗</a>
          </div>
          <span class="tenue piccolo">Dati: {v.dati}</span>
        </li>
      {/each}
    </ul>
    <p class="tenue piccolo">
      Voci di altre lingue: <a href={stato.repository} target="_blank" rel="noreferrer">{stato.repository}</a>
    </p>
  {/if}

  <button
    type="button"
    class="area"
    class:sopra
    disabled={occupato !== null}
    onclick={() => input.click()}
    ondragover={(e) => {
      e.preventDefault()
      sopra = true
    }}
    ondragleave={() => (sopra = false)}
    {ondrop}
  >
    <span class="icona" aria-hidden="true">⇪</span>
    <strong>{occupato ?? 'Trascina qui i file delle voci'}</strong>
    <span class="tenue">oppure clicca per sceglierli (<code>.onnx</code> e <code>.onnx.json</code>)</span>
  </button>
  <input
    bind:this={input}
    type="file"
    accept=".onnx,.json"
    multiple
    hidden
    onchange={(e) => {
      aggiungi(e.currentTarget.files)
      e.currentTarget.value = ''
    }}
  />

  {#if errore}
    <p class="testo-errore" role="alert">{errore}</p>
  {/if}
  {#if esito}
    <div role="status">
      {#if esito.aggiunti.length > 0}
        <p class="ok">Aggiunti: {esito.aggiunti.join(', ')}</p>
      {/if}
      {#each esito.errori as e (e.file)}
        <p class="testo-errore"><strong>{e.file}</strong>: {e.messaggio}</p>
      {/each}
    </div>
  {/if}

  {#if stato}
    <h3>Installate</h3>
    {#if stato.installate.length === 0}
      <p class="tenue">Nessuna voce nella cartella.</p>
    {/if}
    <ul class="elenco">
      {#each stato.installate as v (v.nome)}
        <li class="installata">
          <span>
            <strong>{v.nome}</strong>
            <span class="tenue">· {v.mb} MB</span>
            {#if !v.modello}
              <span class="etichetta errore">manca il file .onnx</span>
            {:else if !v.configurazione}
              <span class="etichetta errore">manca il file .onnx.json (o non è valido)</span>
            {/if}
          </span>
          <button type="button" class="secondario" disabled={occupato !== null} onclick={() => elimina(v.nome)}>
            Elimina
          </button>
        </li>
      {/each}
    </ul>

    <p class="tenue piccolo cartella">
      Puoi anche copiare i file a mano in <code>{stato.cartella}</code>, poi
      <button type="button" class="link" disabled={occupato !== null} onclick={aggiorna}>aggiorna l'elenco</button>
    </p>
  {/if}
</details>

<style>
  details {
    border-top: 1px solid var(--bordo);
    padding: 0.75rem 0;
  }

  summary {
    cursor: pointer;
    font-weight: 600;
  }

  h3 {
    margin: 1rem 0 0.5rem;
    font-size: 1rem;
  }

  .elenco {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    margin: 0;
    padding: 0;
    list-style: none;
  }

  .voce {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    padding: 0.7rem 0.9rem;
    border: 1px solid var(--bordo);
    border-radius: var(--raggio);
  }

  .intestazione,
  .link {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.3rem 0.9rem;
  }

  .link a {
    color: var(--accento);
    font-weight: 600;
  }

  .piccolo {
    font-size: 0.88rem;
  }

  .installata {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    overflow-wrap: anywhere;
  }

  .ok {
    color: var(--successo);
  }

  .cartella {
    margin-top: 0.75rem;
    overflow-wrap: anywhere;
  }

  .area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.35rem;
    width: 100%;
    margin-top: 1rem;
    padding: 1.75rem 1rem;
    border: 2px dashed var(--bordo-forte);
    border-radius: var(--raggio);
    background: var(--superficie);
    color: inherit;
    font: inherit;
    font-weight: normal;
    cursor: pointer;
    transition:
      border-color 0.15s,
      background 0.15s;
  }

  .area:hover:not(:disabled),
  .area.sopra {
    border-color: var(--accento);
    background: var(--accento-tenue);
    filter: none;
  }

  .icona {
    font-size: 1.6rem;
    color: var(--accento);
  }
</style>
