import streamlit as st
from datetime import date
from pathlib import Path
import re

st.title("Scout-Import Generator (sicherer Minimal-Patch)")

mandant = st.text_input("Mandant", "63000")
ak = st.multiselect("Abrechnungskreis", ["55","70","90"], default=["70"])
stichtag = st.date_input("Stichtag aktiv bis", date(2099, 1, 31))
seed_file = st.text_input("Seed-Datei (Pfad im Repo)", "seeds/00037736.sql")

def patch_seed_title_only_text(text: str, new_title: str):
    m = re.search(r"i_name IN \('(\d{8})'", text, flags=re.IGNORECASE)
    if not m:
        raise RuntimeError("Konnte I_NAME im Seed nicht erkennen.")
    iname = m.group(1)
    text = re.sub(rf'"{re.escape(iname)}","[^"]+"',
                  f'"{iname}","{new_title}"',
                  text, count=1)
    return text
if st.button("Scout-Datei erzeugen"):
    try:
        raw = Path(seed_file).read_text(encoding="utf-8", errors="ignore")
        titel = f"{mandant}_{','.join(ak)}_{stichtag}"

        # Feldmapping anwenden
        db_fields = [MAPPING[table].get(f, f) for f in fields]
        select_block = ", ".join([f"{table}.{f}" for f in db_fields])
        out_text = re.sub(r"SELECT\s+(.+?)\s+FROM",
                          f"SELECT {select_block} FROM",
                          raw, flags=re.S)

        # Titel ändern
        m = re.search(r"i_name IN \('(\d{8})'", raw, flags=re.IGNORECASE)
        if m:
            iname = m.group(1)
            out_text = re.sub(rf'"{re.escape(iname)}","[^"]+"',
                              f'"{iname}","{titel}"',
                              out_text, count=1)

        st.success("Scout-Datei wurde erstellt ✅ (mit SELECT)")
        st.download_button("Scout-Datei herunterladen",
                           data=out_text,
                           file_name="Scout_Import_SELECT.sql",
                           mime="text/plain")
    except Exception as e:
        st.error(f"Fehler: {e}")
