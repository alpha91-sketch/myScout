import streamlit as st
import json
from datetime import date

# Mapping laden
with open("data/felder_mapping.json", "r", encoding="utf-8") as f:
    MAPPING = json.load(f)

st.title("Scout-Abfrage Generator")

# Eingaben
mandant = st.text_input("Mandant", "63000")
ak = st.multiselect("Abrechnungskreis", ["55", "70", "90"], default=["70"])
stichtag = st.date_input("Stichtag aktiv bis", date(2099, 1, 31))

# Tabellen & Felder
table = st.selectbox("Tabelle wählen", list(MAPPING.keys()))
fields = st.multiselect("Felder auswählen", list(MAPPING[table].keys()))

if st.button("Scout-Datei erzeugen"):
    # SELECT Block aus Felder generieren
    selected = [MAPPING[table][f] for f in fields]
    sql_text = f"SELECT {', '.join(selected)} FROM {table};"

    st.success("Scout-Datei wurde erstellt ✅")
    st.download_button("Scout-Datei herunterladen",
                       data=sql_text,
                       file_name="Scout_Abfrage.sql",
                       mime="text/plain")
