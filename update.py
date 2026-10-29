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
tijd_zoeken = (tijd_nu - timedelta(minutes=30)).isoformat(timespec='seconds')

# ---------------------------------------------------------
# 1. DE 3 TRAJECTEN DEFINIËREN & OPHALEN
# ---------------------------------------------------------
etappes = [
    {"naam": "LEDN-UT", "van": "LEDN", "naar": "UT"},
    {"naam": "UT - AH", "van": "UT", "naar": "AH"},
    {"naam": "AH-DTCH", "van": "AH", "naar": "DTCH"}
]

alle_data_bakjes = []

for etappe in etappes:
    params = {
        "fromStation": etappe["van"],
        "toStation": etappe["naar"],
        "dateTime": tijd_zoeken,
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Fout bij aanvraag {etappe['naam']}: {response.status_code} - {response.text}")
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
    <title>Route: LEDN - DTCH</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ white-space: nowrap; font-family: sans-serif; background: #fff; color: #000; margin: 0; padding: 0; }}
        h1 {{ font-size: 45px; margin: 0; color: #003399; padding-left: 2pt; }}
        .tijd {{ font-size: 60px; font-weight: bold; color: black; margin-bottom: 5px; padding-left: 2pt; }}
        ul {{ list-style-type: none; padding: 0; margin: 0; }}
        .vertrek {{ font-weight: bold; font-size: 72px; }}
        .spoor {{ color: blue; font-weight: bold; font-size: 50px; }}
        .station {{ color: black; font-size: 30pt; font-weight: bold; }}
        .etappe-header {{ background: #ffc917; color: #003399; padding: 10px; font-size: 50px; font-weight: bold; margin: 20px 2pt 5px 2pt; border: 8px solid #003399; border-radius: 5px; }}
        
        .menu-link {{
            display: inline-block;
            background: #003399;
            color: white;
            padding: 15px 20px;
            margin: 5px 5px 15px 5px;
            text-decoration: none;
            font-size: 40px;
            font-weight: bold;
            border-radius: 10px;
        }}
    </style>
</head>
<body id="top">
    <h1>Test 6</h1>
    <div class="tijd">{tijd_vis}</div>
    <div style='padding: 2pt; margin-bottom: 20px;'>
"""

for bakje in alle_data_bakjes:
    etappe_naam_id = bakje["etappe_naam"].replace(" ", "")
    html_content += f"<a href='#{etappe_naam_id}' class='menu-link'>{bakje['etappe_naam']}</a> "

html_content += "</div>\n"

for bakje in alle_data_bakjes:
    etappe_naam = bakje["etappe_naam"]
    etappe_naam_id = etappe_naam.replace(" ", "")
    trips = bakje["trips"]
    
    html_content += f"""
    <div id='{etappe_naam_id}' class="etappe-header">{etappe_naam}</div>
    <ul>
    """
    
    if not trips:
        html_content += "<li style='font-size: 40px; color: red; font-weight: bold; padding: 10px;'>Geen reizen gevonden voor dit traject.</li>"
    
    for trip in trips[:5]: 
        status = trip.get('status', 'ONBEKEND')
        if status == "NORMAL":
            status_html = "" 
        else:
            status_html = f"<div style='color: red; font-size: 45px; font-weight: bold; margin-bottom: 5px;'>{status}</div>"
        
        # GELE LIJN: Scheidt de reisopties van elkaar
        html_content += f"""
        <li style="padding: 10px 0; border-bottom: 10px solid #ffc917;">
            {status_html}
            <ul>
        """
        
        for leg in trip.get('legs', []):
            if leg.get('travelType') == 'PUBLIC_TRANSIT':
                vervoer = leg['product']['shortCategoryName']
                if vervoer == "TRAIN":
                    vervoer = "ST"

                is_cancelled = leg.get('cancelled', False)
                is_part_cancelled = leg.get('partCancelled', False)
                if is_cancelled:
                    bg_color = "#ffcccc" 
                elif is_part_cancelled:
                    bg_color = "#ffe6cc" 
                else:
                    bg_color = "#f4f4f4" 
                    
                v_station = leg['origin'].get('stationCode', leg['origin']['name'])
                
                v_gepland_spoor = leg['origin'].get('plannedTrack', '?')
                v_actueel_spoor = leg['origin'].get('actualTrack', v_gepland_spoor)

                if v_gepland_spoor != v_actueel_spoor:
                    spoor_tekst = f"<span style='color: red; font-weight: bold;'>{v_actueel_spoor}</span>"
                else:
                    spoor_tekst = f"<span class='spoor'>{v_actueel_spoor}</span>"

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
                
                a_gepland_spoor = leg['destination'].get('plannedTrack', '?')
                a_actueel_spoor = leg['destination'].get('actualTrack', a_gepland_spoor)
                if a_gepland_spoor != a_actueel_spoor:
                    a_spoor_tekst = f"<span style='color: red; font-weight: bold;'>{a_actueel_spoor}</span>"
                else:
                    a_spoor_tekst = f"<span class='spoor'>{a_actueel_spoor}</span>"

                a_station = leg['destination'].get('stationCode', leg['destination']['name'])
                
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

                richting = leg.get('direction', 'Onbekend')
    
                richting_afkortingen = {
                    "Venlo": "VL",
                    "Ede-Wageningen": "ED",
                    "Arnhem Centraal": "AH",
                    "Winterswijk": "WW",
                    "Nijmegen": "NM",
                    "Utrecht Centraal": "UT",
                    "Den Haag Centraal": "GVC",
                    "Rotterdam Centraal": "RTD",
                    "Groningen": "GN",
                    "Drodrecht": "DD",
                    "Leeuwarden": "LW"
                }
                
                # Haal de eindbestemming op uit de API
                richting_voluit = leg.get('direction', 'Onbekend')
                
                # Check of we hier een afkorting voor hebben in ons lijstje
                richting = richting_afkortingen.get(richting_voluit, richting_voluit)
                
                html_content += f"""
                <li style="background: {bg_color}; padding: 5px 2px; margin: 0; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">
                    <span class="station">&#10230; {a_station} ({richting})</span><br>
                    <span class="spoor" style="color:black;">{vervoer}: </span><span class="spoor">{spoor_tekst}</span><span class="spoor" style="color:black;"> - </span><span class="spoor">{a_spoor_tekst}</span><br>
                    <span class="vertrek">{v_tijd}</span><br>
                    <span class="vertrek">{a_tijd}</span>
                </li>
                """
    
        html_content += """
            </ul>
        </li>
        """
        
    html_content += """
    </ul>
    <div style="text-align: right; margin-top: 10px; margin-bottom: 30px; padding-right: 15px;">
        <a href="#top" style="font-size: 35px; color: #003399; font-weight: bold; text-decoration: none;">↑ Terug naar menu</a>
    </div>
    """

html_content += """
</body>
</html>
"""

with open("ld.html", "w", encoding="utf-8") as f:
    f.write(html_content)
