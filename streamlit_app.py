import streamlit as st
from datetime import datetime, date
from pathlib import Path
import re
import os

st.title("Scout-Generator – Grundstruktur + Urlaubskürzung (stabil)")

SEED_PATH = "seeds/scout_temp.sql"

# ---------- Utilities ----------
def read_seed(path: str) -> str:
    if not Path(path).exists():
        st.error(f"Seed-Datei fehlt: {path}")
        st.stop()
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def extract_iname(sql_text: str) -> str:
    """
    Versucht, die I_NAME (8-stellige Nummer) aus dem IMEMBER-Block zu ziehen.
    Arbeitet robust auch ohne $DATATYPES oder wenn Reihenfolge anders ist.
    """
    # 1. Direkt nach 8-stelliger Zahl in Anführungszeichen suchen
    m = re.search(r'INSERT\s+INTO\s+L2001\.imember.*?\n\s*"(\d{8})"', sql_text, flags=re.I|re.S)
    if m:
        return m.group(1)

    # 2. Fallback: irgendeine 8-stellige Zahl in Anführungszeichen
    m = re.search(r'"(\d{8})"', sql_text)
    if m:
        return m.group(1)

    raise RuntimeError("I_NAME (imember) nicht gefunden. Bitte prüfen, ob Seed-Datei korrekt ist.")

def patch_title(sql_text: str, iname: str, new_title: str) -> str:
    # Ersetzt NUR die erste IMEMBER-Zeile ("<iname>","<titel>",)
    pattern = rf'("({re.escape(iname)})","[^"]+")'
    return re.sub(pattern, f'"{iname}","{new_title}"', sql_text, count=1)

def replace_block(sql_text: str, table: str, new_lines: list) -> str:
    """
    Ersetzt den $DATATYPES-Datenblock eines INSERTs (z. B. IFIELD oder IBEDINGUNG) durch new_lines.
    """
    regex = rf'(INSERT\s+INTO\s+L2001\.{table}\s*\$DATATYPES\s*\n)(.*?)(\n/)'
    m = re.search(regex, sql_text, flags=re.I|re.S)
    if not m:
        # Falls der Block nicht im Seed existiert, belassen wir es (kein riskantes Anhängen).
        return sql_text
    start, end = m.start(2), m.end(2)
    block = "\n".join(new_lines) if new_lines else ""
    return sql_text[:start] + block + sql_text[end:]

def ddmmyyyy(dt: date) -> str:
    return f"{dt.day:02d}.{dt.month:02d}.{dt.year}"

# ---------- UI ----------
seed_raw = read_seed(SEED_PATH)
iname = extract_iname(seed_raw)

modus = st.radio("Modus wählen", ["Manuell", "Urlaubskürzung"], horizontal=True)

# Gemeinsame Eingaben
titel = st.text_input("Report-Titel", "Urlaubskürzung – Monatsprüfung")

if modus == "Manuell":
    st.subheader("Manuelle Felder / Bedingungen")
    fields_input = st.text_area("Felder (kommagetrennt)", "PGRDAT.NANAME,PGRDAT.VORNAME,VERTRAG.VERBEGIN,VERTRAG.VERENDE")
    conds_input = st.text_area("WHERE-Bedingungen (je Zeile oder mit AND getrennt)",
                               "PGRDAT.AK = '70' AND VERTRAG.VERBEGIN >= '01.01.2024'")

    if st.button("Scout-Datei erzeugen (Manuell)"):
        try:
            fields = [f.strip() for f in fields_input.split(",") if f.strip()]
            # Bedingungen: sowohl je Zeile als auch per AND akzeptieren:
            conds_lines = []
            for line in conds_input.splitlines():
                line = line.strip()
                if not line:
                    continue
                # split on AND to allow a single-line input
                parts = [p.strip() for p in re.split(r'\bAND\b', line, flags=re.I) if p.strip()]
                conds_lines.extend(parts)

            out = patch_title(seed_raw, iname, titel)

            # IFIELD
            if fields:
                new_ifield = [f'"{iname}","{i}","{fld}",' for i, fld in enumerate(fields, start=1)]
                out = replace_block(out, "ifield", new_ifield)

            # IBEDINGUNG
            if conds_lines:
                new_conds = [f'"{iname}","{i}","{expr}",' for i, expr in enumerate(conds_lines, start=1)]
                out = replace_block(out, "ibedingung", new_conds)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button("Scout-Datei herunterladen",
                               data=out, file_name=f"Scout_Manuell_{ts}.sql", mime="text/plain")
            st.success("Scout-Datei generiert ✅")
        except Exception as e:
            st.error(f"Fehler: {e}")

