import requests
from bs4 import BeautifulSoup

URL = "https://1xbet.global/en/live/basketball"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

# Fetch HTML Content
def fetch_html(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Parse and Extract Basketball Matches (Script 1 Logic)
def extract_matches(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    matches = soup.find_all(class_='c-events__name')
    teams_list = []
    for idx, match in enumerate(matches, start=1):
        teams = match.find('span', class_='c-events__teams')
        if teams:
            teams_text = teams.text.strip().replace("Including Overtime", "")
            teams_text = " ".join(teams_text.split())
            teams_list.append(f"Game {idx}: {teams_text}")
    return teams_list

# Parse and Extract Timers and Quarter Info (Script 2 Logic)
def extract_timers(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    timers = soup.find_all(class_='c-events-scoreboard__subitem')
    timer_list = []
    for timer in timers:
        current_timer = timer.find(class_='c-events__time')
        current_quarter = timer.find(class_='c-events__overtime')
        if current_timer:
            timer_text = current_timer.get_text(strip=True)
            quarter_text = current_quarter.get_text(strip=True) if current_quarter else "No quarter info"
            timer_list.append(f"Timer: {timer_text} | Quarter: {quarter_text}")
    return timer_list

# Main Function to Merge and Print Output
def main():
    html_content = fetch_html(URL)
    
    if html_content:
        matches = extract_matches(html_content)
        timers = extract_timers(html_content)
        
        # Handle mismatched lengths
        max_len = max(len(matches), len(timers))
        matches += ["No match data"] * (max_len - len(matches))
        timers += ["No timer data"] * (max_len - len(timers))
        
        # Merge and print line by line
        for match, timer in zip(matches, timers):
            print(f"{match} - {timer}")

if __name__ == "__main__":
    main()
