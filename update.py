import os
import requests
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# NS API
ns_key = os.environ.get("NS_API_KEY")
url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips"
headers = {"Ocp-Apim-Subscription-Key": ns_key}

nl_tijdzone = ZoneInfo("Europe/Amsterdam")
tijd_nu = datetime.now(nl_tijdzone)
tijd_vis = tijd_nu.strftime('%H:%M')

# ---------------------------------------------------------
# AANVRAAG 1: Vanaf half uurtje geleden
# ---------------------------------------------------------
tijd_zoeken_1 = tijd_nu - timedelta(hours=1,minutes=30)
ns_tijd_1 = tijd_zoeken_1.isoformat(timespec='seconds')

params_1 = {
    "fromStation": "LEDN", # Leiden Centraal
    "toStation": "DTCH",    # Doetinchem De Huet
    "dateTime": ns_tijd_1
}

response_1 = requests.get(url, headers=headers, params=params_1)

if response_1.status_code != 200:
    print(f"Fout bij aanvraag 1: {response_1.status_code} - {response_1.text}")
    exit(1)

data_1 = response_1.json()

# Haal de lijst met reizen uit het eerste antwoord
trips_1 = data_1.get('trips', [])

# ---------------------------------------------------------
# AANVRAAG 2: Voor de reizen die daarna komen
# ---------------------------------------------------------
# We kijken naar de geplande vertrektijd van de LAATSTE reis uit aanvraag 1
# Als we geen reizen hebben gevonden, zoeken we gewoon 2 uur in de toekomst.
if len(trips_1) > 0:
    # Pak de vertrektijd van de eerste 'leg' van de laatste 'trip'
    laatste_vertrek_str = trips_1[-1]['legs'][0]['origin']['plannedDateTime']
    # Zet de string om naar een datetime object en tel er 1 minuut bij op
    # (zodat we de laatste reis niet nog een keer opvragen)
    laatste_vertrek = datetime.strptime(laatste_vertrek_str[:19], "%Y-%m-%dT%H:%M:%S")
    laatste_vertrek = laatste_vertrek.replace(tzinfo=nl_tijdzone)
    tijd_zoeken_2 = laatste_vertrek + timedelta(minutes=1)
else:
    tijd_zoeken_2 = tijd_nu # + timedelta(hours=2)

ns_tijd_2 = tijd_zoeken_2.isoformat(timespec='seconds')

params_2 = {
    "fromStation": "LEDN",
    "toStation": "DTCH",
    "dateTime": ns_tijd_2
}

response_2 = requests.get(url, headers=headers, params=params_2)

if response_2.status_code != 200:
    print(f"Fout bij aanvraag 2: {response_2.status_code} - {response_2.text}")
    exit(1)

data_2 = response_2.json()

# Haal de lijst met reizen uit het tweede antwoord
trips_2 = data_2.get('trips', [])

# ---------------------------------------------------------
# SAMENVOEGEN
# ---------------------------------------------------------
# Plak de twee lijsten met reizen aan elkaar
alle_trips = trips_1 + trips_2

# Optioneel: Haal dubbele reizen eruit (soms overlappen API resultaten)
# We gebruiken de 'checksum' of unieke combinatie van vertrektijd om dubbelen te filteren.
unieke_trips = []
geziene_vertrektijden = set()

for trip in alle_trips:
    if len(trip.get('legs', [])) > 0:
        vertrek = trip['legs'][0]['origin']['plannedDateTime']
        if vertrek not in geziene_vertrektijden:
            unieke_trips.append(trip)
            geziene_vertrektijden.add(vertrek)

# 'unieke_trips' bevat nu je gecombineerde lijst (waarschijnlijk zo'n 8 tot 12 reizen)
print(f"Totaal aantal unieke reizen gevonden: {len(unieke_trips)}")

