import os
from openai import OpenAI

# Client initialisieren (API-Key muss in GitHub Secret OPENAI_API_KEY hinterlegt sein)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def parse_user_request(user_input: str) -> str:
    """
    Nimmt eine natürliche Spracheingabe (z.B. 'Zeige alle Mitarbeiter mit AK=70, die ...')
    und gibt ein SQL-Snippet im Scout-Format zurück.
    """

    prompt = f"""
    Du bist ein SQL-Generator für P&I Loga Scout.
    Aufgabe: Erstelle aus folgender Anforderung eine importierbare Scout-SQL-Abfrage.
    Nutze die Tabellen PGRDAT (Personendaten) und VERTRAG (Vertragsdaten) als Kern,
    und ergänze weitere Tabellen falls nötig.
    Achte auf:
    - korrektes SELECT
    - sauberes WHERE
    - GROUP BY und ORDER BY nur falls sinnvoll
    - nur gültige Feldnamen aus dem Feldkatalog
    - Ausgabe als plain SQL, ohne Kommentare oder Erklärungen.

    Anforderung:
    {user_input}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Du bist ein SQL-Generator für Scout-Auswertungen."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    sql_code = response.choices[0].message.content.strip()
    return sql_code


# Testlauf (kann in Streamlit oder Colab ausprobiert werden)
if __name__ == "__main__":
    test_input = "Zeige alle Mitarbeiter mit Vertragsbeginn nach dem 01.01.2024 und leeren Personalakten."
    print(parse_user_request(test_input))
