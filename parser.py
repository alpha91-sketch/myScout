import os
import re
import json
from pathlib import Path
from openai import OpenAI

# ---------- Config ----------
DEFAULT_SEED = "seeds/scout_temp.sql"
MAPPING_PATH = "data/felder_mapping.json"

# OpenAI Client (API-Key in Streamlit-Cloud Secrets oder Env hinterlegen)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Helpers ----------
def load_seed(seed_path: str) -> str:
    return Path(seed_path).read_text(encoding="utf-8", errors="ignore")

def load_mapping(path: str) -> dict:
    if Path(path).exists():
        return json.loads(Path(path).read_text(encoding="utf-8"))
    # Minimaler Fallback falls Datei fehlt
    return {
        "terms": {
            "mandant": "PGRDAT.MAN",
            "ak": "PGRDAT.AK",
            "pnr": "PGRDAT.PNR",
            "name": "PGRDAT.NANAME",
            "vorname": "PGRDAT.VORNAME",
            "vertragsbeginn": "VERTRAG.VERBEGIN",
            "vertragsende": "VERTRAG.VERENDE",
            "sv_tage": "SALDEN.SV_TAGE",
            "fehlzeitencode": "ZEITENKAL.FEHLKZ",
            "fehlzeit_von": "ZEITENKAL.VON",
            "fehlzeit_bis": "ZEITENKAL.BIS"
        },
        "join_rules": {
            "VERTRAG": "JOIN VERTRAG ON PGRDAT.MAN = VERTRAG.MAN AND PGRDAT.AK = VERTRAG.AK AND PGRDAT.PNR = VERTRAG.PNR",
            "ZEITENKAL": "LEFT JOIN ZEITENKAL ON PGRDAT.MAN = ZEITENKAL.MAN AND PGRDAT.AK = ZEITENKAL.AK AND PGRDAT.PNR = ZEITENKAL.PNR",
            "SALDEN":   "LEFT JOIN SALDEN   ON PGRDAT.MAN = SALDEN.MAN   AND PGRDAT.AK = SALDEN.AK   AND PGRDAT.PNR = SALDEN.PNR"
        }
    }

def extract_iname(seed_text: str) -> str:
    m = re.search(r"i_name IN \('(\d{8})'", seed_text, flags=re.I)
    if m: return m.group(1)
    # Fallback: erste 8-stellige Nummer
    m = re.search(r'"(\d{8})"', seed_text)
    if m: return m.group(1)
    raise RuntimeError("I_NAME (8-stellig) nicht im Seed gefunden.")

def patch_title(seed_text: str, new_title: str) -> str:
    # Ersetze erste Titelstelle in IMEMBER
    return re.sub(r'"(\d{8})","[^"]+"', f'"\\1","{new_title}"', seed_text, count=1)

def patch_select(seed_text: str, select_fields: list) -> str:
    select_block = ", ".join(select_fields) if select_fields else "PGRDAT.MAN, PGRDAT.AK, PGRDAT.PNR"
    return re.sub(r"SELECT\s+(.+?)\s+FROM", f"SELECT {select_block} FROM", seed_text, flags=re.S | re.I)

def insert_joins(seed_text: str, join_lines: list) -> str:
    if not join_lines: return seed_text
    join_text = "\n    " + "\n    ".join(join_lines)
    # Nach der VERTRAG-Join-Zeile einfügen (erste Treffer)
    return re.sub(r"(JOIN\s+VERTRAG[^\n]*\n)", r"\1" + join_text + "\n", seed_text, count=1, flags=re.I)

