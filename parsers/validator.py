from pathlib import Path
import re

REQUIRED_BLOCKS = ["itable", "ifield", "ibeziehung", "ibedingung"]

def validate_scout_sql(path: str) -> None:
    sql_text = Path(path).read_text(encoding="utf-8", errors="ignore")

    print(f"🔎 Prüfe Datei: {path}")

    # 1. Sind alle Kern-Blöcke vorhanden?
    for block in REQUIRED_BLOCKS:
        if f"INSERT INTO L2001.{block}" not in sql_text.lower():
            print(f"❌ Block {block.upper()} fehlt!")
        else:
            print(f"✅ Block {block.upper()} gefunden.")

    # 2. Zeilenstruktur prüfen (Anzahl Kommas)
    for block in REQUIRED_BLOCKS:
        pattern = re.compile(rf'INSERT INTO L2001.{block}(.+?)/', flags=re.S | re.I)
        m = pattern.search(sql_text)
        if m:
            lines = m.group(1).splitlines()
            for line in lines:
                if line.strip().startswith('"'):
                    comma_count = line.count(",")
                    print(f"ℹ️ {block.upper()}-Zeile: {comma_count} Kommas -> {line[:60]}...")

    print("✅ Validierung abgeschlossen.")
