import os, re, json, unicodedata
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

# ---------- Pfade ----------
DEFAULT_SEED = "seeds/scout_temp.sql"
TABLE_MAPPING_PATH = "data/table_mapping.json"

# ---------- OpenAI Client ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Utils ----------
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9_]+", "_", s.lower()).strip("_")

def load_seed(seed_path: str) -> str:
    return Path(seed_path).read_text(encoding="utf-8", errors="ignore")

def load_table_mapping(path: str) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def extract_iname(seed_sql: str) -> str:
    m = re.search(r"i_name IN \('(\d{8})'\)", seed_sql, flags=re.I)
    if not m:
        raise RuntimeError("I_NAME nicht gefunden.")
    return m.group(1)

# ---------- Patch-Funktionen ----------
def patch_ifield(seed_sql: str, iname: str, fields: List[str]) -> str:
    """Fügt IFIELD-Zeilen ein für die gewünschten Felder."""
    insert_pos = seed_sql.find("INSERT INTO L2001.ifield")
    if insert_pos == -1:
        raise RuntimeError("IFIELD-Block nicht gefunden")
    lines = []
    for i, f in enumerate(fields):
        tbl, col = f.split(".")
        lines.append(f"\"{iname}\",\"{tbl}\",\"{tbl}\",\"{col}\",{i},\"{col}\",,,,,\"{col}\",,,")
    new_block = "\n".join(lines) + "\n"
    return seed_sql + "\n" + new_block

def patch_ibeziehung(seed_sql: str, iname: str, joins: List[List[str]]) -> str:
    """Fügt IBEZIEHUNG-Zeilen ein für die Join-Beziehungen."""
    insert_pos = seed_sql.find("INSERT INTO L2001.ibeziehung")
    if insert_pos == -1:
        raise RuntimeError("IBEZIEHUNG-Block nicht gefunden")
    lines = []
    for j in joins:
        src_tbl, src_col, tgt_tbl, tgt_col = j
        lines.append(f"\"{iname}\",\"{src_tbl}\",\"{src_tbl}\",\"{src_col}\",\"{tgt_tbl}\",\"{tgt_tbl}\",\"{tgt_col}\",,1,")
    new_block = "\n".join(lines) + "\n"
    return seed_sql + "\n" + new_block

def patch_ibedingung(seed_sql: str, iname: str, conditions: List[str]) -> str:
    """Fügt IBEDINGUNG-Zeilen ein für WHERE-Bedingungen."""
    insert_pos = seed_sql.find("INSERT INTO L2001.ibedingung")
    if insert_pos == -1:
        raise RuntimeError("IBEDINGUNG-Block nicht gefunden")
    lines = []
    for i, cond in enumerate(conditions):
        lines.append(f"\"{iname}\",\"PGRDAT\",\"PGRDAT\",\"\",{i},,,0,0,,,,'',,'{cond}'")
    new_block = "\n".join(lines) + "\n"
    return seed_sql + "\n" + new_block

# ---------- Hauptfunktion ----------
def parse_user_request(user_input: str, seed_path: str = DEFAULT_SEED) -> str:
    seed = load_seed(seed_path)
    table_map = load_table_mapping(TABLE_MAPPING_PATH)
    iname = extract_iname(seed)

    # Fallback: Basisfelder
    selected_fields = [table_map["PGRDAT"]["fields"]["mandant"],
                       table_map["PGRDAT"]["fields"]["abrechnungskreis"],
                       table_map["PGRDAT"]["fields"]["personalnummer"]]

    joins_needed = []
    conditions = []

    # Erkennung über Keywords im User-Input
    if "resturlaub" in _norm(user_input):
        selected_fields.append(table_map["SALDEN"]["fields"]["resturlaub"])
        joins_needed.extend(table_map["SALDEN"]["join_keys"])
    if "fehlzeit" in _norm(user_input):
        selected_fields.append(table_map["ZEITENKAL"]["fields"]["fehlzeitencode"])
        selected_fields.append(table_map["ZEITENKAL"]["fields"]["beginn_fehlzeit"])
        selected_fields.append(table_map["ZEITENKAL"]["fields"]["ende_fehlzeit"])
        joins_needed.extend(table_map["ZEITENKAL"]["join_keys"])
    if "vertrag" in _norm(user_input):
        selected_fields.append(table_map["VERTRAG"]["fields"]["vertragsbeginn"])
        selected_fields.append(table_map["VERTRAG"]["fields"]["vertragsende"])
        joins_needed.extend(table_map["VERTRAG"]["join_keys"])
    if "ak=70" in _norm(user_input):
        conditions.append("PGRDAT.AK = '70'")
    if "sv_tage=0" in _norm(user_input):
        conditions.append("COALESCE(ZEITENKAL.SV_TAGE,0) = 0")

    out = patch_ifield(seed, iname, selected_fields)
    out = patch_ibeziehung(out, iname, joins_needed)
    out = patch_ibedingung(out, iname, conditions)

    return out
