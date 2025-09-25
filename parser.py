# parser.py
import os, re, json, unicodedata
from pathlib import Path
from typing import Dict, List
from openai import OpenAI

# ---------- Pfade ----------
DEFAULT_SEED = "seeds/scout_temp.sql"
MAPPING_PATH = "data/felder_mapping.json"

# ---------- OpenAI Client ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Utils ----------
def _norm(s: str) -> str:
    """kleine Normalisierung: klein, Diakritik raus, nur a-z0-9_"""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", s.lower()).strip("_")
    return s

def load_seed(seed_path: str) -> str:
    return Path(seed_path).read_text(encoding="utf-8", errors="ignore")

def load_mapping(path: str) -> Dict:
    m = json.loads(Path(path).read_text(encoding="utf-8"))
    # zusätzlich: normalisierte Term-Keys
    terms = m.get("terms", {})
    norm_terms = { _norm(k): v for k, v in terms.items() }
    m["terms_norm"] = norm_terms
    return m

def extract_iname(seed_sql: str) -> str:
    m = re.search(r"i_name\s+IN\s+\('(\d{8})'\)", seed_sql, flags=re.I)
    if not m:
        raise RuntimeError("I_NAME (member) nicht gefunden.")
    return m.group(1)

def patch_title(seed_sql: str, new_title: str) -> str:
    iname = extract_iname(seed_sql)
    return re.sub(rf'"{re.escape(iname)}","[^"]+"',
                  f'"{iname}","{new_title}"', seed_sql, count=1)

def _split_at_select(seed_sql: str):
    m = re.search(r"\bSELECT\b", seed_sql, flags=re.I)
    if not m:
        raise RuntimeError("SELECT-Block im Seed nicht gefunden.")
    return seed_sql[:m.start()], seed_sql[m.start():]

def patch_select_where_joins(seed_sql: str,
                             select_cols: List[str],
                             extra_where: str,
                             extra_joins: List[str]) -> str:
    head, block = _split_at_select(seed_sql)

    # SELECT-Spalten ersetzen (nur im Query-Block)
    block = re.sub(r"SELECT\s+(.+?)\s+FROM",
                   "SELECT " + ", ".join(select_cols) + " FROM",
                   block, flags=re.S | re.I)

    # Joins nach FROM einfügen (nur im Query-Block)
    if extra_joins:
        m = re.search(r"(FROM\s+.+?)(\nWHERE|\nGROUP BY|\nORDER BY|$)", block, flags=re.S | re.I)
        if m:
            before = m.group(1)
            after = block[m.end(1):]
            join_txt = "\n    " + "\n    ".join(extra_joins)
            block = before + join_txt + after

    # WHERE zusammenführen/ergänzen (nur im Query-Block)
    extra_where = extra_where.strip()
    if extra_where:
        if re.search(r"\bWHERE\b", block, flags=re.I):
            block = re.sub(r"WHERE\s+(.+?)(GROUP BY|ORDER BY|$)",
                           lambda m: "WHERE (" + m.group(1).strip() + ") AND (" + extra_where + ") " + m.group(2),
                           block, flags=re.S | re.I)
        else:
            # erstes Zeilenende nach FROM/JOINS suchen
            m2 = re.search(r"(FROM[\s\S]+?)(GROUP BY|ORDER BY|$)", block, flags=re.I)
            if m2:
                prefix = m2.group(1)
                suffix = block[m2.end(1):]
                block = prefix + "\nWHERE " + extra_where + "\n" + suffix
            else:
                block += "\nWHERE " + extra_where + "\n"

    return head + block

# ---------- LLM-Plan ----------
SYSTEM_PROMPT = """Du bist ein Parser, der natürliche Fragen in einen Plan für LOGA/SCOUT-SQL übersetzt.
Antworte NUR als JSON mit Feldern:
- fields: Liste SQL-Spalten (z.B. "PGRDAT.MAN", "VERTRAG.VERBEGIN")
- conditions: eine einzige WHERE-Bedingung als SQL-Text (ohne 'WHERE'), ODER "" wenn nicht nötig
- tables_extra: optionale Liste zusätzlicher Tabellen: ["ZEITENKAL","SALDEN"] wenn gebraucht
- group_by: Liste Positionszahlen als Strings (z.B. ["1","2"])
- order_by: Text wie "1,2"
Verwende NUR bekannte Spaltennamen aus dem Mapping.
"""

