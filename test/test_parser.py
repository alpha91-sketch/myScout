# tests/test_parser.py
from pathlib import Path
from parser import parse_user_request, check_seed_sql

SEED_PATH = "seeds/scout_temp.sql"
EXPORT_PATH = "exports/test_output.sql"

def test_seed_valid():
    check_seed_sql(SEED_PATH)

def test_generate_sql():
    user_input = "Zeige alle Mitarbeiter mit AK=70 und SV-Tage=0"
    sql_code = parse_user_request(user_input, seed_path=SEED_PATH)

    Path("exports").mkdir(exist_ok=True)
    Path(EXPORT_PATH).write_text(sql_code, encoding="utf-8")

    assert "SELECT" in sql_code
    assert "FROM" in sql_code
    assert "PGRDAT" in sql_code
    assert "INSERT" in sql_code or "ISV_ABFRAGE" in sql_code

    print("✅ Test erfolgreich:", EXPORT_PATH)
