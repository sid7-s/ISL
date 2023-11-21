import pandas as pd
import random
import ast

# Replace with the path to your CSV file
csv_file_path = 'match_details.csv'

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)

# Function to simulate a match
def simulate_match(xg_a, xg_b):
    goals_a = sum(1 for xg in xg_a if random.randint(1, 100) <= float(xg) * 100)
    goals_b = sum(1 for xg in xg_b if random.randint(1, 100) <= float(xg) * 100)
    return goals_a, goals_b

# Function to calculate xPoints from simulation results
def calculate_xpoints_from_simulation(xg_a, xg_b, simulations=10000):
    points_a, points_b = 0, 0
    for _ in range(simulations):
        goals_a, goals_b = simulate_match(xg_a, xg_b)
        if goals_a > goals_b:
            points_a += 3
        elif goals_a < goals_b:
            points_b += 3
        else:
            points_a += 1
            points_b += 1
    return points_a / simulations, points_b / simulations

# Apply the simulation to each match
df['Team A xG'] = df['Team A xG'].apply(ast.literal_eval)
df['Team B xG'] = df['Team B xG'].apply(ast.literal_eval)
df['Team A xPoints'], df['Team B xPoints'] = zip(*df.apply(lambda row: calculate_xpoints_from_simulation(row['Team A xG'], row['Team B xG']), axis=1))

import pandas as pd

# Assuming df is your DataFrame with the matches, xPoints, and actual points

# Initialize a dictionary to store the total points and xPoints for each team
teams_points = {}

# Process each match in the DataFrame
for index, row in df.iterrows():
    team_a = row['Team A']
    team_b = row['Team B']
    points_a = row['Team A Points']
    points_b = row['Team B Points']
    xpoints_a = row['Team A xPoints']
    xpoints_b = row['Team B xPoints']

    # Initialize team records in the dictionary if not already present
    if team_a not in teams_points:
        teams_points[team_a] = {'Points': 0, 'xPoints': 0}
    if team_b not in teams_points:
        teams_points[team_b] = {'Points': 0, 'xPoints': 0}

    # Add actual points and xPoints to the respective teams' totals
    teams_points[team_a]['Points'] += points_a
    teams_points[team_a]['xPoints'] += xpoints_a
    teams_points[team_b]['Points'] += points_b
    teams_points[team_b]['xPoints'] += xpoints_b

# Convert the dictionary to a DataFrame
points_table = pd.DataFrame([(team, data['Points'], data['xPoints']) for team, data in teams_points.items()], columns=['Team', 'Points', 'xPoints'])

# Sort the teams first by actual Points (highest first) and then by xPoints (highest first)
points_table = points_table.sort_values(by=['Points', 'xPoints'], ascending=[False, False]).reset_index(drop=True)

# Display the points table
print(points_table)
