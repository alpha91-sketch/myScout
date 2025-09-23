import streamlit as st
from datetime import date, datetime
from pathlib import Path
import re
import os

st.title("Scout-Import Generator (stabil – Seed + Parameter-Updates)")

# ► Seed-Datei auswählen (aus /seeds)
seed_files = [f for f in os.listdir("seeds") if f.endswith(".sql")]
seed_file = st.selectbox("Seed-Datei wählen", seed_files)

# ► Parameter
mandant = st.text_input("Mandant (MAN)", "63000")
ak = st.selectbox("Abrechnungskreis (AK)", ["55", "70", "90"], index=1)  # bewusst EIN Wert (IBEDINGUNG '=')
stichtag = st.date_input("Stichtag (VER_BIS ≥)", date(2099, 1, 31))

# Hilfsfunktionen
def ddmmyyyy(d: date) -> str:
    return f"{d.day:02d}.{d.month:02d}.{d.year}"

def find_iname(seed_text: str) -> str:
    # I_NAME aus einem der DELETE-Statements ziehen
    m = re.search(r"i_name\s+IN\s+\('(\d{8})'\)", seed_text, flags=re.IGNORECASE)
    if not m:
        # Fallback: INAME (z.B. in itemplateout)
        m = re.search(r"iname\s+IN\s+\('(\d{8})'\)", seed_text, flags=re.IGNORECASE)
    if not m:
        raise RuntimeError("Konnte I_NAME/INAME im Seed nicht erkennen.")
    return m.group(1)

def patch_title(seed_text: str, iname: str, new_title: str) -> str:
    # Ersten Titel-Eintrag für dieses I_NAME patchen: "<I_NAME>","<Titel>"
    return re.sub(rf'"{re.escape(iname)}","[^"]+"',
                  f'"{iname}","{new_title}"',
                  seed_text, count=1)

def append_param_updates(seed_text: str, iname: str, man: str, ak_val: str, ver_bis_ddmmyyyy: str) -> str:
    # IBEDINGUNG: Expression-Werte setzen – gezielt über Tbl_name + F_dbcol (enthält Label + Tech-Name)
    # WICHTIG: Wir ändern NICHT die Struktur, nur die Werte der vorhandenen Bedingungen.
    updates = f"""
-- === Parameter-Updates: IBEDINGUNG (nur Werte, keine Struktur) ===
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
   set expression='{ver_bis_ddmmyyyy}'
 where i_name='{iname}'
   and lower(tbl_name)='vertrag'
   and f_dbcol like '% VER_BIS';
"""
    # Am Ende anfügen – Scout führt diese execsql-Updates nach den INSERTs aus.
    if not seed_text.endswith("\n"):
        seed_text += "\n"
    return seed_text + updates

if st.button("Scout-Datei erzeugen"):
    try:
        raw = Path(f"seeds/{seed_file}").read_text(encoding="utf-8", errors="ignore")
        iname = find_iname(raw)
        titel = f"{mandant}_{ak}_{stichtag}"

        out = patch_title(raw, iname, titel)
        out = append_param_updates(out, iname, mandant, ak, ddmmyyyy(stichtag))

        # Download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Scout_{seed_file.replace('.sql','')}_{timestamp}.sql"
        st.success(f"Scout-Datei erzeugt ✅ (Seed: {seed_file}, I_NAME: {iname})")
        st.download_button("Scout-Datei herunterladen",
                           data=out,
                           file_name=file_name,
                           mime="text/plain")
    except Exception as e:
        st.error(f"Fehler: {e}")

