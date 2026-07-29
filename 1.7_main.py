import requests
from bs4 import BeautifulSoup
import time
import logging
import base64

#  Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

_encoded_url = b'aHR0cHM6Ly9hcGkudGVsZWdyYW0ub3JnL2JvdDc2NzMwNzIyODc6QUFFOHp3VW96Ykcxb051UEM3OURTUl k5NGJfT1doaDJXcDgvc2VuZE1lc3NhZ2U='
_encoded_room = b'LTAwMjE3MDM3NzM2OA=='

URL = "https://1xbet.global/en/live/basketball"
EPL_URL = base64.b64decode(_encoded_url).decode()
ROOM_ID = base64.b64decode(_encoded_room).decode()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'
}

# Track alerts to avoid duplicates
alerted_games = set()

#  Fetch HTML
def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        logger.info("Fetched HTML content successfully.")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data: {e}")
        return None

#  Extract Match Info
def extract_matches(html_content):
    soup = BeautifulSoup(html_content, 'html.parser') 
    matches = soup.find_all(class_='betting-main-dashboard')
    teams_list = []
    for idx, match in enumerate(matches, start=1):
        teams = match.find('span', class_='dashboard__champs')
        if teams:
            teams_text = teams.text.strip().replace("Including Overtime", "")
            teams_text = " ".join(teams_text.split())
            teams_list.append(f"Game {idx}: {teams_text}")
    return teams_list

# Extract Scores and Quarters
def extract_scores_and_quarters(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    target_elements = soup.find_all('div',class_='ui-game-scores--size-m ui-game-scores--theme-gray-100 ui-game-scores')

    games = []
    i = 0
    while i < len(target_elements):
        try:
            team1_scores = [span.get_text(strip=True) for span in target_elements[i].find_all('span')]
            team2_scores = [span.get_text(strip=True) for span in target_elements[i + 1].find_all('span')]

            if not team1_scores:
                team1_scores = ["0"]
            if not team2_scores:
                team2_scores = ["0"]

            team1 = {
                'total_score': team1_scores[0],
                'quarters': team1_scores[1:] if len(team1_scores) > 1 else []
            }
            team2 = {
                'total_score': team2_scores[0],
                'quarters': team2_scores[1:] if len(team2_scores) > 1 else []
            }

            games.append((team1, team2))
            i += 2

        except IndexError:
            games.append((
                {'total_score': "0", 'quarters': []},
                {'total_score': "0", 'quarters': []}
            ))
            i += 2

    return games

#  Extract Timer Info
def extract_timer(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    timer_elements = soup.find_all(class_='c-events-scoreboard__subitem')

    timers = []
    for timer in timer_elements:
        time_element = timer.find(class_='c-events__time')
        quarter_element = timer.find(class_='c-events__overtime')

        timer_text = time_element.get_text(strip=True) if time_element else "No timer info"
        quarter_text = quarter_element.get_text(strip=True) if quarter_element else "No quarter info"

        timers.append(f"Timer: {timer_text} | Quarter: {quarter_text}")

    if not timers:
        timers = ["Timer: No timer info | Quarter: No quarter info"]

    return timers

def send_payload(message):
    try:
        response = requests.post(
            EPL_URL,
            data={'chat_id': ROOM_ID, 'text': message}
        )
        if response.status_code == 200:
            logger.info("Payload sent successfully.")
        else:
            logger.error(f"Failed to send payload: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending payload: {e}")

#  Main Logic
def main():
    while True:
        html_content = fetch_html(URL)

        if html_content:
            matches = extract_matches(html_content)
            games = extract_scores_and_quarters(html_content)
            timers = extract_timer(html_content)

            max_len = max(len(matches), len(games), len(timers))
            matches += ["No match data"] * (max_len - len(matches))
            games += [({}, {})] * (max_len - len(games))
            timers += ["Timer: No timer info | Quarter: No quarter info"] * (max_len - len(timers))

            for match, (team1, team2), timer in zip(matches, games, timers):

                # Convert quarters safely
                t1_quarters = [int(q) for q in team1.get('quarters', []) if q.isdigit()]
                t2_quarters = [int(q) for q in team2.get('quarters', []) if q.isdigit()]

                game_id = match

                # =========================
                # 🔥 NEW LOGIC: LOW SCORE ALERT
                # =========================
                if t1_quarters and t2_quarters:
                    prev_q_index = min(len(t1_quarters), len(t2_quarters)) - 1

                    if prev_q_index >= 0:
                        t1_prev = t1_quarters[prev_q_index]
                        t2_prev = t2_quarters[prev_q_index]

                        if (t1_prev < 13 or t2_prev < 13) and game_id not in alerted_games:
                            logger.info("LOW SCORING ALERT 🚨")
                            logger.info(f"{match}")
                            logger.info(f"Previous Q Score -> Team1: {t1_prev}, Team2: {t2_prev}")
                            logger.info(f"{timer}")
                            logger.info("-" * 40)

                            message = f"{match} | Low scoring Q 🚨 ({t1_prev}-{t2_prev})"
                            #send_payload(message)

                            alerted_games.add(game_id)

                # =========================
                # EXISTING 2Q LOGIC
                # =========================
                first_quarter_sum = sum(
                    int(q) for q in team1.get('quarters', [])[:1] + team2.get('quarters', [])[:1]
                    if q.isdigit()
                )

                if first_quarter_sum < 50 and "2nd quarter" in timer.lower() and (
                    "12:5" in timer or "13:0" in timer or "13:1" in timer or
                    "16:5" in timer or "17:" in timer
                ):
                    second_quarter_sum = sum(
                        int(q) for q in team1.get('quarters', [])[1:2] + team2.get('quarters', [])[1:2]
                        if q.isdigit()
                    )

                    estimated_2q_points = second_quarter_sum * 3.5

                    if estimated_2q_points < 29:
                        logger.info(f"{match}")
                        logger.info(f"Team1 Total: {team1.get('total_score')} | Qs: {team1.get('quarters')}")
                        logger.info(f"Team2 Total: {team2.get('total_score')} | Qs: {team2.get('quarters')}")
                        logger.info(f"{timer}")
                        logger.info(f"Estimated 2Q pts: {estimated_2q_points}")
                        logger.info("-" * 40)

                        message = f"{match} | 2Q pts: OV{estimated_2q_points}"
                        #send_payload(message)

        time.sleep(10)

# Script entrypoint
if __name__ == "__main__":
    main()