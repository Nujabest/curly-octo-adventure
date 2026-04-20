import requests

JOLPICA = "https://api.jolpi.ca/ergast/f1"


def jolpica_get(url, timeout=8):
    """GET request to Jolpica. Returns None on failure."""
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"[Jolpica] {url} → {e}")
        return None


def get_round_number(year, gp_name):
    """Find the round number for a GP name in a given year."""
    data = jolpica_get(f"{JOLPICA}/{year}.json")
    if not data:
        return None

    try:
        races = data["MRData"]["RaceTable"]["Races"]
        gp_lower = gp_name.lower()

        for race in races:
            if (
                gp_lower in race["raceName"].lower()
                or gp_lower
                in race["Circuit"].get("Location", {}).get("country", "").lower()
                or gp_lower in race["Circuit"].get("circuitName", "").lower()
            ):
                return int(race["round"])

        for race in races:
            loc = race["Circuit"].get("Location", {})
            if (
                gp_lower in loc.get("locality", "").lower()
                or gp_lower in loc.get("country", "").lower()
            ):
                return int(race["round"])
    except Exception:
        pass

    return None
