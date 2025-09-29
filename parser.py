# parser.py – Scout-konformer Patch
import os, re, json, unicodedata
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

# ---------- Pfade ----------
DEFAULT_SEED = "seeds/scout_temp.sql"
MAPPING_PATH = "data/felder_mapping.json"

# ---------- OpenAI Client ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Hilfsfunktionen ----------
def _norm(s: str) -> str:
    """Kleinbuchstaben, Diakritik entfernen."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", s.lower()).strip("_")

def load_seed(seed_path: str) -> str:
    return Path(seed_path).read_text(encoding="utf-8", errors="ignore")

def load_mapping(path: str) -> Dict:
    m = json.loads(Path(path).read_text(encoding="utf-8"))
    terms = m.get("terms", {})
    norm_terms = { _norm(k): v for k, v in terms.items() }
    m["terms_norm"] = norm_terms
    return m

def extract_iname(seed_sql: str) -> str:
    m = re.search(r"i_name IN \('(\d{8})'\)", seed_sql, flags=re.I)
    if not m:
        raise RuntimeError("I_NAME nicht gefunden.")
    return m.group(1)

# ---------- Patch-Funktionen ----------
def patch_ifield(seed_sql: str, iname: str, fields: List[str]) -> str:
    """Patcht IFIELD-Zeilen: Spaltenauswahl."""
    # Alle alten IFIELDs für dieses iname löschen
    seed_sql = re.sub(rf'"{iname}".+?IFIELD.+?\n', "", seed_sql, flags=re.I)
    # Neue IFIELD-Zeilen anhängen
    insert_pos = seed_sql.find("INSERT INTO L2001.ifield")
    if insert_pos == -1:
        raise RuntimeError("IFIELD-Block nicht gefunden")
    lines = []
    for i, f in enumerate(fields):
        tbl, col = f.split(".")
        lines.append(f"\"{iname}\",\"{tbl}\",\"{tbl}\",\"{col}\",{i},\"{col}\",,,,,\"{col}\",,,")
    new_block = "\n".join(lines) + "\n"
    seed_sql = seed_sql[:insert_pos] + seed_sql[insert_pos:] + new_block
    return seed_sql

def patch_ibedingung(seed_sql: str, iname: str, conditions: List[str]) -> str:
    """Patcht IBEDINGUNG-Zeilen: WHERE-Bedingungen."""
    # Alte Bedingungen löschen
    seed_sql = re.sub(rf'"{iname}".+?IBEDINGUNG.+?\n', "", seed_sql, flags=re.I)
    insert_pos = seed_sql.find("INSERT INTO L2001.ibedingung")
    if insert_pos == -1:
        raise RuntimeError("IBEDINGUNG-Block nicht gefunden")
    lines = []
    for i, cond in enumerate(conditions):
        # Sehr vereinfachte Darstellung: Ausdruck in I_expression
        lines.append(f"\"{iname}\",\"PGRDAT\",\"PGRDAT\",\"\",{i},,,0,0,,,,'',,'{cond}'")
    new_block = "\n".join(lines) + "\n"
    seed_sql = seed_sql[:insert_pos] + seed_sql[insert_pos:] + new_block
    return seed_sql

# ---------- Hauptfunktion ----------
def parse_user_request(user_input: str, seed_path: str = DEFAULT_SEED) -> str:
    seed = load_seed(seed_path)
    mapping = load_mapping(MAPPING_PATH)
    iname = extract_iname(seed)

    # Fallback Felder
    fields = ["PGRDAT.MAN","PGRDAT.AK","PGRDAT.PNR","PGRDAT.NANAME","PGRDAT.VORNAME"]

    # Einfache Bedingungserkennung
    conditions = []
    if "ak=70" in _norm(user_input):
        conditions.append("PGRDAT.AK = '70'")
    if "sv-tage=0" in _norm(user_input):
        conditions.append("COALESCE(SALDEN.SV_TAGE,0) = 0")

    # Seed patchen
    out = patch_ifield(seed, iname, fields)
    out = patch_ibedingung(out, iname, conditions)

    return out
