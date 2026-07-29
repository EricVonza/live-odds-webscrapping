import requests
from bs4 import BeautifulSoup
import time
import logging
import base64

# ------------------ LOGGING ------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------ CONFIG ------------------
_encoded_url = b'aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3JnL2JvdDc2NzMwNzIyODc6QUFFOHp3VW96Ykcxb051UEM3OURTUl k5NGJfT1doaDJXcDgvc2VuZE1lc3NhZ2U='
_encoded_room = b'LTAwMjE3MDM3NzM2OA=='

URL = "https://1xbet.global/en/live/basketball"
EPL_URL = base64.b64decode(_encoded_url).decode()
ROOM_ID = base64.b64decode(_encoded_room).decode()

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# ------------------ FETCH ------------------
def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.text
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return None

# ------------------ PARSE ------------------
def extract_games(html):
    soup = BeautifulSoup(html, 'html.parser')
    games = []

    match_blocks = soup.select('div[class*="dashboard"], div[class*="event"]')

    for block in match_blocks:
        try:
            teams = block.select('span.ui-caption')
            if len(teams) < 2:
                continue

            team1_name = teams[0].get_text(strip=True)
            team2_name = teams[1].get_text(strip=True)

            scores = [
                int(s.get_text(strip=True))
                for s in block.select('.ui-game-scores__num')
                if s.get_text(strip=True).isdigit()
            ]

            if len(scores) < 2:
                continue

            # totals
            t1_total = scores[0]
            t2_total = scores[1]

            # quarters
            quarter_scores = scores[2:]

            t1_quarters = []
            t2_quarters = []

            for i in range(0, len(quarter_scores), 2):
                if i + 1 < len(quarter_scores):
                    t1_quarters.append(quarter_scores[i])
                    t2_quarters.append(quarter_scores[i + 1])

            # TIMER + PERIOD
            time_block = block.select_one('.ui-game-timer, .scoreboard-timer, .event__stage')
            period_text = ""
            game_time = ""

            if time_block:
                txt = time_block.get_text(" ", strip=True)
                parts = txt.split()

                for part in parts:
                    if ":" in part:
                        game_time = part
                    elif "Q" in part.upper():
                        period_text = part.upper()

            games.append({
                "match": f"{team1_name} vs {team2_name}",
                "team1": {
                    "total": t1_total,
                    "quarters": t1_quarters
                },
                "team2": {
                    "total": t2_total,
                    "quarters": t2_quarters
                },
                "period": period_text,
                "time": game_time
            })

        except Exception:
            continue

    return games

# ------------------ TELEGRAM ------------------
def send_payload(message):
    try:
        requests.post(EPL_URL, data={
            'chat_id': ROOM_ID,
            'text': message
        })
    except Exception as e:
        logger.error(f"Telegram error: {e}")

# ------------------ MAIN ------------------
def main():
    alerted = set()
    last_heartbeat = time.time()

    while True:
        html = fetch_html(URL)

        if not html:
            logger.warning("❌ Failed to fetch HTML")
            time.sleep(5)
            continue

        # HEARTBEAT
        now = time.time()
        if now - last_heartbeat >= 15:
            logger.info("HTML fetched successfully")
            last_heartbeat = now

        games = extract_games(html)
        logger.info(f"Live games found: {len(games)}")

        for game in games:
            t1_q = game["team1"]["quarters"]
            t2_q = game["team2"]["quarters"]

            period = game.get("period", "")
            time_str = game.get("time", "")

            # 🐢 SLOW START (CHECK Q1 WHILE IN 2Q)
            if period == "2Q" and time_str.startswith("15:"):
                if len(t1_q) >= 1 and len(t2_q) >= 1:

                    q1_t1 = t1_q[0]
                    q1_t2 = t2_q[0]

                    if q1_t1 < 8 or q1_t2 < 8:
                        game_id = game["match"] + "_slow_start"

                        if game_id not in alerted:
                            alerted.add(game_id)

                            msg = f"{game['match']} | Slow start Q1: {q1_t1}-{q1_t2} (2Q 15:00)"

                            logger.info("🐢 SLOW START DETECTED")
                            logger.info(msg)
                            logger.info("-" * 40)

                            # send_payload(msg)

            # 🔥 LOW SCORING LOGIC (needs 2 completed quarters)
            if len(t1_q) < 2 or len(t2_q) < 2:
                continue

            prev_index = min(len(t1_q), len(t2_q)) - 2
            t1_prev = t1_q[prev_index]
            t2_prev = t2_q[prev_index]

            # exclude 0-0
            if (t1_prev < 14 or t2_prev < 14) and not (t1_prev == 0 and t2_prev == 0):
                game_id = game["match"]

                if game_id not in alerted:
                    alerted.add(game_id)

                    total_prev = t1_prev + t2_prev

                    # ⚠️ DISCLAIMER LOGIC
                    disclaimer = ""
                    if total_prev > 38:
                        disclaimer = " ⚠️ Low probability (high total quarter)"

                    # 🔮 PREDICTOR LOGIC
                    predicted_total = total_prev - 4

                    msg = (
                        f"{game['match']} | Low Q score: {t1_prev}-{t2_prev}"
                        f"{disclaimer} | 🔮 Predicted next Q total: {predicted_total}"
                    )

                    logger.info("Previous Low Scoring Quarter Detected")
                    logger.info(msg)
                    logger.info("-" * 40)

                    # send_payload(msg)

        time.sleep(10)

# ------------------ RUN ------------------
if __name__ == "__main__":
    main()