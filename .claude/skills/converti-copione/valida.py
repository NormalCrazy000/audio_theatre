"""
Controlla un file .copione.txt: stampa un riepilogo e gli errori.
Esce con codice 1 se ci sono errori.

Uso (dalla radice del progetto):
    uv run --project backend python .claude/skills/converti-copione/valida.py FILE.copione.txt
"""

import sys
from pathlib import Path

from copione_audio.copione import analizza

if len(sys.argv) != 2:
    sys.exit(__doc__)
copione, errori = analizza(Path(sys.argv[1]).read_text(encoding="utf-8"))

print(f"Titolo: {copione.titolo}  Lingua: {copione.lingua}")
print(f"Scene: {len(copione.scene)}  Battute: {len(copione.battute)}")
for nome, numero in copione.battute_per_personaggio().items():
    print(f"  {nome}: {numero}")
for i, scena in enumerate(copione.scene, 1):
    print(f"  scena {i} ({scena.titolo}): {len(scena.battute)} battute")

if errori:
    print(f"\n{len(errori)} errori:", file=sys.stderr)
    for errore in errori:
        print(f"  {errore}", file=sys.stderr)
    sys.exit(1)
print("\nNessun errore.")
