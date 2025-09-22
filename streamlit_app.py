import streamlit as st
from datetime import date
from pathlib import Path
import re
import json
import os

st.title("Scout-Import Generator (Multi-Tabellen + WHERE-Bausteine)")

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
tables = st.multiselect("Tabellen wählen", ["PGRDAT", "VERTRAG", "FBA"], default=["PGRDAT"])

# Felder-Auswahl pro Tabelle
fields = []
for t in tables:
    selected = st.multiselect(f"Felder aus {t} auswählen", list(MAPPING[t].keys()))
    fields.extend([(t, f) for f in selected])

# WHERE-Bausteine
st.subheader("WHERE-Bedingungen aufbauen")
where_parts = []
max_conditions = 3  # Anzahl Bedingungen begrenzen (für Demo)

for i in range(max_conditions):
    col1, col2, col3 = st.columns([3, 2, 3])
    with col1:
        table_choice = st.selectbox(f"Tabelle {i+1}", tables, key=f"where_table_{i}")
        field_choice = st.selectbox(
            f"Feld {i+1}", list(MAPPING[table_choice].keys()), key=f"where_field_{i}"
        )
    with col2:
        operator = st.selectbox(
            f"Operator {i+1}", ["=", "!=", ">", "<", ">=", "<=", "LIKE"], key=f"where_op_{i}"
        )
    with col3:
        value = st.text_input(f"Wert {i+1}", key=f"where_val_{i}")
    if value:
        where_parts.append(f"{table_choice}.{MAPPING[table_choice][field_choice]} {operator} '{value}'")

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

        # FROM patch: Joins für mehrere Tabellen
        if "PGRDAT" in [t for t, _ in fields] and "VERTRAG" in [t for t, _ in fields]:
            out_text = re.sub(r"FROM\s+(\S+)",
                              r"FROM PGRDAT JOIN VERTRAG ON PGRDAT.MAN = VERTRAG.MAN "
                              r"AND PGRDAT.AK = VERTRAG.AK AND PGRDAT.PNR = VERTRAG.PNR",
                              out_text, flags=re.S)

        if "PGRDAT" in [t for t, _ in fields] and "FBA" in [t for t, _ in fields]:
            out_text = out_text.replace(
                "FROM PGRDAT",
                "FROM PGRDAT JOIN FBA ON PGRDAT.MAN = FBA.MAN "
                "AND PGRDAT.AK = FBA.AK AND PGRDAT.PNR = FBA.PNR"
            )

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
                if "GROUP BY" in out_text:
                    out_text = re.sub(r"(GROUP BY.+?)($|\n)",
                                      f"\\1\nORDER BY {order_by} \\2",
                                      out_text, flags=re.S)
                else:
                    out_text = re.sub(r"(WHERE.+?)($|\n)",
                                      f"\\1\nORDER BY {order_by} \\2",
                                      out_text, flags=re.S)

        # Titel patch
        m = re.search(r"i_name IN \('(\d{8})'", raw, flags=re.IGNORECASE)
        if m:
            iname = m.group(1)
            out_text = re.sub(rf'"{re.escape(iname)}","[^"]+"',
                              f'"{iname}","{titel}"',
                              out_text, count=1)

        st.success(f"Scout-Datei aus Seed {seed_file} wurde erstellt ✅")
        st.download_button("Scout-Datei herunterladen",
                           data=out_text,
                           file_name=f"Scout_{seed_file.replace('.sql','')}_MULTI_WHERE.sql",
                           mime="text/plain")
    except Exception as e:
        st.error(f"Fehler: {e}")
