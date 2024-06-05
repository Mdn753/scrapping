import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def get_team_code(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    return path_parts[3]  # Assuming the team code is the 4th part of the path

def get_second_table_link(stats_link):
    team_code = get_team_code(stats_link)
    return f"https://fbref.com/en/squads/{team_code}/2023-2024/matchlogs/all_comps/passing/{team_code}-Match-Logs-All-Competitions"

def get_team_links(main_page_url, table_id):
    # Request the main page content
    req = requests.get(main_page_url)
    if req.status_code == 200:
        content = req.content
    else:
        raise Exception(f"Failed to retrieve content from {main_page_url}. Status code: {req.status_code}")

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find(id=table_id)
    
    if not table:
        raise Exception(f"Table with ID {table_id} not found.")
    
    team_links = {}
    rows = table.find_all("tr")
    
    for row in rows:
        team_cell = row.find('td', {'data-stat': 'team'})
        if team_cell:
            team_name = team_cell.get_text(strip=True)
            team_link = 'https://fbref.com' + team_cell.find('a')['href']
            team_links[team_name] = team_link
    
    return team_links

def scoresfixtures(team_links, output_folder='output'):
    '''
    Description: This function picks all the games in one season for multiple teams and saves the data to Excel files.
    
    Inputs:
        - team_links: A dictionary where keys are team names and values are the URLs to the team's stats page.
        - output_folder: The folder where the output Excel files will be saved (default is 'output').
        
    Outputs:
        - Excel files containing the data for each team.
    '''
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for team_name, stats_link in team_links.items():
        # Derive the match logs link from the stats link
        match_logs_link = get_second_table_link(stats_link)
        links_ids = {
            'Stats': (stats_link, 'div_matchlogs_for'),
            'Match Logs': (match_logs_link, 'div_matchlogs_for')
        }
        
        dataframes = {}
        
        for sheet_name, (link, ids) in links_ids.items():
            # Request the content of the webpage
            req = requests.get(link)
            if req.status_code == 200:
                content = req.content
            else:
                raise Exception(f"Failed to retrieve content from {link}. Status code: {req.status_code}")

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            tb = soup.find(id=ids)
            
            if not tb:
                raise Exception(f"Table with ID {ids} not found.")

            rows = tb.find_all("tr")
            data = []

            # Determine headers based on the sheet name
            if sheet_name == "Stats":
                headers = ["Date", "Time", "Comp", "Round", "Day", "Venue", "Result", 
                           "GF", "GA", "Opponent", "xG", "xGA", "Poss", "Attendance", 
                           "Captain", "Formation", "Referee", "Match Report", "Notes"]
            elif sheet_name == "Match Logs":
                headers = ["Date", "Time", "Comp", "Round", "Day", "Venue", "Result", 
                           "GF", "GA", "Opponent", "Cmp1", "Att1", "Cmp%", "TotDist", 
                           "PrgDist", "Cmp2", "Att2", "Cmp%2", "Cmp3", "Att3", "Cmp%3", 
                           "Cmp4", "Att4", "Cmp%4", "Ast", "xAG", "xA", "KP", "1/3", 
                           "PPA", "CrsPA", "PrgP", "Match Report"]
            else:
                raise Exception("Unknown table structure.")

            expected_length = len(headers)
            
            # Extract data from each row
            for row in rows:
                cols = row.find_all(['th', 'td'])
                cols = [col.get_text(strip=True) for col in cols]
                
                # Skip rows that don't match the expected length
                if len(cols) != expected_length:
                    continue
                
                data.append(cols)
            
            df = pd.DataFrame(data, columns=headers)
            dataframes[sheet_name] = df

            # Print out the headers and first few rows of the second sheet's data for debugging
            if sheet_name == "Match Logs":
                print(f"Headers for {team_name} - {sheet_name}: {headers}")
                print(f"Data for {team_name} - {sheet_name}:")
                print(df.head())

        # Save all DataFrames to an Excel file with multiple sheets
        output_file = f"{output_folder}/{team_name}.xlsx"
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        print(f"Data for {team_name} has been written to {output_file}")

# Main script execution
main_page_url = 'https://fbref.com/en/comps/Big5/Big-5-European-Leagues-Stats'
table_id = 'div_big5_table'
team_links = get_team_links(main_page_url, table_id)
output_folder = 'output'  # Desired output folder name
scoresfixtures(team_links, output_folder)
