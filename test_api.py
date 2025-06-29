import requests

url = "https://www.helpslot.win/api/games?name=golden+empire&requestFrom=H5"
headers = {
    "Accept": "application/json",
    "Referer": "https://www.helpslot.win/",
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
data = response.json()

# Print the full JSON response (nicely formatted)
import json
print(json.dumps(data, indent=2))

# Or just print all game IDs and names
for game in data.get("data", []):
    print(f"{game['id']}: {game['name']}")
