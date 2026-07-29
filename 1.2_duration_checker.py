import requests
from bs4 import BeautifulSoup

# URL of the website to scrape
url = "https://1xbet.global/en/live/basketball"

# Set headers to mimic a real browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

# Send a GET request to the website with headers
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Print the raw HTML content for debugging (optional)
    # print("Raw HTML content:")
    # print(response.text)  # Uncomment this if you want to see the full HTML response
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the section that contains the basketball match information
    timer = soup.find_all(class_='c-events-scoreboard__subitem')  # Check this class name

    # Check if any timers are found
    if not timer:
        print("No timers found. Check the class name or the website's structure.")
    else:
        # Loop through each match and extract the current quarter information
        for duration in timer:
            # Find the specific element that contains the current quarter info
            current_timer = duration.find(class_='c-events__time')  # Check this class name
            current_quarter = duration.find(class_='c-events__overtime')  # Find the quarter info
            
            # Check if the timer element exists
            if current_timer:
                # Extract text from the timer element and strip whitespace
                timer_text = current_timer.get_text(strip=True)

                # Extract text from the quarter element (if it exists)
                quarter_text = current_quarter.get_text(strip=True) if current_quarter else "No quarter info"

                if timer_text:  # Ensure it's not empty
                    # Print both timer and quarter information
                    print(f"Timer: {timer_text} | Quarter Status: {quarter_text}")
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
