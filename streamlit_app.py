import streamlit as st
from datetime import datetime
from pathlib import Path
import re
import os

st.title("Scout Pegasus Mini – Freitext → Scout-Export")

# Seeds im Repo suchen
seed_files = [f for f in os.listdir("seeds") if f.endswith(".sql")]
if not seed_files:
    st.error("Kein Seed in /seeds/ gefunden! Bitte mindestens eine .sql dorthin legen.")
    st.stop()

seed_file = st.selectbox("Seed-Datei wählen", seed_files)

# Eingabe: Freitext-Frage
frage = st.text_area("Deine Frage:", "Welche Mitarbeiter aus AK 70 haben ab 01.01.2024 einen Vertrag?")

# Wörterbuch (Mapping Freitext → Scout-Felder)
FIELD_MAP = {
    "name": "PGRDAT.NANAME",
    "vorname": "PGRDAT.VORNAME",
    "vertrag": "VERTRAG.VERBEGIN",
    "vertragsbeginn": "VERTRAG.VERBEGIN",
    "resturlaub": "ZEITENKAL.RESTURLAUB",
}

# Parser für die Eingabe
def parse_frage(text: str):
    conds = []
    fields = []

    # AK erkennen
    m = re.search(r"AK\s*(\d+)", text, flags=re.I)
    if m:
        conds.append(f"PGRDAT.AK = '{m.group(1)}'")

    # Datum erkennen
    m = re.search(r"ab\s*(\d{1,2}\.\d{1,2}\.\d{4})", text)
    if m:
        conds.append(f"VERTRAG.VERBEGIN >= '{m.group(1)}'")

    # Felder aus Wörterbuch
    for k, v in FIELD_MAP.items():
        if k in text.lower():
            fields.append(v)

    if not fields:
        fields = ["PGRDAT.NANAME", "PGRDAT.VORNAME"]  # Standardfelder

    return fields, conds

# Patch-Funktionen
def patch_imember_title(sql_text: str, new_title: str) -> str:
    return re.sub(r'("00000001","[^"]+")', f'"00000001","{new_title}"', sql_text, count=1)

def patch_ifield(sql_text: str, fields: list) -> str:
    lines = []
    for i, f in enumerate(fields, start=1):
        lines.append(f'"00000001","{i}","{f}",')
    block = "\n".join(lines)
    return re.sub(r'INSERT INTO L2001.ifield.*?\n(.*?)\n/', 
                  f'INSERT INTO L2001.ifield\n$DATATYPES\n{block}\n/', 
                  sql_text, flags=re.S)

def patch_ibedingung(sql_text: str, conds: list) -> str:
    lines = []
    for i, c in enumerate(conds, start=1):
        lines.append(f'"00000001","{i}","{c}",')
    if not lines:
        lines.append('"00000001","1","1=1",')  # Default-Bedingung (immer wahr)
    block = "\n".join(lines)
    return re.sub(r'INSERT INTO L2001.ibedingung.*?\n(.*?)\n/', 
                  f'INSERT INTO L2001.ibedingung\n$DATATYPES\n{block}\n/', 
                  sql_text, flags=re.S)

# Hauptlogik
if st.button("Scout-Datei erzeugen"):
    try:
        raw = Path(f"seeds/{seed_file}").read_text(encoding="utf-8", errors="ignore")

        # Frage parsen
        fields, conds = parse_frage(frage)

        # Patches anwenden
        titel = frage[:50]
        out = patch_imember_title(raw, titel)
        out = patch_ifield(out, fields)
        out = patch_ibedingung(out, conds)

        # Ergebnisdatei
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Scout_{Path(seed_file).stem}_{timestamp}.sql"

        st.success("Scout-Datei generiert ✅")
        st.download_button("Scout-Datei herunterladen", data=out, file_name=file_name, mime="text/plain")

    except Exception as e:
        st.error(f"Fehler: {e}")
