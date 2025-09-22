S3
Sehr geehrte Damen und Herren,   
vielen Dank für Ihre E-Mail. Ich bin gerade nicht erreichbar. Meine Emails werden nicht weitergeleitet. 

Beste Grüße, 
Andy Runzheimer   

Dear Sir or Madam, 
Thank you for your email. I'm currently not available. My emails will not be forwarded.

Best regards, 
Andy

Runzheimer, Andy
​
Runzheimer, Andy​
import streamlit as st
from datetime import date
from pathlib import Path
import re
import json
import os

st.title("Scout-Import Generator (Seed-Auswahl + SELECT + WHERE + GROUP BY + ORDER BY)")

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

# Tabelle & Felder
table = st.selectbox("Tabelle wählen", list(MAPPING.keys()))
fields = st.multiselect("Felder auswählen", list(MAPPING[table].keys()))

# WHERE-Bedingung
where_clause = st.text_area("WHERE-Bedingungen (optional)", "PGRDAT.AK = '70'")

# ORDER BY
order_by = st.text_input("ORDER BY (optional)", "1,2")

if st.button("Scout-Datei erzeugen"):
    try:
        raw = Path(f"seeds/{seed_file}").read_text(encoding="utf-8", errors="ignore")
        titel = f"{mandant}_{','.join(ak)}_{stichtag}"

        # SELECT patch
        if fields:
            db_fields = [MAPPING[table].get(f, f) for f in fields]
            select_block = ", ".join([f"{table}.{f}" for f in db_fields])
            out_text = re.sub(r"SELECT\s+(.+?)\s+FROM",
                              f"SELECT {select_block} FROM",
                              raw, flags=re.S)
        else:
            out_text = raw

        # WHERE patch
        if where_clause.strip():
            out_text = re.sub(r"WHERE\s+(.+?)(GROUP BY|ORDER BY|$)",
                              f"WHERE {where_clause} \\2",
                              out_text, flags=re.S)

        # GROUP BY automatisch ergänzen
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
                           file_name=f"Scout_{seed_file.replace('.sql','')}_GEN.sql",
                           mime="text/plain")
    except Exception as e:
        st.error(f"Fehler: {e}")
