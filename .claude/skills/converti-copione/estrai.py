"""
Estrae il testo grezzo da un PDF e lo stampa.

Uso (dalla radice del progetto):
    uv run --project backend python .claude/skills/converti-copione/estrai.py FILE.pdf
"""

import sys
from pathlib import Path

from audio_theatre.conversione.pdf import estrai_testo

if len(sys.argv) != 2:
    sys.exit(__doc__)
print(estrai_testo(Path(sys.argv[1])))
