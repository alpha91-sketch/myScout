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
        out_text = patch_seed_title_only_text(raw, titel)
        st.success("Scout-Datei wurde erstellt ✅ (nur Titel geändert)")
        st.download_button("Scout-Datei herunterladen",
                           data=out_text,
                           file_name="Scout_Import_MINIMAL.sql",
                           mime="text/plain")
    except Exception as e:
        st.error(f"Fehler: {e}")
