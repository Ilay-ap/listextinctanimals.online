import json
import time
import urllib.request

time.sleep(2)

try:
    req = urllib.request.Request("http://127.0.0.1:8000/pt-br/global-map-data/")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print(f"Total Locations (Points): {data['statistics']['total_locations']}")
        print(
            f"Max Concentration per Country: {data['statistics']['max_concentration']}"
        )
except Exception as e:
    print(f"Error: {e}")
