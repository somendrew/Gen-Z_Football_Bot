from dotenv import load_dotenv
import requests
from datetime import date, timedelta
import os

load_dotenv()
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY", "NOT SET")

LEAGUES = {
    "PL":  "Premier League",
    "CL":  "UEFA Champions League",
    "PD":  "La Liga",
    "SA":  "Serie A",
}

WATCHED_TEAMS = {
    "FC Barcelona",
    "Real Madrid CF",
    "Arsenal FC",
    "Manchester City FC",
    "Liverpool FC",
    "Manchester United FC",
    "Chelsea FC",
    "FC Bayern München",
    "Juventus FC",
    "AC Milan",
    "Inter Milan",
    "Atlético de Madrid",
}

def is_watched_match(match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    return home in WATCHED_TEAMS or away in WATCHED_TEAMS

def get_finished_matches():
    headers   = {"X-Auth-Token": FOOTBALL_KEY}
    today     = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    try:
        url = (
            f"https://api.football-data.org/v4/matches"
            f"?dateFrom={yesterday}&dateTo={today}"
            f"&status=FINISHED&competitions=PL,CL,PD,SA"
        )
        r = requests.get(url, headers=headers, timeout=10)
        print(f"API status code: {r.status_code}", flush=True)
        r.raise_for_status()

        matches = r.json().get("matches", [])
        results = []
        for m in matches:
            comp_code = m.get("competition", {}).get("code", "")
            comp_name = LEAGUES.get(comp_code)
            if comp_name and is_watched_match(m):
                results.append((comp_name, m))

        print(f"Finished PL/CL/La Liga/Serie A matches: {len(results)}", flush=True)
        return results

    except Exception as e:
        print(f"Error fetching matches: {e}", flush=True)
        return []