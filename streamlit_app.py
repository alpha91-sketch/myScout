import streamlit as st
from datetime import date, datetime
import json
import os

st.title("Scout-Import Generator (Minimal, PGRDAT + VERTRAG)")

# Mapping laden
with open("data/felder_mapping.json", "r", encoding="utf-8") as f:
    MAPPING = json.load(f)

# Eingaben
mandant = st.text_input("Mandant", "63000")
ak = st.multiselect("Abrechnungskreis", ["55", "70", "90"], default=["70"])
stichtag = st.date_input("Stichtag aktiv bis", date(2099, 1, 31))

# Tabellen fix: PGRDAT + VERTRAG
tables = ["PGRDAT", "VERTRAG"]

# Felder-Auswahl
fields = []
for t in tables:
    selected = st.multiselect(f"Felder aus {t} auswählen", list(MAPPING[t].keys()), key=f"fields_{t}")
    fields.extend([(t, f) for f in selected])

# WHERE-Bausteine
st.subheader("WHERE-Bedingungen")
if "where_conditions" not in st.session_state:
    st.session_state["where_conditions"] = []

def add_condition():
    st.session_state["where_conditions"].append({"table": "PGRDAT", "field": "", "op": "=", "val": ""})

def clear_conditions():
    st.session_state["where_conditions"] = []

st.button("Bedingung hinzufügen", on_click=add_condition)
st.button("Alle Bedingungen löschen", on_click=clear_conditions)

where_parts = []
for idx, cond in enumerate(st.session_state["where_conditions"]):
    col1, col2, col3, col4 = st.columns([2, 3, 2, 3])
    with col1:
        table_choice = st.selectbox(f"Tabelle {idx+1}", tables, key=f"where_table_{idx}")
        cond["table"] = table_choice
    with col2:
        field_choice = st.selectbox(f"Feld {idx+1}", list(MAPPING[cond['table']].keys()), key=f"where_field_{idx}")
        cond["field"] = field_choice
    with col3:
        cond["op"] = st.selectbox(f"Operator {idx+1}", ["=", "!=", ">", "<", ">=", "<=", "LIKE"], key=f"where_op_{idx}")
    with col4:
        cond["val"] = st.text_input(f"Wert {idx+1}", key=f"where_val_{idx}")
    if cond["val"]:
        where_parts.append(f"{cond['table']}.{MAPPING[cond['table']][cond['field']]} {cond['op']} '{cond['val']}'")

where_clause = " AND ".join(where_parts)

# ORDER BY
order_by = st.text_input("ORDER BY (optional)", "1,2")

if st.button("Scout-Datei erzeugen"):
    try:
        # SELECT Block
        if fields:
            db_fields = [f"{t}.{MAPPING[t].get(f, f)}" for t, f in fields]
        else:
            db_fields = ["PGRDAT.MAN", "PGRDAT.AK", "PGRDAT.PNR"]  # Fallback
        select_block = ",\n    ".join(db_fields)

        # FROM Block mit fixem Join
        from_block = (
            "FROM PGRDAT\n"
            "JOIN VERTRAG ON PGRDAT.MAN = VERTRAG.MAN\n"
            "    AND PGRDAT.AK = VERTRAG.AK\n"
            "    AND PGRDAT.PNR = VERTRAG.PNR"
        )

        # WHERE Block
        where_block = ""
        if where_clause.strip():
            where_block = f"WHERE {where_clause}"

        # GROUP BY Block
        group_by_block = ""
        if fields:
            group_by_block = "GROUP BY " + ",".join(str(i+1) for i in range(len(fields)))

        # ORDER BY Block
        order_by_block = ""
        if order_by.strip():
            order_by_block = f"ORDER BY {order_by}"

        # Finales SQL zusammensetzen
        out_text = (
            "SELECT\n    " + select_block + "\n" +
            from_block + "\n" +
            (where_block + "\n" if where_block else "") +
            (group_by_block + "\n" if group_by_block else "") +
            (order_by_block + "\n" if order_by_block else "")
        )

        # Export speichern
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"Scout_Minimal_{timestamp}.sql"
        file_path = os.path.join("exports", file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(out_text)

        # Download
        st.success("Scout-Datei wurde erstellt ✅ (Minimal-Version)")
        st.download_button("Scout-Datei herunterladen",
                           data=out_text,
                           file_name=file_name,
                           mime="text/plain")

    except Exception as e:
        st.error(f"Fehler: {e}")
