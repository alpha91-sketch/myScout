import streamlit as st
from datetime import datetime
from pathlib import Path
import re
import os

st.title("Scout-Generator – basierend auf scout_temp.sql")

# Seed-Datei festlegen
seed_file = "seeds/scout_temp.sql"
if not Path(seed_file).exists():
    st.error(f"Seed-Datei {seed_file} nicht gefunden!")
    st.stop()

# Eingaben
titel_input = st.text_input("Titel für den Report", "Mein Scout Report")
fields_input = st.text_area("Felder (kommagetrennt)", "PGRDAT.NANAME,PGRDAT.VORNAME,VERTRAG.VERBEGIN,VERTRAG.VERENDE")
conds_input = st.text_area("WHERE-Bedingungen", "PGRDAT.AK = '70' AND VERTRAG.VERBEGIN >= '01.01.2024'")

# Hilfsfunktionen
def patch_title(sql_text: str, new_title: str) -> str:
    return re.sub(r'("(\d{8})","[^"]+")', f'"\\2","{new_title}"', sql_text, count=1)

def patch_ifield(sql_text: str, fields: list) -> str:
    m = re.search(r'(INSERT INTO L2001\.ifield.*?\$DATATYPES\n)(.*?)(\n/)', sql_text, flags=re.S|re.I)
    if not m: return sql_text
    start, end = m.start(2), m.end(2)
    new_lines = []
    for i, f in enumerate(fields, start=1):
        new_lines.append(f'"00000001","{i}","{f}",')
    new_block = "\n".join(new_lines)
    return sql_text[:start] + new_block + sql_text[end:]

def patch_ibedingung(sql_text: str, conds: list) -> str:
    m = re.search(r'(INSERT INTO L2001\.ibedingung.*?\$DATATYPES\n)(.*?)(\n/)', sql_text, flags=re.S|re.I)
    if not m: return sql_text
    start, end = m.start(2), m.end(2)
    new_lines = []
    for i, c in enumerate(conds, start=1):
        new_lines.append(f'"00000001","{i}","{c}",')
    new_block = "\n".join(new_lines)
    return sql_text[:start] + new_block + sql_text[end:]

# Button
if st.button("Scout-Datei erzeugen"):
    try:
        raw = Path(seed_file).read_text(encoding="utf-8", errors="ignore")
        fields = [f.strip() for f in fields_input.split(",") if f.strip()]
        conds = [c.strip() for c in conds_input.split("AND") if c.strip()]

        out = patch_title(raw, titel_input)
        out = patch_ifield(out, fields)
        out = patch_ibedingung(out, conds)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Scout_{timestamp}.sql"

        st.success("Scout-Datei generiert ✅")
        st.download_button("Scout-Datei herunterladen", data=out, file_name=file_name, mime="text/plain")

    except Exception as e:
        st.error(f"Fehler: {e}")