else:
    st.subheader("Urlaubskürzung – Parametrisierung")

    # Monat / Jahr
    jahr = st.number_input("Jahr", value=date.today().year, step=1, format="%d")
    monat = st.number_input("Monat (1–12)", value=date.today().month, min_value=1, max_value=12, step=1, format="%d")

    # Fehlzeitcodes
    default_codes = ["KOL","KEND1","KEND2","KEND3","KUR","ELTERNZEIT","PFLEGEZEIT","KON","WI"]
    codes = st.text_input("Fehlzeit-Codes (kommagetrennt)", ",".join(default_codes))

    # SV-Tage Feld (anpassbar, falls anders benannt im System)
    svtage_field = st.text_input("Feldname für SV-Tage (z. B. SALDEN.SV_TAGE)", "SALDEN.SV_TAGE")
    require_sv_zero = st.checkbox("Nur Mitarbeiter mit SV-Tage = 0 berücksichtigen", value=True)

    # HU30 Marker als Feld-Ausdruck (Scout akzeptiert häufig Ausdrücke im IFIELD)
    hu_marker = st.text_input("Kürzungs-Hinweis (Konstante als Feld-Ausdruck)", "'HU30'")

    # Grund-Felder (kannst du anpassen/erweitern)
    base_fields_default = "PGRDAT.MAN,PGRDAT.AK,PGRDAT.PNR,PGRDAT.NANAME,PGRDAT.VORNAME,VERTRAG.VERBEGIN,VERTRAG.VERENDE"
    base_fields = st.text_input("Basis-Felder (kommagetrennt)", base_fields_default)

    # Optionale Felder für Urlaub (anpassbar auf eure SALDEN-/URlaubsfelder)
    url_fields_default = "SALDEN.URL_GESAMT,SALDEN.URL_GESETZLICH,SALDEN.URL_FREIWILLIG"
    url_fields = st.text_input("Urlaubs-Felder (kommagetrennt, an euer Schema anpassen)", url_fields_default)

    # Optionaler Ausdruck zur Duplikatsvermeidung (bereits gekürzte Ansprüche nicht erneut)
    already_reduced_expr = st.text_input(
        "Bedingung 'noch nicht gekürzt' (optional, z. B. keine HU30 Historie)",
        ""  # leer = keine zusätzliche Bedingung
    )

    if st.button("Scout-Datei erzeugen (Urlaubskürzung)"):
        try:
            # 1) Titel patchen
            out = patch_title(seed_raw, iname, titel)

            # 2) IFIELD aufbauen: Basisfelder + Urlaubsfelder + HU30-Marker
            fields = [f.strip() for f in (base_fields.split(",") + url_fields.split(",") + [hu_marker]) if f.strip()]
            new_ifield = [f'"{iname}","{i}","{fld}",' for i, fld in enumerate(fields, start=1)]
            out = replace_block(out, "ifield", new_ifield)

            # 3) IBEDINGUNG aufbauen
            #   Monatserste/Monatsletzte im DD.MM.YYYY-Format
            from calendar import monthrange
            first_day = date(int(jahr), int(monat), 1)
            last_day = date(int(jahr), int(monat), monthrange(int(jahr), int(monat))[1])
            d1 = ddmmyyyy(first_day)
            d2 = ddmmyyyy(last_day)

            # Fehlzeitliste
            code_list = [c.strip() for c in codes.split(",") if c.strip()]
            in_list = ",".join([f"'{c}'" for c in code_list]) if code_list else "''"

            # Bedingungen:
            conds = []
            # a) Fehlzeiten-Codes (Tabelle/Feld bitte ggf. anpassen: ZEITENKAL.FEHLKZ angenommen)
            conds.append(f"ZEITENKAL.FEHLKZ IN ({in_list})")
            # b) voller Kalendermonat: Beginn <= Monatserster UND Ende >= Monatsletzter (Felder ggf. anpassen)
            conds.append(f"ZEITENKAL.VON <= '{d1}'")
            conds.append(f"ZEITENKAL.BIS >= '{d2}'")
            # c) SV-Tage = 0 (optional)
            if require_sv_zero and svtage_field.strip():
                conds.append(f"{svtage_field.strip()} = 0")
            # d) bereits gekürzte ausschließen (optional)
            if already_reduced_expr.strip():
                conds.append(f"({already_reduced_expr.strip()})")

            new_conds = [f'"{iname}","{i}","{expr}",' for i, expr in enumerate(conds, start=1)]
            out = replace_block(out, "ibedingung", new_conds)

            # 4) Download
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button("Scout-Datei herunterladen",
                               data=out, file_name=f"Scout_Urlaubskuers_{jahr}_{monat:02d}_{ts}.sql", mime="text/plain")
            st.success("Scout-Datei generiert ✅")
        except Exception as e:
            st.error(f"Fehler: {e}")
