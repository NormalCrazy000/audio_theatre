<script lang="ts">
  import { anteprima, NARRATORE, type Analisi, type InfoVoce, type Motore, type Voce } from './api'

  type Props = {
    analisi: Analisi
    personaggio: string
    /** Personaggi da non far sentire. */
    esclusi: string[]
    /** Indici delle scene scelte. */
    scene: number[]
    voci: Record<string, Voce>
    elencoVoci: InfoVoce[]
    motore: Motore
    /** Se si leggono le didascalie: allora serve anche la voce del narratore. */
    leggiDidascalie: boolean
  }

  let {
    analisi,
    personaggio = $bindable(),
    esclusi = $bindable(),
    scene = $bindable(),
    voci = $bindable(),
    elencoVoci,
    motore,
    leggiDidascalie,
  }: Props = $props()

  const TONI = ['-24Hz', '-12Hz', '+0Hz', '+12Hz', '+24Hz']

  const altri = $derived(analisi.personaggi.filter((n) => n !== personaggio))
  const sceneMie = $derived(
    analisi.scene.filter((s) => s.personaggi.includes(personaggio)).map((s) => s.indice),
  )
  const conVoce = $derived([
    ...analisi.personaggi,
    ...(leggiDidascalie ? [NARRATORE] : []),
  ])

  let inAscolto = $state<string | null>(null)
  let erroreAnteprima = $state<string | null>(null)

  /** "it-IT-ElsaNeural" → "Elsa"; "it_IT-paola-medium" → "paola, medium". */
  function nomeVoce(v: InfoVoce): string {
    const nome = v.nome
      .replace(/^[a-z]{2,3}[-_][A-Z]{2}-/, '')
      .replace(/Neural$/, '')
      .replace(/-([a-z_]+)$/, ', $1')
    const genere = { Male: 'M', Female: 'F' }[v.genere]
    return genere ? `${nome} (${genere})` : nome
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
      const url = await anteprima(voci[nome], frase, motore)
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

<label class="campo">
  <span>Personaggio da studiare</span>
  <select bind:value={personaggio}>
    {#each analisi.personaggi as nome (nome)}
      <option value={nome}>{nome} ({analisi.battute_per_personaggio[nome]} battute)</option>
    {/each}
  </select>
</label>

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
    Voci {motore === 'piper' ? 'offline' : 'online'} (si cambia nelle Impostazioni), assegnate in automatico
    senza conoscere il genere dei personaggi: controllale con ▶.
  </p>
  {#if Object.keys(voci).length === 0}
    <p class="testo-errore">Nessuna voce disponibile: controlla la sintesi vocale nelle Impostazioni.</p>
  {/if}
  <div class="voci">
    {#each conVoce as nome (nome)}
      {#if voci[nome]}
        <span class="nome">{nome === NARRATORE ? 'Narratore' : nome}</span>
        <select bind:value={voci[nome].nome} aria-label="Voce di {nome}">
          {#each elencoVoci as v (v.nome)}
            <option value={v.nome}>
              {nomeVoce(v)}
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
  .campo {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    max-width: 24rem;
    margin-bottom: 1rem;
  }

  .campo > span {
    font-weight: 600;
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
