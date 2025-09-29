from parsers.parser_blocks import assemble_scout_file
from parsers.validator import validate_scout_sql
from pathlib import Path

def test_build_sql():
    iname = "00049999"
    tables = ["PGRDAT","SALDEN"]
    fields = ["PGRDAT.MAN","PGRDAT.AK","PGRDAT.PNR","SALDEN.URL_REST"]
    joins = [["PGRDAT","MAN","SALDEN","MAN"],
             ["PGRDAT","AK","SALDEN","AK"],
             ["PGRDAT","PNR","SALDEN","PNR"]]
    conditions = ["PGRDAT.AK = '70'"]

    sql_code = assemble_scout_file(iname, tables, fields, joins, conditions)

    Path("exports").mkdir(exist_ok=True)
    out_path = "exports/test_import.sql"
    Path(out_path).write_text(sql_code, encoding="utf-8")

    print("✅ Datei erzeugt:", out_path)

    # Validierung
    validate_scout_sql(out_path)
