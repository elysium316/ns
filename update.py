import os
import requests
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# NS API
ns_key = os.environ.get("NS_API_KEY")

# tijdzone
nl_tijdzone = ZoneInfo("Europe/Amsterdam")
tijd_nu = datetime.now(nl_tijdzone)
tijd_zoeken = tijd_nu - timedelta(hours=1, minutes=30)
ns_tijd = tijd_zoeken.strftime('%Y-%m-%dT%H:%M:%S')
tijd_vis = tijd_nu.strftime('%H:%M')
print(f"{tijd_zoeken}, {ns_tijd}, {tijd_vis}")

# OPVRAGEN
url = f"https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips?fromStation=ASDZ&toStation=RTD&dateTime={ns_tijd}"
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
        body {{ font-family: sans-serif; background: #fff; color: #000; }}
        h1 {{ font-size: 45px; margin: 0; color: #003399; }}
        .tijd {{ font-size: 60px; font-weight:bold; color: black; margin-bottom: 15px; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #ccc; }}
        .vertrek {{ font-weight: bold; font-size: 72px; }}
        .spoor {{ color: blue; font-weight: bold; font-size:45px;}}
        .status {{ color: black; font-size: 50px; font-weight: bold}}
        .station {{color:black; font-size:35pt; font-weight: bold}}
    </style>
</head>
<body style="margin:2pt;padding:2pt;">
    <h1>Leiden C.</h1>
    <h1>Dtc DH</h1>
    
    
    <h1>test 8</h1>

    
    <div class="tijd">{tijd_vis}</div>
    <ul>
"""

for trip in data.get('trips', [])[:10]: # Toon max 4 reizen
    status = trip.get('status', 'ONBEKEND')

    if status == "NORMAL":
        status = "NORMAL"
    else:
        status = f"<span style='color: red;'>{status}</span>"
    
    # Begin een overkoepelend blok voor één complete reis (van A naar B)
    html_content += f"""
    <li style="margin-bottom: 15px; border-bottom: 2px solid #003399; padding-bottom: 10px;">
        <div class="status">{status}</div>
        <ul style="list-style-type: none; padding-left: 0; margin: 0;">
    """
    
    # Loop nu door alle afzonderlijke voertuigen/overstappen (legs) van DEZE reis
    for leg in trip.get('legs', []):
        if leg.get('travelType') == 'PUBLIC_TRANSIT':
            vervoer = leg['product']['shortCategoryName'] # Bijv. IC, SPR of BUS
            if vervoer == "TRAIN":
                vervoer = "ST"
                
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

            # Spoor (met wijzigings-check)
            v_gepland_spoor = leg['origin'].get('plannedTrack', '?')
            v_actueel_spoor = leg['origin'].get('actualTrack', v_gepland_spoor)
            if v_gepland_spoor != v_actueel_spoor:
                spoo'origin'r_tekst = f"<span style='color: red; font-weight: bold;'>{v_actueel_spoor}</span>"
            else:
                spoor_tekst = f"<span class='spoor'>{v_actueel_spoor}</span>"
                
            a_gepland_spoor = leg['destination'].get('plannedTrack', '?')
            a_actueel_spoor = leg['destination'].get('actualTrack', a_gepland_spoor)
            if a_gepland_spoor != a_actueel_spoor:
                a_spoor_tekst = f"<span style='color: red; font-weight: bold;'>{a_actueel_spoor}</span>"
            else:
                a_spoor_tekst = f"<span class='spoor'>{a_actueel_spoor}</span>"
            
            # --- AANKOMST INFO ---
            a_station = leg['destination']['name']
            a_station = a_station.replace(" Centraal", " C.") # Kort de naam af
            
            # Aankomsttijd (met vertragings-check)
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
            
            # Voeg dit specifieke ritje toe aan de HTML
            html_content += f"""
            <li style="background: #f4f4f4; padding: 5px 0; margin-bottom: 5px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; border-left: none; border-right: none;">
                <span class="station">{v_station}</span><br>
                <span class="spoor" style="color:black;">{vervoer}: </span><span class="spoor">{spoor_tekst} - {a_spoor_tekst}</span><br>
                <span class="vertrek">{v_tijd}</span><br>
                <span class="vertrek">{a_tijd}</span>
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