def plan_from_llm(user_input: str, mapping: Dict) -> Dict:
    # Begriffe im Text heuristisch gegen terms_norm mappen, falls LLM nicht erreichbar
    terms_norm = mapping.get("terms_norm", {})
    guessed_fields = []
    for k_norm, col in terms_norm.items():
        if re.search(r"\b" + re.escape(k_norm) + r"\b", _norm(user_input)):
            guessed_fields.append(col)
    # Feldfallback
    if not guessed_fields:
        guessed_fields = ["PGRDAT.MAN","PGRDAT.AK","PGRDAT.PNR","PGRDAT.NANAME","PGRDAT.VORNAME"]

    # LLM-Versuch
    try:
        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps({"mapping_terms": list(mapping["terms"].keys()),
                                                    "user_request": user_input}, ensure_ascii=False)}
        ]
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
            temperature=0.1,
        )
        raw = resp.choices[0].message.content.strip()
        # JSON extrahieren
        json_txt = raw[raw.find("{"): raw.rfind("}")+1]
        plan = json.loads(json_txt)
    except Exception:
        # Solider Fallback
        cond = []
        # einfache Muster
        m_ak = re.search(r"\bak\s*=\s*'?(\d+)'?", user_input, flags=re.I)
        if m_ak: cond.append(f"PGRDAT.AK = '{m_ak.group(1)}'")
        if "sv-tage=0" in _norm(user_input) or "sv_tage=0" in _norm(user_input):
            cond.append("COALESCE(SALDEN.SV_TAGE,0) = 0")
        condition = " AND ".join(cond)

        tables_extra = []
        if "sv" in _norm(user_input): tables_extra.append("SALDEN")
        if "fehlzeit" in _norm(user_input) or "abgelaufen" in _norm(user_input):
            tables_extra.append("ZEITENKAL")

        plan = {
            "fields": guessed_fields,
            "conditions": condition,
            "tables_extra": tables_extra,
            "group_by": [],
            "order_by": ""
        }

    # Defaults absichern
    plan.setdefault("fields", guessed_fields)
    plan.setdefault("conditions", "")
    plan.setdefault("tables_extra", [])
    plan.setdefault("group_by", [])
    plan.setdefault("order_by", "")
    return plan

# ---------- Hauptfunktion ----------
def parse_user_request(user_input: str, seed_path: str = DEFAULT_SEED) -> str:
    seed = load_seed(seed_path)
    mapping = load_mapping(MAPPING_PATH)

    # 1) Plan
    plan = plan_from_llm(user_input, mapping)

    # 2) SELECT-Felder
    fields = plan["fields"]
    if not fields:
        fields = ["PGRDAT.MAN","PGRDAT.AK","PGRDAT.PNR"]
    select_cols = fields

    # 3) zusätzliche Joins
    join_rules = mapping.get("join_rules", {})
    extra = [t for t in plan["tables_extra"] if t in join_rules]
    joins = [join_rules[t] for t in extra]

    # 4) WHERE
    where_expr = plan["conditions"]

    # 5) Query patchen
    title_snippet = re.sub(r"[^A-Za-z0-9]+","_", user_input[:40])
    out = patch_title(seed, title_snippet)
    out = patch_select_where_joins(out, select_cols, where_expr, joins)

    # 6) Optional: GROUP/ORDER ersetzen, wenn Plan etwas liefert und Seed Blöcke hat
    if plan.get("group_by"):
        gb = "GROUP BY " + ", ".join([str(x) for x in plan["group_by"]])
        if re.search(r"\bGROUP BY\b", out, flags=re.I):
            out = re.sub(r"GROUP BY\s+(.+?)(ORDER BY|$)", gb + " \\2", out, flags=re.S | re.I)
        else:
            out += "\n" + gb
    if plan.get("order_by"):
        ob = "ORDER BY " + plan["order_by"]
        if re.search(r"\bORDER BY\b", out, flags=re.I):
            out = re.sub(r"ORDER BY\s+(.+?)($|\n)", ob + " \\2", out, flags=re.S | re.I)
        else:
            out += "\n" + ob

    return out
