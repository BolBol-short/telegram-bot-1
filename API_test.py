import httpx

ALADHAN_API = "https://api.aladhan.com/v1"
cities = ["Phnom Penh", "Battambang"]

for city in cities:
    params = {"city": city, "country": "Cambodia", "method": 3}
    res = httpx.get(
        ALADHAN_API + "/timingsByCity", 
        params=params,
        follow_redirects=True,
    )

    # Check BEFORE parsing — don't trust the response blindly
    if res.status_code != 200 or not res.text.strip():
        print(f"{city}: bad response (status {res.status_code}) — body: {res.text[:150]!r}")
        continue

    data = res.json()
    timings = data["data"]["timings"]
    hijri = data["data"]["date"]["hijri"]["date"]

    print(f"{city}  (Hijri {hijri})")
    for prayer in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        print(f"  {prayer:8} - {timings[prayer]}")
    print()