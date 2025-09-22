import streamlit as st
from datetime import date, datetime
from pathlib import Path
import re
import json
import os

st.title("Scout-Import Generator (stabilisiert + Export-Fix)")

# Mapping laden
with open("data/felder_mapping.json", "r", encoding="utf-8") as f:
    MAPPING = json.load(f)

# Seeds laden
seed_files = [f for f in os.listdir("seeds") if f.endswith(".sql")]
seed_file = st.selectbox("Seed-Datei wählen", seed_files)

# Eingaben
mandant = st.text_input("Mandant", "63000")
ak = st.multiselect("Abrechnungskreis", ["55", "70", "90"], default=["70"])
stichtag = st.date_input("Stichtag aktiv bis", date(2099, 1, 31))

# Tabellen-Auswahl (erweitert)
tables = st.multiselect(
    "Tabellen wählen",
    ["PGRDAT", "VERTRAG", "FBA", "ZEITENKAL", "SALDEN"],
    default=["PGRDAT"]
)

# Felder-Auswahl pro Tabelle
fields = []
for t in tables:
    selected = st.multiselect(f"Felder aus {t} auswählen", list(MAPPING[t].keys()), key=f"fields_{t}")
    fields.extend([(t, f) for f in selected])

# Dynamische WHERE-Bausteine
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
        raw = Path(f"seeds/{seed_file}").read_text(encoding="utf-8", errors="ignore")
        titel = f"{mandant}_{','.join(ak)}_{stichtag}"

        # SELECT patch
        if fields:
            db_fields = [f"{t}.{MAPPING[t].get(f, f)}" for t, f in fields]
            select_block = ", ".join(db_fields)
            out_text = re.sub(r"SELECT\s+(.+?)\s+FROM",
                              f"SELECT {select_block} FROM",
                              raw, flags=re.S)
        else:
            out_text = raw

        # FROM patch (stabilisiert)
        join_clauses = []
        if "VERTRAG" in [t for t, _ in fields]:
            join_clauses.append("JOIN VERTRAG ON PGRDAT.MAN = VERTRAG.MAN AND PGRDAT.AK = VERTRAG.AK AND PGRDAT.PNR = VERTRAG.PNR")
        if "FBA" in [t for t, _ in fields]:
            join_clauses.append("JOIN FBA ON PGRDAT.MAN = FBA.MAN AND PGRDAT.AK = FBA.AK AND PGRDAT.PNR = FBA.PNR")
        if "ZEITENKAL" in [t for t, _ in fields]:
            join_clauses.append("JOIN ZEITENKAL ON PGRDAT.MAN = ZEITENKAL.MAN AND PGRDAT.AK = ZEITENKAL.AK AND PGRDAT.PNR = ZEITENKAL.PNR")
        if "SALDEN" in [t for t, _ in fields]:
            join_clauses.append("JOIN SALDEN ON PGRDAT.MAN = SALDEN.MAN AND PGRDAT.AK = SALDEN.AK AND PGRDAT.PNR = SALDEN.PNR")

        if join_clauses:
            out_text = re.sub(r"FROM\s+\S+", "FROM PGRDAT " + " ".join(join_clauses), out_text, flags=re.S)

        # WHERE patch
        if where_clause.strip():
            if "WHERE" in out_text:
                out_text = re.sub(r"WHERE\s+(.+?)(GROUP BY|ORDER BY|$)",
                                  f"WHERE {where_clause} \\2",
                                  out_text, flags=re.S)
            else:
                out_text = re.sub(r"(FROM.+?)(GROUP BY|ORDER BY|$)",
                                  f"\\1\nWHERE {where_clause} \\2",
                                  out_text, flags=re.S)

        # GROUP BY automatisch
        if fields:
            group_by_clause = "GROUP BY " + ",".join(str(i+1) for i in range(len(fields)))
            if "GROUP BY" in out_text:
                out_text = re.sub(r"GROUP BY\s+(.+?)(ORDER BY|$)",
                                  f"{group_by_clause} \\2",
                                  out_text, flags=re.S)
            else:
                out_text = re.sub(r"(WHERE.+?)(ORDER BY|$)",
                                  f"\\1\n{group_by_clause} \\2",
                                  out_text, flags=re.S)

        # ORDER BY patch
        if order_by.strip():
            if "ORDER BY" in out_text:
                out_text = re.sub(r"ORDER BY\s+(.+?)($|\n)",
                                  f"ORDER BY {order_by} \\2",
                                  out_text, flags=re.S)
            else:
                out_text += f"\nORDER BY {order_by}"

        # Titel patch
        m = re.search(r"i_name IN \('(\d{8})'", raw, flags=re.IGNORECASE)
        if m:
            iname = m.group(1)
            out_text = re.sub(rf'"{re.escape(iname)}","[^"]+"',
                              f'"{iname}","{titel}"',
                              out_text, count=1)

        # Export-Verwaltung: History speichern
        os.makedirs("exports", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = Path("exports/history.sql")
        with open(history_file, "a", encoding="utf-8") as hist:
            hist.write(f"\n-- Export {timestamp}\n")
            hist.write(out_text + "\n")

        # Dummy-Datei für GitHub sichtbar machen
        Path("exports/.gitkeep").write_text("")

        # Download
        st.success(f"Scout-Datei aus Seed {seed_file} wurde erstellt ✅")
        st.download_button("Scout-Datei herunterladen",
                           data=out_text,
                           file_name=f"Scout_{seed_file.replace('.sql','')}_{timestamp}.sql",
                           mime="text/plain")

    except Exception as e:
        st.error(f"Fehler: {e}")
