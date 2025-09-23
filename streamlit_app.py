import streamlit as st
from datetime import date, datetime
from pathlib import Path
import re
import os

st.title("Scout-Import Generator (Template-basiert, stabil)")

# Template laden
template_file = "seeds/template_minimal.sql"
raw_template = Path(template_file).read_text(encoding="utf-8", errors="ignore")

# Eingaben
mandant = st.text_input("Mandant (MAN)", "63000")
ak = st.text_input("Abrechnungskreis (AK)", "70")
stichtag = st.date_input("Stichtag (VER_BIS ≥)", date(2099, 1, 31))

# Hilfsfunktionen
def ddmmyyyy(d: date) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"

def patch_iname_and_title(template_text: str, new_iname: str, new_title: str) -> str:
    # I_NAME ersetzen
    out = re.sub(r"99999999", new_iname, template_text)
    # Titel ändern
    out = re.sub(r"'TEMPLATE_MINIMAL'", f"'{new_title}'", out, count=1)
    return out

def append_param_updates(base_text: str, iname: str, man: str, ak_val: str, ver_bis_val: str) -> str:
    updates = f"""
-- === Parameter-Updates für Bedingungen ===
execsql update L2001.ibedingung
   set expression='{man}'
 where i_name='{iname}'
   and lower(tbl_name)='pgrdat'
   and f_dbcol like '% MAN';

execsql update L2001.ibedingung
   set expression='{ak_val}'
 where i_name='{iname}'
   and lower(tbl_name)='pgrdat'
   and f_dbcol like '% AK';

execsql update L2001.ibedingung
   set expression='{ver_bis_val}'
 where i_name='{iname}'
   and lower(tbl_name)='vertrag'
   and f_dbcol like '% VERENDE%';
"""
    return base_text + "\n" + updates

if st.button("Scout-Datei erzeugen"):
    try:
        # Neue I_NAME generieren (z. B. Zeitstempel als 8-stellige Zahl)
        new_iname = datetime.now().strftime("%H%M%S%f")[:8]
        titel = f"{mandant}_{ak}_{stichtag}"

        # Template patchen
        patched = patch_iname_and_title(raw_template, new_iname, titel)

        # Parameter anhängen
        out = append_param_updates(patched, new_iname, mandant, ak, ddmmyyyy(stichtag))

        # Export speichern
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Scout_Template_{timestamp}.sql"
        file_path = os.path.join("exports", file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(out)

        # Download
        st.success("Scout-Datei wurde erstellt ✅ (Template-basiert, stabil)")
        st.download_button("Scout-Datei herunterladen",
                           data=out,
                           file_name=file_name,
                           mime="text/plain")

    except Exception as e:
        st.error(f"Fehler: {e}")
