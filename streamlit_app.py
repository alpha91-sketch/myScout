import streamlit as st
from datetime import date

st.title("Scout-Abfrage Generator")

st.markdown("Dieses Formular erzeugt eine Scout-Importdatei auf Basis deiner Eingaben.")

# Eingabeformular
mandant = st.text_input("Mandant", "63000")
ak = st.multiselect("Abrechnungskreis", ["55", "70", "90"], default=["70"])
stichtag = st.date_input("Stichtag aktiv bis", date(2099, 1, 31))

if st.button("Scout-Datei erzeugen"):
    # Dummy-SQL, später durch Seed-Logik ersetzt
    sql_text = f"""-- Scout Dummy-SQL
-- Mandant: {mandant}
-- Abrechnungskreis: {','.join(ak)}
-- Stichtag: {stichtag}
"""
    st.success("Scout-Datei wurde erstellt ✅")
    st.download_button("Scout-Datei herunterladen",
                       data=sql_text,
                       file_name="Scout_Abfrage.sql",
                       mime="text/plain")