# 3. Begin met het bouwen van de HTML pagina (ZONDER Javascript)
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Leiden C. - Doetinchem de Huet</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; background: #fff; color: #000; }}
        h1 {{ font-size: 45px; margin: 0; color: #003399; }}
        .tijd {{ font-size: 60px; font-weight:bold; color: black; margin-bottom: 15px; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #ccc; }}
        .vertrek {{ font-weight: bold; font-size: 72px; }}
        .spoor {{ color: blue; font-weight: bold; font-size:50px;}}
        .status {{ color: black; font-size: 50px; font-weight: bold}}
        .station {{color:black; font-size:33pt; font-weight: bold}}
    </style>
</head>
<body style="margin:2pt;padding:2pt;">
    <h1>Leiden C.</h1>
    <h1>Dtc DH</h1>
    <div class="tijd">{tijd_vis}</div>
    <ul>
"""
for trip in unieke_trips[:10]: 
    status = trip.get('status', 'ONBEKEND')
    if status == "NORMAL":
        status = "NORMAL"
    else:
        status = f"<span style='color: red;'>{status}</span>"
    
    # Begin het overkoepelende blok voor één complete reis
    html_content += f"""
    <li style="margin-bottom: 10px; border-bottom: 10px solid #003399; padding-bottom: 10px;">
        <div class="status">{status}</div>
        <ul style="list-style-type: none; padding-left: 0; margin: 0;">
    """
    
    # Loop nu door alle afzonderlijke voertuigen/overstappen (legs) van DEZE reis
    for leg in trip.get('legs', []):
        if leg.get('travelType') == 'PUBLIC_TRANSIT':
            vervoer = leg['product']['shortCategoryName'] # Bijv. IC, SPR of BUS
            if vervoer == "TRAIN":
                vervoer = "ST"

            # CANCELLED
            is_cancelled = leg.get('cancelled', False)
            is_part_cancelled = leg.get('partCancelled', False)
            if is_cancelled:
                bg_color = "#ffcccc" # Duidelijk rood voor volledig vervallen
            elif is_part_cancelled:
                bg_color = "#ffe6cc" # Duidelijk oranje voor deels vervallen
            else:
                bg_color = "#f4f4f4" # Standaard grijs
                
            # NAAMGEVING
            v_station = leg['origin']['name']
            if v_station == "Leiden Centraal":
                v_station = "Leiden C."
            elif v_station == "Utrecht Centraal":
                v_station = "Utrecht C."
            elif v_station == "Arnhem Centraal":
                v_station = "Arnhem C."
            elif v_station == "Doetinchem De Huet":
                v_station = "Dtc De Huet"
            
            # Spoorinfo vertrek
            v_gepland_spoor = leg['origin'].get('plannedTrack', '?')
            v_actueel_spoor = leg['origin'].get('actualTrack', v_gepland_spoor)

            # Spoorwijziging
            if v_gepland_spoor != v_actueel_spoor:
                spoor_tekst = f"<span style='color: red; font-weight: bold;'>{v_actueel_spoor}</span>"
            else:
                spoor_tekst = f"<span class='spoor'>{v_actueel_spoor}</span>"

            # Vertrek vertraging
            v_gepland_str = leg['origin']['plannedDateTime']
            v_actueel_str = leg['origin'].get('actualDateTime', v_gepland_str)
            v_gepland_tijd = v_gepland_str[11:16]
            if v_gepland_str != v_actueel_str:
                pt = datetime.strptime(v_gepland_str[:19], "%Y-%m-%dT%H:%M:%S")
                at = datetime.strptime(v_actueel_str[:19], "%Y-%m-%dT%H:%M:%S")
                delay_min = int((at - pt).total_seconds() / 60)
                if delay_min > 0:
                    v_tijd = f"{v_gepland_tijd}<span style='color: red; font-weight: bold;'>{delay_min}</span>"
                else:
                    v_tijd = v_gepland_tijd
            else:
                v_tijd = v_gepland_tijd
            
            # Info aankomst spoor         
            a_gepland_spoor = leg['destination'].get('plannedTrack', '?')
            a_actueel_spoor = leg['destination'].get('actualTrack', a_gepland_spoor)
            if a_gepland_spoor != a_actueel_spoor:
                a_spoor_tekst = f"<span style='color: red; font-weight: bold;'>{a_actueel_spoor}</span>"
            else:
                a_spoor_tekst = f"<span class='spoor'>{a_actueel_spoor}</span>"
        
            # Vertraging aankomst
            a_gepland_str = leg['destination']['plannedDateTime']
            a_actueel_str = leg['destination'].get('actualDateTime', a_gepland_str)
            a_gepland_tijd = a_gepland_str[11:16]
            if a_gepland_str != a_actueel_str:
                pt = datetime.strptime(a_gepland_str[:19], "%Y-%m-%dT%H:%M:%S")
                at = datetime.strptime(a_actueel_str[:19], "%Y-%m-%dT%H:%M:%S")
                delay_min = int((at - pt).total_seconds() / 60)
                if delay_min > 0:
                    a_tijd = f"{a_gepland_tijd}<span style='color: red; font-weight: bold;'>{delay_min}</span>"
                else:
                    a_tijd = a_gepland_tijd
            else:
                a_tijd = a_gepland_tijd
            
            # Toevoegen
            html_content += f"""
            <li style="background: {bg_color}; padding: 5px 0; margin-bottom: 5px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; border-left: none; border-right: none;">
                <span class="station">{v_station}</span><br>
                <span class="spoor" style="color:black;">{vervoer}: </span><span class="spoor">{spoor_tekst}</span><span class="spoor" style="color:black;"> - </span><span class="spoor">{a_spoor_tekst}</span><br>
                <span class="vertrek">{v_tijd}</span><br>
                <span class="vertrek">{a_tijd}</span>
            </li>
            """
    html_content += """
        </ul>
    </li>
    """
with open("ld.html", "w", encoding="utf-8") as f:
    f.write(html_content)
