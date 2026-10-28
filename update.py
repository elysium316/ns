import os
import requests
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# NS API
ns_key = os.environ.get("NS_API_KEY")

# TIJDZONE en "time keys"
nl_tijdzone = ZoneInfo("Europe/Amsterdam")
tijd_nu = datetime.now(nl_tijdzone)
print(tijd_nu)
tijd_straks = tijd_nu + timedelta(hours=1)

# OPVRAGEN
url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips?fromStation=LEDN&toStation=DTCH"
headers = {"Ocp-Apim-Subscription-Key": ns_key}
response = requests.get(url, headers=headers)

# Als de API een fout geeft (bijv. verkeerde sleutel), stop dan
if response.status_code != 200:
    print(f"Fout bij ophalen NS data: {response.status_code}")
    exit(1)

data = response.json()
tijd_nu = datetime.now().strftime('%H:%M:%S')

# 3. Begin met het bouwen van de HTML pagina (ZONDER Javascript)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Leiden C. - Doetinchem de Huet</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; background: #fff; color: #000; padding: 10px; }}
        h1 {{ font-size: 50px; margin: 0; color: #003399; }}
        .tijd {{ font-size: 50px; font-weight:bold; color: black; margin-bottom: 15px; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #ccc; }}
        .vertrek {{ font-weight: bold; font-size: 16px; }}
        .spoor {{ color: #003399; font-weight: bold; }}
        .status {{ color: #d00; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Leiden C</h1>
    <h1>Utrecht C.</h1>
    <div class="tijd">{tijd_nu}</div>
    <ul>
"""

# 4. Voeg de treinen toe aan het lijstje
for trip in data.get('trips', [])[:4]: # Toon max 4 reizen
    print(trip)
    try:
        # Haal de vertrektijd uit de complexe datastructuur (neem alleen HH:MM)
        vertrek = trip['legs'][0]['origin']['plannedDateTime'][11:16]
        spoor = trip['legs'][0]['origin'].get('plannedTrack', '?')
        status = trip['status']
        
        html_content += f"""
        <li>
            <span class="vertrek">{vertrek}</span> - Spoor <span class="spoor">{spoor}</span><br>
            <span class="status">Status: {status}</span>
        </li>
        """
    except IndexError:
        continue

html_content += """
    </ul>
</body>
</html>
"""

# 5. Sla dit op als de HTML pagina die we online gaan zetten
with open("info.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML succesvol gebouwd!")
