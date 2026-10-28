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
tijd_zoeken = tijd_nu - timedelta(hours=1, minutes=30)
ns_tijd = tijd_zoeken.strftime('%Y-%m-%dT%H:%M:%S')
tijd_vis = tijd_nu.strftime('%H:%M')

# OPVRAGEN
url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips?fromStation=LEDN&toStation=DTCH&dateTime={ns_tijd}"
headers = {"Ocp-Apim-Subscription-Key": ns_key}
response = requests.get(url, headers=headers)

# Als de API een fout geeft (bijv. verkeerde sleutel), stop dan
if response.status_code != 200:
    print(f"Fout bij ophalen NS data: {response.status_code}")
    exit(1)

data = response.json()

# 3. Begin met het bouwen van de HTML pagina (ZONDER Javascript)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Leiden C. - Doetinchem de Huet</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; background: #fff; color: #000; padding: 10px; }}
        h1 {{ font-size: 45px; margin: 0; color: #003399; }}
        .tijd {{ font-size: 50px; font-weight:bold; color: black; margin-bottom: 15px; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #ccc; }}
        .vertrek {{ font-weight: bold; font-size: 30px; }}
        .spoor {{ color: #003399; font-weight: bold; }}
        .status {{ color: #d00; font-size: 12px; }}
    </style>
</head>
<body style="margin:2pt 0 2pt 0;padding:2pt 0 2pt 0;">
    <h1>Leiden C.</h1>
    <h1>Dtc DH</h1>
    <div class="tijd">{tijd_vis}</div>
    <ul>
"""

for trip in data.get('trips', [])[:4]: # Toon max 4 reizen
    status = trip.get('status', 'ONBEKEND')
    
    # Begin een overkoepelend blok voor één complete reis (van A naar B)
    html_content += f"""
    <li style="margin-bottom: 15px; border-bottom: 2px solid #003399; padding-bottom: 10px;">
        <div class="status" style="font-weight: bold; margin-bottom: 5px;">Status: {status}</div>
        <ul style="list-style-type: none; padding-left: 0; margin: 0;">
    """
    
    # Loop nu door alle afzonderlijke voertuigen/overstappen (legs) van DEZE reis
    for leg in trip.get('legs', []):
        if leg.get('travelType') == 'PUBLIC_TRANSIT':
            vervoer = leg['product']['shortCategoryName'] # Bijv. IC, SPR of BUS
            
            # --- VERTREK INFO ---
            v_station = leg['origin']['name']
            if v_station == "Leiden Centraal":
                v_station = "Leiden C."
            elif v_station == "Utrecht Centraal":
                v_station = "Utrecht C."
            elif v_station == "Arnhem Centraal":
                v_station = "Arnhem C."
            elif v_station == "Doetinchem De Huet":
                v_station = "Dtc De Huet"
                
            v_tijd = leg['origin']['plannedDateTime'][11:16]

            # Ophalen spoorinfo
            v_gepland = leg['origin'].get('plannedTrack', '?')
            v_actueel = leg['origin'].get('actualTrack', v_gepland)
            
            # Check of het vertrekspoor is gewijzigd (zo ja, maak het rood)
            if v_gepland != v_actueel:
                spoor_tekst = f"<span style='color: red; font-weight: bold;'>{v_actueel}</span> (was {v_gepland})"
            else:
                spoor_tekst = f"<span class='spoor'>{v_actueel}</span>"
            
            # --- AANKOMST INFO ---
            a_station = leg['destination']['name']
            a_tijd = leg['destination']['plannedDateTime'][11:16]
            
            # Voeg dit specifieke ritje toe aan de HTML
            html_content += f"""
            <li style="background: #f4f4f4; padding: 5px 0; margin-bottom: 5px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; border-left: none; border-right: none;">
                <b>{v_station}</b><span> - {spoor_tekst} - </span><b>{vervoer}</b><br>
                <span class="vertrek">{v_tijd} - {a_tijd}</span>
            </li>
            """
            
    # Sluit de reis netjes af
    html_content += """
        </ul>
    </li>
    """

# 5. Sla dit op als de HTML pagina die we online gaan zetten
with open("info.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("HTML succesvol gebouwd!")
