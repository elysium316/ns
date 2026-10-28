import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- INSTELLINGEN ---
ns_key = os.environ.get("NS_API_KEY")
url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v3/trips"
headers = {"Ocp-Apim-Subscription-Key": ns_key}

nl_tijdzone = ZoneInfo("Europe/Amsterdam")
tijd_nu = datetime.now(nl_tijdzone)
tijd_vis = tijd_nu.strftime('%H:%M')
# We zoeken vanaf een half uurtje geleden, zodat we ook treinen zien die nét weg zijn
tijd_zoeken = (tijd_nu - timedelta(minutes=30)).isoformat(timespec='seconds')

# ---------------------------------------------------------
# 1. DE 3 TRAJECTEN DEFINIËREN & OPHALEN
# ---------------------------------------------------------
# Dit is onze matrix met de 3 losse etappes
etappes = [
    {"naam": "Leiden C. ➔ Utrecht C.", "van": "LEDN", "naar": "UT"},
    {"naam": "Utrecht C. ➔ Arnhem C.", "van": "UT", "naar": "AH"},
    {"naam": "Arnhem C. ➔ Dtc De Huet", "van": "AH", "naar": "DTCH"}
]

# We gaan de opgehaalde reizen hier in opslaan
alle_data_bakjes = []

for etappe in etappes:
    params = {
        "fromStation": etappe["van"],
        "toStation": etappe["naar"],
        "dateTime": tijd_zoeken,
        # nextAdvices laten we weg, NS geeft er standaard ~5, wat perfect is per etappe.
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Fout bij aanvraag {etappe['naam']}: {response.status_code} - {response.text}")
        # Bij een fout stoppen we niet het hele script, maar maken we er een lege lijst van
        alle_data_bakjes.append({"etappe_naam": etappe["naam"], "trips": []})
    else:
        data = response.json()
        trips = data.get('trips', [])
        alle_data_bakjes.append({"etappe_naam": etappe["naam"], "trips": trips})

# ---------------------------------------------------------
# 2. HTML OPBOUWEN
# ---------------------------------------------------------
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Route: Leiden - Doetinchem</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: sans-serif; background: #fff; color: #000; margin:2pt; padding:2pt; }}
        h1 {{ font-size: 45px; margin: 0; color: #003399; }}
        .tijd {{ font-size: 60px; font-weight:bold; color: black; margin-bottom: 15px; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        li {{ padding: 10px 0; }}
        .vertrek {{ font-weight: bold; font-size: 72px; }}
        .spoor {{ color: blue; font-weight: bold; font-size: 50px; }}
        .status {{ color: black; font-size: 50px; font-weight: bold; }}
        .station {{ color: black; font-size: 33pt; font-weight: bold; }}
        .etappe-header {{ background: #ffc917; color: #003399; padding: 10px; font-size: 50px; font-weight: bold; margin-top: 30px; margin-bottom: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Leiden C.</h1>
    <h1>Dtc DH</h1>
    <div class="tijd">{tijd_vis}</div>
"""

# Loop door de 3 opgehaalde bakjes (etappes) heen
for bakje in alle_data_bakjes:
    etappe_naam = bakje["etappe_naam"]
    trips = bakje["trips"]
    
    # Maak een dikke gele header voor dit specifieke traject
    html_content += f"""
    <div class="etappe-header">{etappe_naam}</div>
    <ul style="border-bottom: 10px solid #003399; padding-bottom: 10px; margin-bottom: 20px;">
    """
    
    # Als er geen treinen zijn gevonden (storing of API fout)
    if not trips:
        html_content += "<li style='font-size: 40px; color: red; font-weight: bold;'>Geen reizen gevonden voor dit traject.</li>"
    
    # Pak maximaal de eerste 5 opties per etappe (zodat de pagina niet oneindig lang wordt)
    for trip in trips[:5]: 
        status = trip.get('status', 'ONBEKEND')
        if status == "NORMAL":
            status = "" # Bij normaal verbergen we de tekst om het strak te houden
        else:
            status = f"<span style='color: red;'>{status}</span><br>"
        
        # Loop door alle afzonderlijke voertuigen/overstappen van DEZE specifieke rit 
        # (Meestal is dit er maar 1, omdat we per los traject zoeken, maar bijv. bij een bus-omleiding kunnen het er meer zijn)
        for leg in trip.get('legs', []):
            if leg.get('travelType') == 'PUBLIC_TRANSIT':
                vervoer = leg['product']['shortCategoryName']
                if vervoer == "TRAIN":
                    vervoer = "ST"

                # CANCELLED
                is_cancelled = leg.get('cancelled', False)
                is_part_cancelled = leg.get('partCancelled', False)
                if is_cancelled:
                    bg_color = "#ffcccc" # Rood voor volledig vervallen
                elif is_part_cancelled:
                    bg_color = "#ffe6cc" # Oranje voor deels vervallen
                else:
                    bg_color = "#f4f4f4" # Standaard grijs
                    
                # NAAMGEVING
                v_station = leg['origin']['name']
                if v_station == "Leiden Centraal": v_station = "Leiden C."
                elif v_station == "Utrecht Centraal": v_station = "Utrecht C."
                elif v_station == "Arnhem Centraal": v_station = "Arnhem C."
                elif v_station == "Doetinchem De Huet": v_station = "Dtc De Huet"
                
                # Spoorinfo vertrek
                v_gepland_spoor = leg['origin'].get('plannedTrack', '?')
                v_actueel_spoor = leg['origin'].get('actualTrack', v_gepland_spoor)

                # Spoorwijziging vertrek
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
                        v_tijd = f"{v_gepland_tijd}<span style='color: red; font-weight: bold;'>+{delay_min}</span>"
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
                        a_tijd = f"{a_gepland_tijd}<span style='color: red; font-weight: bold;'>+{delay_min}</span>"
                    else:
                        a_tijd = a_gepland_tijd
                else:
                    a_tijd = a_gepland_tijd
                
                # Toevoegen van de rit aan de HTML
                html_content += f"""
                <li style="background: {bg_color}; padding: 5px 0; margin-bottom: 10px; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd; border-left: none; border-right: none;">
                    {status}
                    <span class="station">{v_station}</span><br>
                    <span class="spoor" style="color:black;">{vervoer}: </span><span class="spoor">{spoor_tekst}</span><span class="spoor" style="color:black;"> - </span><span class="spoor">{a_spoor_tekst}</span><br>
                    <span class="vertrek">{v_tijd}</span><br>
                    <span class="vertrek">{a_tijd}</span>
                </li>
                """
    
    # Sluit de lijst van deze etappe af
    html_content += """
    </ul>
    """

# Sluit het hele document af
html_content += """
</body>
</html>
"""

with open("ld.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Succes! HTML opgebouwd uit 3 aparte trajecten.")
