import os
import re
from pathlib import Path
from openai import OpenAI

# OpenAI Client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Seed-Datei laden
def load_seed(seed_path="seeds/scout_temp.sql"):
    raw = Path(seed_path).read_text(encoding="utf-8", errors="ignore")
    return raw

def extract_iname(seed_text: str) -> str:
    m = re.search(r"i_name IN \('(\d{8})'", seed_text, flags=re.IGNORECASE)
    if not m:
        raise RuntimeError("I_NAME (8-stellig) nicht gefunden in Seed.")
    return m.group(1)

def patch_sql(seed_text: str, sql_core: str, title: str, desc: str) -> str:
    # SELECT-Bereich ersetzen
    out_text = re.sub(
        r"SELECT(.+?)FROM",
        f"SELECT {sql_core} FROM",
        seed_text,
        flags=re.S | re.I
    )
    # Titel patchen
    out_text = re.sub(
        r'"(\d{8})","[^"]+"',
        f'"\\1","{title}"',
        out_text,
        count=1
    )
    return out_text

def parse_user_request(user_input: str, seed_path="seeds/scout_temp.sql") -> str:
    """
    Baut Scout-kompatibles SQL auf Basis einer Seed-Datei.
    """
    seed_raw = load_seed(seed_path)
    iname = extract_iname(seed_raw)

    # KI: relevante Felder finden
    prompt = f"""
    Die User-Anfrage lautet: {user_input}

    Aufgabe:
    - Nutze Felder aus PGRDAT, VERTRAG, ZEITENKAL, SALDEN.
    - Baue daraus eine SELECT-Liste (nur Felder, getrennt mit Kommas).
    - Ergänze WHERE-Klauseln, falls nötig.
    Beispiel: PGRDAT.MAN, PGRDAT.AK, PGRDAT.PNR, VERTRAG.VERBEGIN
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Du bist ein SQL-Generator für LOGA Scout."},
                  {"role": "user", "content": prompt}],
        temperature=0
    )

    sql_raw = response.choices[0].message.content.strip()

    if not sql_raw:
        sql_raw = "PGRDAT.MAN, PGRDAT.AK, PGRDAT.PNR, PGRDAT.NANAME, PGRDAT.VORNAME"

    # Titel & Beschreibung
    title = re.sub(r"[^A-Za-z0-9]+", "_", user_input[:30])
    desc = f"Generiert aus Anfrage: {user_input}"

    # Seed patchen
    sql_final = patch_sql(seed_raw, sql_raw, title, desc)
    return sql_final
