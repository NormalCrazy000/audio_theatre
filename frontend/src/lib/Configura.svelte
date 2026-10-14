<script lang="ts">
  import { anteprima, NARRATORE, type Analisi, type InfoVoce, type Voce } from './api'
  import type { OpzioniGenerali } from './impostazioni'

  type Props = {
    analisi: Analisi
    personaggio: string
    /** Personaggi da non far sentire. */
    esclusi: string[]
    /** Indici delle scene scelte. */
    scene: number[]
    generali: OpzioniGenerali
    voci: Record<string, Voce>
    elencoVoci: InfoVoce[]
  }

  let {
    analisi,
    personaggio = $bindable(),
    esclusi = $bindable(),
    scene = $bindable(),
    generali = $bindable(),
    voci = $bindable(),
    elencoVoci,
  }: Props = $props()

  const TONI = ['-24Hz', '-12Hz', '+0Hz', '+12Hz', '+24Hz']

  const altri = $derived(analisi.personaggi.filter((n) => n !== personaggio))
  const sceneMie = $derived(
    analisi.scene.filter((s) => s.personaggi.includes(personaggio)).map((s) => s.indice),
  )
  const conVoce = $derived([
    ...analisi.personaggi,
    ...(generali.leggi_didascalie ? [NARRATORE] : []),
  ])

  // Ultimo numero di battute scelto, per ritrovarlo tornando da "scena intera".
  let ultimoContesto = $state(3)
  let inAscolto = $state<string | null>(null)
  let erroreAnteprima = $state<string | null>(null)

  function cambiaContesto(scenaIntera: boolean) {
    if (scenaIntera) {
      if (generali.contesto !== null) ultimoContesto = generali.contesto
      generali.contesto = null
    } else {
      generali.contesto = ultimoContesto
    }
  }

  function alternaEscluso(nome: string, incluso: boolean) {
    esclusi = incluso ? esclusi.filter((n) => n !== nome) : [...esclusi, nome]
  }

  function alternaScena(indice: number, scelta: boolean) {
    scene = scelta ? [...scene, indice].sort((a, b) => a - b) : scene.filter((i) => i !== indice)
  }

  async function ascolta(nome: string) {
    inAscolto = nome
    erroreAnteprima = null
    try {
      const frase = nome === NARRATORE ? 'Entra Giulia, molto agitata.' : `Buongiorno, sono ${nome}.`
      const url = await anteprima(voci[nome], frase)
      const audio = new Audio(url)
      audio.onended = () => URL.revokeObjectURL(url)
      await audio.play()
    } catch (e) {
      erroreAnteprima = e instanceof Error ? e.message : String(e)
    } finally {
      inAscolto = null
    }
  }
</script>

<div class="griglia">
  <label class="campo">
    <span>Personaggio da studiare</span>
    <select bind:value={personaggio}>
      {#each analisi.personaggi as nome (nome)}
        <option value={nome}>{nome} ({analisi.battute_per_personaggio[nome]} battute)</option>
      {/each}
    </select>
  </label>

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

<details>
  <summary>Personaggi da ascoltare <span class="tenue">({altri.length - esclusi.filter((n) => altri.includes(n)).length}/{altri.length})</span></summary>
  <p class="tenue">Le battute dei personaggi esclusi vengono saltate del tutto.</p>
  <div class="caselle">
    {#each altri as nome (nome)}
      <label class="scelta">
        <input
          type="checkbox"
          checked={!esclusi.includes(nome)}
          onchange={(e) => alternaEscluso(nome, e.currentTarget.checked)}
        />
        <span>{nome}</span>
      </label>
    {/each}
  </div>
</details>

<details>
  <summary>
    Scene <span class="tenue">({scene.filter((i) => sceneMie.includes(i)).length}/{sceneMie.length} in cui parla {personaggio})</span>
  </summary>
  <div class="azioni">
    <button type="button" class="link" onclick={() => (scene = analisi.scene.map((s) => s.indice))}>Tutte</button>
    <button type="button" class="link" onclick={() => (scene = [])}>Nessuna</button>
  </div>
  <div class="caselle colonna">
    {#each analisi.scene as s (s.indice)}
      {@const parla = sceneMie.includes(s.indice)}
      <label class="scelta" class:spenta={!parla}>
        <input
          type="checkbox"
          disabled={!parla}
          checked={parla && scene.includes(s.indice)}
          onchange={(e) => alternaScena(s.indice, e.currentTarget.checked)}
        />
        <span>
          {s.titolo ?? `Scena ${s.indice + 1}`}
          <span class="tenue">· {s.battute} battute{parla ? '' : ` · ${personaggio} non parla`}</span>
        </span>
      </label>
    {/each}
  </div>
</details>

<details>
  <summary>Voci</summary>
  <p class="tenue">
    Assegnate in automatico senza conoscere il genere dei personaggi: controllale con ▶.
  </p>
  <label class="scelta">
    <input type="checkbox" bind:checked={generali.leggi_didascalie} />
    <span>Leggi anche le didascalie (voce del narratore)</span>
  </label>
  <div class="voci">
    {#each conVoce as nome (nome)}
      {#if voci[nome]}
        <span class="nome">{nome === NARRATORE ? 'Narratore' : nome}</span>
        <select bind:value={voci[nome].nome} aria-label="Voce di {nome}">
          {#each elencoVoci as v (v.nome)}
            <option value={v.nome}>
              {v.nome.replace(/^[a-z]{2}-[A-Z]{2}-/, '').replace(/Neural$/, '')} ({v.genere === 'Male' ? 'M' : 'F'})
            </option>
          {/each}
        </select>
        <select bind:value={voci[nome].tono} aria-label="Tono di {nome}">
          {#each TONI as tono (tono)}
            <option value={tono}>tono {tono.replace('Hz', '')}</option>
          {/each}
        </select>
        <button
          type="button"
          class="secondario icona"
          onclick={() => ascolta(nome)}
          disabled={inAscolto !== null}
          aria-label="Ascolta la voce di {nome}"
        >
          {inAscolto === nome ? '…' : '▶'}
        </button>
      {/if}
    {/each}
  </div>
  {#if erroreAnteprima}
    <p class="testo-errore">{erroreAnteprima}</p>
  {/if}
</details>

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

  .campo > span,
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

  .scelta.spenta {
    opacity: 0.55;
    cursor: default;
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

  details {
    border-top: 1px solid var(--bordo);
    padding: 0.75rem 0;
  }

  summary {
    cursor: pointer;
    font-weight: 600;
  }

  .caselle {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1.25rem;
    margin-top: 0.5rem;
  }

  .caselle.colonna {
    flex-direction: column;
    flex-wrap: nowrap;
    max-height: 18rem;
    overflow: auto;
  }

  .azioni {
    display: flex;
    gap: 1rem;
    margin-top: 0.5rem;
  }

  .voci {
    display: grid;
    grid-template-columns: minmax(6rem, auto) minmax(0, 1fr) auto auto;
    gap: 0.5rem;
    align-items: center;
    margin-top: 0.75rem;
  }

  .voci .nome {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .icona {
    width: 2.4rem;
    padding-inline: 0;
  }

  @media (max-width: 30rem) {
    .voci {
      grid-template-columns: minmax(0, 1fr) auto auto;
    }

    .voci .nome {
      grid-column: 1 / -1;
      margin-top: 0.5rem;
    }
  }
</style>
