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
        logging.StreamHandler()  # Console output
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
    matches = soup.find_all(class_='betting-main-dashboard')   # where all the matches are found
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
    target_elements = soup.find_all('div', class_='ui-game-scores--size-m ui-game-scores--theme-gray-100 ui-game-scores')
    games = []
    i = 0
    while i < len(target_elements):
        try:
            team1_scores = [span.get_text(strip=True) for span in target_elements[i].find_all('span', class_='ui-game-scores--size-m ui-game-scores--theme-gray-100 ui-game-scores')]
            team2_scores = [span.get_text(strip=True) for span in target_elements[i + 1].find_all('span', class_='ui-game-scores--size-m ui-game-scores--theme-gray-100 ui-game-scores')]

            if not team1_scores:
                team1_scores = ["0"]
            if not team2_scores:
                team2_scores = ["0"]

            team1 = {
                'total_score': team1_scores[0],
                'quarters': team1_scores[1:] if len(team1_scores) > 1 else ["No data"]
            }
            team2 = {
                'total_score': team2_scores[0],
                'quarters': team2_scores[1:] if len(team2_scores) > 1 else ["No data"]
            }

            games.append((team1, team2))
            i += 2
        except IndexError:
            games.append((
                {'total_score': "0", 'quarters': ["No data"]},
                {'total_score': "0", 'quarters': ["No data"]}
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
                first_quarter_sum = sum(int(q) for q in team1.get('quarters', ['0'])[:1] + team2.get('quarters', ['0'])[:1] if q.isdigit())
                if first_quarter_sum < 50 and "2nd quarter" in timer.lower() and ("12:5" in timer or "13:0" in timer or "13:1" in timer or "16:5" in timer or "17:" in timer):
                    second_quarter_sum = sum(int(q) for q in team1.get('quarters', ['0'])[1:2] + team2.get('quarters', ['0'])[1:2] if q.isdigit())
                    estimated_2q_points = second_quarter_sum * 3.5
                    if estimated_2q_points < 29:
                        logger.info(f"{match} - First Team Total: {team1.get('total_score', 'No data')}, Quarters: {', '.join(team1.get('quarters', ['No data']))}")
                        logger.info(f"Second Team Total: {team2.get('total_score', 'No data')}, Quarters: {', '.join(team2.get('quarters', ['No data']))}")
                        logger.info(f"{timer}")
                        logger.info(f"Estimated midpoint pts: {second_quarter_sum}")
                        logger.info(f"Estimated 2Q pts: {estimated_2q_points}")
                        logger.info("-" * 40)

                        message = f"{match} | 2Q pts: OV{estimated_2q_points} "
                        #send_payload(message)

        time.sleep(10)

# Script entrypoint
if __name__ == "__main__":
    main()
