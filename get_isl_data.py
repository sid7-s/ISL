#import the necessary libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
import pandas as pd
import requests

#Function 1 - To create a web driver
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # loading the browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=chrome_options)
    return driver


# Function 2 - To extract all Match IDs which is required for the API requests
def get_match_id_list(driver, league_url):
    driver.get(league_url)
    # Get all the match divs for that page
    all_links_elements = driver.find_elements(By.TAG_NAME, "a")
    all_links = [link.get_attribute("href") for link in all_links_elements]
    all_links
    pattern = r"https://www.fotmob.com/en-GB/matches/*"
    match_links = [elem for elem in all_links if re.match(pattern, elem)]
    match_ids = []
    # extract all match_ids from the match_url
    for link in match_links:
        match_id = link.split('/')[-1].split('#')[-1]
        match_ids.append(match_id)

    return match_ids


# Function 3 - To get all the match stats for a particular match ID
def get_match_stats(match_id):
    url = f'https://www.fotmob.com/api/matchDetails?matchId={match_id}'
    response = requests.get(url)
    json_data = response.json()

    # Extract match ID
    match_id = json_data['general']['matchId']

    # Extract team information from the 'lineup' section
    lineup_data = json_data['content']['lineup'].get('lineup', [])
    team_id_name_dict = {item.get('teamId'): item.get('teamName') for item in lineup_data if
                         item.get('teamId') and item.get('teamName')}

    # Extract the shots data
    shots_data = json_data['content']['shotmap']['shots']

    # Create a DataFrame from the shots data
    shots_df = pd.DataFrame(
        [{'teamId': shot.get('teamId'), 'expectedGoals': shot.get('expectedGoals')} for shot in shots_data])

    # Group by 'teamId' and keep individual expected goals
    grouped_shots_df = shots_df.groupby('teamId')['expectedGoals'].apply(list).reset_index()

    # Extract actual score from the 'header' section
    header_teams_data = json_data['header']['teams']
    team_scores = {team['id']: team['score'] for team in header_teams_data}

    # Determine points based on actual score
    def assign_points(score_a, score_b):
        if score_a > score_b:
            return 3, 0
        elif score_a < score_b:
            return 0, 3
        else:
            return 1, 1

    # Identify Team A and Team B
    teams = list(grouped_shots_df['teamId'])
    team_a_id = teams[0] if teams else None
    team_b_id = teams[1] if len(teams) > 1 else None

    # Calculate actual points for each team
    team_a_points, team_b_points = assign_points(team_scores.get(team_a_id, 0), team_scores.get(team_b_id, 0))

    # Construct the row for this match
    match_row = {
        'Match ID': match_id,
        'Team A': team_id_name_dict.get(team_a_id),
        'Team A xG': grouped_shots_df[grouped_shots_df['teamId'] == team_a_id]['expectedGoals'].iloc[
            0] if team_a_id else [],
        'Team A Points': team_a_points,
        'Team B': team_id_name_dict.get(team_b_id),
        'Team B xG': grouped_shots_df[grouped_shots_df['teamId'] == team_b_id]['expectedGoals'].iloc[
            0] if team_b_id else [],
        'Team B Points': team_b_points
    }

    return match_row

#Function 4 - To get all stats for all the matches
def get_season_stats(league_url):
    # Create an empty DataFrame to hold the data
    all_matches_data = []
    match_ids = get_match_id_list(get_driver(),league_url)
    print(match_ids)
    # Loop through each match ID
    for match_id in match_ids:
        try:
            # Make the API call and extract the desired stats
            match_stats = get_match_stats(match_id)
            # Append the stats for this match to the DataFrame
            all_matches_data.append(match_stats)
        except:
            print("Could not get stats for", match_id)
    final_df = pd.DataFrame(all_matches_data)
    return final_df


#Call the function to get the stats for the whole season
url = "https://www.fotmob.com/en-GB/leagues/9478/matches/super-league/by-round?page=0"
stats_data = get_season_stats(url)

url = "https://www.fotmob.com/en-GB/leagues/9478/matches/super-league/by-round?page=1"
stats_data = pd.concat([stats_data, get_season_stats(url)], ignore_index=True)

url = "https://www.fotmob.com/en-GB/leagues/9478/matches/super-league/by-round?page=2"
stats_data = pd.concat([stats_data, get_season_stats(url)], ignore_index=True)

url = "https://www.fotmob.com/en-GB/leagues/9478/matches/super-league/by-round?page=3"
stats_data = pd.concat([stats_data, get_season_stats(url)], ignore_index=True)

stats_data.to_csv('match_details.csv', index=False)
