import requests

resp = requests.get("http://127.0.0.1:8000/api/leaderboard?limit=5")
print("Status:", resp.status_code)
print("Body:", resp.text)