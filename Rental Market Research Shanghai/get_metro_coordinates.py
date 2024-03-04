import requests
import json

# Define the API endpoint URL
url = "https://map.amap.com/service/subway?_1568752521231&srhdata=3100_drw_shanghai.json"

# Send a GET request to the API endpoint
response = requests.get(url)

# Parse the JSON response
data = response.json()

# Extract the station names and coordinates
stations = []
for line in data['l']:
    for station in line['st']:
        name = station['n']
        lng, lat = station['sl'].split(',')
        lines = []
        for ln in data['l']:
            if name in [s['n'] for s in ln['st']]:
                lines.append(ln['ln'])
        stations.append({'name': name, 'lng': float(lng), 'lat': float(lat), 'lines': list(set(lines))})


# Save data to a JSON file
with open('sh_metro_stations.json', 'w') as json_file:
    json.dump(stations, json_file)