def patch_where(seed_text: str, extra_conds: list) -> str:
    if not extra_conds: return seed_text
    add = " AND ".join([f"({c})" for c in extra_conds])
    # WHERE existiert?
    m = re.search(r"\bWHERE\b\s+(.+?)(\bGROUP BY\b|\bORDER BY\b|$)", seed_text, flags=re.S | re.I)
    if m:
        old_expr = m.group(1).strip()
        new_expr = f"({old_expr}) AND {add}"
        start, end = m.start(1), m.end(1)
        return seed_text[:start] + new_expr + seed_text[end:]
    else:
        # WHERE neu zwischen FROM/JOINs und GROUP/ORDER/Ende einsetzen
        m2 = re.search(r"(FROM.+?)(\bGROUP BY\b|\bORDER BY\b|$)", seed_text, flags=re.S | re.I)
        if not m2: 
            # worst-case: einfach anhängen
            return seed_text + "\nWHERE " + add + "\n"
        insert_pos = m2.end(1)
        return seed_text[:insert_pos] + "\nWHERE " + add + "\n" + seed_text[insert_pos:]

# ---------- LLM: Freitext -> Plan-JSON ----------
def plan_from_llm(user_input: str, mapping: dict) -> dict:
    terms = mapping.get("terms", {})
    join_rules = mapping.get("join_rules", {})
    system = (
        "Du bist ein Assistent für LOGA Scout. "
        "Nutze nur Felder aus dem gegebenen Mapping. "
        "Antworte ausschließlich mit JSON."
    )
    user = f"""
Anforderung: {user_input}

Verfügbare Felder (Synonym -> Feld):
{json.dumps(terms, ensure_ascii=False, indent=2)}
Erzeuge ein JSON der Form:
{{
  "fields": ["PGRDAT.NANAME","PGRDAT.VORNAME","VERTRAG.VERBEGIN"],
  "conditions": ["PGRDAT.AK = '70'", "SALDEN.SV_TAGE = 0", "VERTRAG.VERBEGIN >= '2024-01-01'"],
  "tables_extra": ["ZEITENKAL","SALDEN"],
  "group_by": [],
  "order_by": ""
}}
- fields: nur vollqualifizierte Felder (Werte des Mappings verwenden)
- conditions: gültige SQL-Ausdrücke mit den vollqualifizierten Feldern
- tables_extra: zusätzliche Tabellen außer PGRDAT/VERTRAG, falls benötigt
- group_by: optional Liste vollqualifizierter Felder
- order_by: optional String (z.B. "1,2" oder "PGRDAT.NANAME")
Nur JSON, kein Fließtext.
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=0
    )
    raw = resp.choices[0].message.content.strip()
    try:
        plan = json.loads(raw)
    except Exception:
        # sehr defensiver Fallback
        plan = {
            "fields": ["PGRDAT.MAN","PGRDAT.AK","PGRDAT.PNR","PGRDAT.NANAME","PGRDAT.VORNAME","VERTRAG.VERBEGIN","VERTRAG.VERENDE"],
            "conditions": [],
            "tables_extra": [],
            "group_by": [],
            "order_by": ""
        }
    # Minimal absichern
    plan.setdefault("fields", [])
    plan.setdefault("conditions", [])
    plan.setdefault("tables_extra", [])
    plan.setdefault("group_by", [])
    plan.setdefault("order_by", "")
    return plan

# ---------- Hauptfunktion ----------
def parse_user_request(user_input: str, seed_path: str = DEFAULT_SEED) -> str:
    seed = load_seed(seed_path)
    iname = extract_iname(seed)
    mapping = load_mapping(MAPPING_PATH)

    # 1) LLM-Plan holen
    plan = plan_from_llm(user_input, mapping)

    # 2) SELECT patchen
    out = patch_title(seed, re.sub(r"[^A-Za-z0-9]+","_", user_input[:40]))
    out = patch_select(out, plan["fields"])

    # 3) JOINS einfügen (nur zusätzliche)
    join_rules = mapping.get("join_rules", {})
    extra = [t for t in plan["tables_extra"] if t in join_rules and t.upper() in ["ZEITENKAL","SALDEN"]]
    join_lines = [join_rules[t] for t in extra]
    out = insert_joins(out, join_lines)

    # 4) WHERE erweitern
    out = patch_where(out, plan["conditions"])
    # 5) GROUP/ORDER optional (nur ersetzen, wenn vorhanden)
    if plan["group_by"]:
        gb = "GROUP BY " + ", ".join(plan["group_by
