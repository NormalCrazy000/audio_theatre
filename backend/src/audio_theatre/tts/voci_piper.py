"""
Le voci Piper nella cartella delle voci: catalogo con i link, elenco delle
installate, aggiunta ed eliminazione dei file.

L'app non scarica nulla: i file si scaricano a mano dai link del catalogo e si
aggiungono trascinandoli nell'interfaccia o copiandoli nella cartella.
"""

import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

# piper.py → tts → audio_theatre → src → backend → radice del progetto
VOCI_PREDEFINITE = Path(__file__).parents[4] / "voci"

REPOSITORY = "https://huggingface.co/rhasspy/piper-voices"
"""Il repository ufficiale delle voci Piper, con tutte le lingue."""

# I modelli non dichiarano il genere: quello delle voci note è scritto qui.
GENERI = {"paola": "Female", "riccardo": "Male", "serena": "Female"}

# Nome di una voce: lingua_REGIONE-nome-qualità, es. "it_IT-paola-medium".
NOME_VOCE = r"[a-z]{2,3}_[A-Z]{2}-[A-Za-z0-9_]+-(?:x_low|low|medium|high)"
_FILE_VOCE = re.compile(rf"(?P<nome>{NOME_VOCE})(?P<estensione>\.onnx(?:\.json)?)")

# Un modello ONNX è un messaggio protobuf che inizia con il campo
# `ir_version` (numero 1, tipo varint): il primo byte è 0x08.
_INIZIO_ONNX = b"\x08"


def cartella_predefinita() -> Path:
    """`$AUDIO_THEATRE_PIPER`, oppure la cartella `voci/` nella radice del progetto."""
    return Path(os.environ.get("AUDIO_THEATRE_PIPER", VOCI_PREDEFINITE))


@dataclass(frozen=True)
class VoceCatalogo:
    """Una voce da scaricare a mano."""

    nome: str
    genere: str
    mb: int
    dati: str
    """Da quali registrazioni è stata addestrata (utile per la licenza)."""

    @property
    def _percorso(self) -> str:
        lingua_regione, voce, qualita = self.nome.split("-", 2)
        return f"{lingua_regione.split('_')[0]}/{lingua_regione}/{voce}/{qualita}"

    @property
    def qualita(self) -> str:
        return self.nome.rsplit("-", 1)[1]

    @property
    def link_modello(self) -> str:
        return f"{REPOSITORY}/resolve/main/{self._percorso}/{self.nome}.onnx?download=true"

    @property
    def link_configurazione(self) -> str:
        return f"{REPOSITORY}/resolve/main/{self._percorso}/{self.nome}.onnx.json?download=true"

    @property
    def pagina(self) -> str:
        """La cartella della voce, con la scheda (MODEL_CARD) e la licenza dei dati."""
        return f"{REPOSITORY}/tree/main/{self._percorso}"


CATALOGO = [
    VoceCatalogo("it_IT-paola-medium", "Female", 64, "dataset CC0, partendo dalla voce inglese lessac (licenza di ricerca)"),
    VoceCatalogo("it_IT-riccardo-x_low", "Male", 29, "dataset M-AILABS"),
    VoceCatalogo("it_IT-serena-medium", "Female", 64, "dataset sintetico CC-BY-4.0"),
    VoceCatalogo("it_IT-serena-high", "Female", 115, "dataset sintetico CC-BY-4.0"),
]
"""Le voci italiane disponibili nel repository ufficiale."""


@dataclass(frozen=True)
class VoceInstallata:
    """
    Una voce trovata nella cartella. È utilizzabile solo se ha sia il modello
    sia una configurazione valida.
    """

    nome: str
    lingua: str
    """Es. "it-IT", ricavata dal nome."""
    genere: str
    modello: bool
    """Se c'è il file `.onnx`."""
    configurazione: bool
    """Se c'è il file `.onnx.json` ed è leggibile."""
    mb: float

    @property
    def completa(self) -> bool:
        return self.modello and self.configurazione


def _configurazione_valida(percorso: Path) -> bool:
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
        return isinstance(dati["language"]["code"], str) and "phoneme_id_map" in dati
    except (OSError, ValueError, KeyError, TypeError):
        return False


def voci_installate(cartella: Path) -> list[VoceInstallata]:
    """Le voci nella cartella, anche incomplete (un solo file dei due)."""
    nomi = sorted(
        {trovato["nome"] for f in cartella.glob("*.onnx*") if (trovato := _FILE_VOCE.fullmatch(f.name))}
    )
    voci = []
    for nome in nomi:
        modello = cartella / f"{nome}.onnx"
        lingua_regione, speaker, _ = nome.split("-", 2)
        voci.append(
            VoceInstallata(
                nome=nome,
                lingua=lingua_regione.replace("_", "-"),
                genere=GENERI.get(speaker, "Unknown"),
                modello=modello.is_file(),
                configurazione=_configurazione_valida(cartella / f"{nome}.onnx.json"),
                mb=round(modello.stat().st_size / 1e6, 1) if modello.is_file() else 0,
            )
        )
    return voci


def aggiungi_file(cartella: Path, nome_file: str, contenuto: BinaryIO) -> str:
    """
    Controlla un file di una voce e lo salva nella cartella, sostituendo
    quello con lo stesso nome. La scrittura è atomica: un errore a metà non
    lascia file incompleti.

    :param nome_file: Il nome originale, es. "it_IT-paola-medium.onnx".
    :return: Il nome della voce.
    :raises ValueError: Se il nome o il contenuto non sono quelli di una voce Piper.
    """
    trovato = _FILE_VOCE.fullmatch(Path(nome_file).name)
    if not trovato:
        raise ValueError(
            "nome non riconosciuto: servono i file come scaricati, "
            "es. it_IT-paola-medium.onnx e it_IT-paola-medium.onnx.json"
        )
    nome, estensione = trovato["nome"], trovato["estensione"]
    cartella.mkdir(parents=True, exist_ok=True)
    descrittore, temporaneo = tempfile.mkstemp(dir=cartella, prefix=".caricamento-")
    temporaneo = Path(temporaneo)
    try:
        with os.fdopen(descrittore, "wb") as destinazione:
            shutil.copyfileobj(contenuto, destinazione, 1024 * 1024)
        if estensione == ".onnx.json":
            if not _configurazione_valida(temporaneo):
                raise ValueError("non è la configurazione di una voce Piper (JSON non valido)")
        else:
            with temporaneo.open("rb") as file:
                if file.read(1) != _INIZIO_ONNX:
                    raise ValueError("non sembra un modello ONNX")
        temporaneo.replace(cartella / f"{nome}{estensione}")
    finally:
        temporaneo.unlink(missing_ok=True)
    return nome


def elimina_voce(cartella: Path, nome: str) -> None:
    """
    Cancella i file di una voce.

    :raises ValueError: Se il nome non è valido o la voce non c'è.
    """
    if not re.fullmatch(NOME_VOCE, nome):
        raise ValueError(f"nome di voce non valido: {nome}")
    file = [cartella / f"{nome}.onnx", cartella / f"{nome}.onnx.json"]
    if not any(f.exists() for f in file):
        raise ValueError(f"voce non installata: {nome}")
    for f in file:
        f.unlink(missing_ok=True)
