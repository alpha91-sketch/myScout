import streamlit as st
from parser import parse_user_request

st.title("Scout KI Abfragegenerator (Seed-basiert)")

user_input = st.text_area(
    "Beschreibe deine gewünschte Auswertung (natürliche Sprache)",
    "Zeige alle Mitarbeiter mit AK=70 und SV-Tage=0"
)

if st.button("Scout-SQL generieren"):
    try:
        sql_code = parse_user_request(user_input)  # Seed-Pfad default: seeds/scout_temp.sql
        st.success("Scout-SQL wurde erfolgreich erstellt ✅")
        st.code(sql_code, language="sql")
        st.download_button(
            "Scout-SQL herunterladen",
            data=sql_code,
            file_name="Scout_Import.sql",
            mime="text/plain"
        )
    except Exception as e:
        st.error(f"Fehler: {e}")
