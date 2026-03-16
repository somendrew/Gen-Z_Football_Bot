import requests
from datetime import date, timedelta
from config import FOOTBALL_KEY

LEAGUES = {
    "PL": "Premier League",
    "CL": "UEFA Champions League",
}

def get_finished_matches():
    headers  = {"X-Auth-Token": FOOTBALL_KEY}
    today    = str(date.today())
    tomorrow = str(date.today() + timedelta(days=1))

    try:
        url = (
            f"https://api.football-data.org/v4/matches"
            f"?dateFrom={today}&dateTo={tomorrow}"
            f"&status=FINISHED&competitions=PL,CL"
        )
        r = requests.get(url, headers=headers, timeout=10)
        print(f"API status code: {r.status_code}", flush=True)
        r.raise_for_status()

        matches = r.json().get("matches", [])
        results = []
        for m in matches:
            comp_code = m.get("competition", {}).get("code", "")
            comp_name = LEAGUES.get(comp_code)
            if comp_name:
                results.append((comp_name, m))

        print(f"Finished PL/CL matches today: {len(results)}", flush=True)
        return results

    except Exception as e:
        print(f"Error fetching matches: {e}", flush=True)
        return []