import pandas as pd
import requests
from bs4 import BeautifulSoup

def scoresfixtures(links_ids, output_file='output.xlsx'):
    '''
    Description: This function picks all the games in one season and combines all links into one specific list,
                 then saves the data to an Excel file.
    
    Inputs:
        - links_ids: A dictionary where keys are the links of the main pages and values are the IDs of the tables on those pages.
        - output_file: The name of the output Excel file (default is 'output.xlsx').
        
    Outputs:
        - An Excel file containing the data.
    '''
    
    # Create an empty dictionary to store all DataFrames with their sheet names
    dataframes = {}

    for link, ids in links_ids.items():
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

        # Determine headers based on the URL
        if "Bayer-Leverkusen-Stats" in link:
            headers = ["Date", "Time", "Comp", "Round", "Day", "Venue", "Result", 
                       "GF", "GA", "Opponent", "xG", "xGA", "Poss", "Attendance", 
                       "Captain", "Formation", "Referee", "Match Report", "Notes"]
            sheet_name = "Stats"
        elif "Bayer-Leverkusen-Match-Logs-All-Competitions" in link:
            headers = ["Date", "Time", "Comp", "Round", "Day", "Venue", "Result", 
                       "GF", "GA", "Opponent", "Cmp1", "Att1", "Cmp%", "TotDist", 
                       "PrgDist", "Cmp2", "Att2", "Cmp%2", "Cmp3", "Att3", "Cmp%3", 
                       "Cmp4", "Att4", "Cmp%4", "Ast", "xAG", "xA", "KP", "1/3", 
                       "PPA", "CrsPA", "PrgP", "Match Report"]
            sheet_name = "Passing"
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

    # Save all DataFrames to an Excel file with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Data has been written to {output_file}")