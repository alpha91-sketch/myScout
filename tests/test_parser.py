from pathlib import Path
from parser import parse_user_request

SEED_PATH = "seeds/scout_temp.sql"
EXPORT_PATH = "exports/test_output.sql"

def test_generate_sql():
    user_input = "Zeige alle Mitarbeiter mit AK=70 und Resturlaub"
    sql_code = parse_user_request(user_input, seed_path=SEED_PATH)

    Path("exports").mkdir(exist_ok=True)
    Path(EXPORT_PATH).write_text(sql_code, encoding="utf-8")

    assert "IFIELD" in sql_code
    assert "IBEZIEHUNG" in sql_code
    assert "IBEDINGUNG" in sql_code

    print("✅ Scout-konforme SQL generiert:", EXPORT_PATH)
