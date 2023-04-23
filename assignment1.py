############################################################################

"""Implamentation for assignment 1 Tasks 1 to 5 for Elements of Data
Processing (COMP20008) by Justin Kelley."""

############################################################################

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
import unicodedata
import re
import json
from collections import defaultdict as dd
import matplotlib.pyplot as plt

############################################################################

# Task 1
# Component of starting url.
SEED_URL_END = 'index.html'

def get_headline(href):
    """"This function takes in a url, href, of an article and
    gets and returns the headline of the article."""
    
    # Extract data from site.
    page = requests.get(href)
    data = BeautifulSoup(page.text, 'html.parser')
    
    return data.find('h1').text



def process_links(data, searched, to_be_searched, articles, first, base_url):
    """"This functions processes the urls of the site, whose information
    is stored in data and updates the searched and to_be_Searched list
    lists ensuring a url is not explored twice."""
    
    # Check and deal with the homepage site to commence web crawl.
    if not first:
        articles[data.find('h1').text] = to_be_searched[0]
    links = data.findAll('a')
    
    # Process the url links for each article page and update the appropriate lists.
    for link in links:
        href = base_url + link['href']
        if (href not in searched and (link.text == "Next Article" or
                    link.text == "Previous Article") and get_headline(href) not in
                    articles.keys()) or first:
            to_be_searched.append(href)

    return 0



def exchange_keys_values(dictionary):
    """This function exchanges the positions of the keys and
    values in a dictionary."""
    
    # Exchange values.
    new_dic = {}
    for key in dictionary:
        new_dic[dictionary[key]] = key
        
    return new_dic




def crawl_web(base_url):
    """This function starts at the url, base_url, and crawls through the links
    on the site and collects url and headline data for the articles found
    and puts it into a csv file."""
    
    # These lists store the lists to be searched and those already searched.
    searched = []
    to_be_searched = []
    
    # Stores article headlines and their urls.
    articles = {}
    
    
    # Access and process the urls on the starting page.
    seed_url = base_url + SEED_URL_END
    page = requests.get(seed_url)
    searched.append(seed_url)
    data = BeautifulSoup(page.text, 'html.parser')
    process_links(data, searched, to_be_searched, articles, True, base_url)
    
    
    # Process each following site with articles and their urls.
    while to_be_searched:
        page = requests.get(to_be_searched[0])
        searched.append(to_be_searched[0])
        data = BeautifulSoup(page.text, 'html.parser')
        process_links(data, searched, to_be_searched, articles, False, base_url)
        to_be_searched.pop(0)
       
    
    # Export article data to a CSV file.
    articles = exchange_keys_values(articles)
    article_series = pd.Series(articles)
    article_series.index.name = 'url'
    article_series.name = 'headline'
    article_series.to_csv("task1.csv")
    
    
    return 0



# Run the web crawl function for task 1.   
crawl_web("http://comp20008-jh.eng.unimelb.edu.au:9889/main/")    



############################################################################

# Task 2
POTENTIAL_RE_SEARCH = "(([, ][\d]{1,2}[-/][\d]{1,2})|([, ]\([\d]{1,2}[-/][\d]{1,2}\))){2,10}"
INVALID_SCORE_RE_SEARCH = "(((0|15|30|45)-(0|15|30|45))|([0-5]-[0-5])|(6-[569])|\
                            ([569]-6))$"



def get_player_names(filename):
    """This function takes the tennis.json file that is to be stored
    in filename and puts the player names from the file into a list."""
    
    # The list to store player names.
    player_names = []
    
    # Access the json file.
    with open(filename) as file:
        player_data = json.load(file)
    
    # Put the names into the list.
    for element in player_data:
        name_cleaned = ""
        name = str(element["name"]).lower()
        for word in name.split(" "):
            name_cleaned = name_cleaned + " " + word.capitalize()
        player_names.append(name_cleaned)
      
    return player_names



def get_player_data(filename):
    """Ths function takes the first player name and first score that
    appears in each article and adds that to the data stored in the
    csv file, filename, and creates a new csv file with the new data."""
    
    # Get article links from filename.
    article_links = pd.read_csv(filename, encoding = 'ISO-8859-1', index_col="url")
    
    # Stores the names that appear in each article.
    first_name = ""
    
    # Stores the article text.
    article_text = ""
    
    # Stores the first player name and first score found in each article.
    article_first_player = {}
    article_first_score = {}
    
    # Checker if name match found.
    found = False
    
    # Get player names from json file.
    player_names = get_player_names("tennis.json")
    
    
    # Get first player name and first score found in each article.
    for link in article_links.index:
        
        # Access data from each link to articles.
        page = requests.get(link)
        data = BeautifulSoup(page.text, 'html.parser')
        
        # Get headline and body text from article.
        article_text = str(article_links[article_links.index ==
                                 link]["headline"][0]) + " "
        for part in data.find(id="articleDetail").findAll('p'):
            article_text = article_text + " " + str(part.text)
        
        
        # Find names from JSON file that appear in the article.
        first_name = ''
        info = article_text.split(" ")
        for word in info:
            for name in player_names:
                name_list = (name.split(" "))[1:]
                if word in name_list:
                    first_name = name[1:]
                    found = True
                    break
            if found == False:
                break
        
        # Add first name to dictionary or N\A if not found.
        if first_name:
            article_first_player[link] = first_name
        else:
            article_first_player[link] = "N\A"
        
        article_first_score[link] = "N\A"
       
       
        # Try to find first valid score in article.
        score = re.search(POTENTIAL_RE_SEARCH, article_text)
        while score:
            # Remove score from article text for next search
            # if required.
            score = score[0]
            score_temp = re.sub("\(", "\(", score)
            score_temp = re.sub("\)", "\)", score_temp)
            article_text = re.sub(score_temp, "", article_text)
            
            # Check if valid score. If not search for next score.
            score = re.sub('(\.)$|(,)$|(!)$', '', score)
            score = re.sub(',', ' ', score)
            if not re.search(INVALID_SCORE_RE_SEARCH, score):
                score = re.sub("^ ", "", score)
                article_first_score[link] = score
                break
            else:
                score = re.search(POTENTIAL_RE_SEARCH, article_text)
                
               
    # Compile all articel url, headline, player and score data together.
    article_links["player"] = article_first_player.values()
    article_links["score"] = article_first_score.values()
    article_links = article_links.loc[article_links["player"] != 'N\A']
    article_links = article_links.loc[article_links["score"] != 'N\A']
  
    # Put data in excel file.
    article_links.to_csv("task2.csv")

    return 0
    
    
    
# Run function to get data from articles.    
get_player_data("task1.csv")



############################################################################

# Task 3
NO_VALUE = -1



def calculate_game_difference(score_set):
    """Takes in a tennis score set, score_set, and calculates the
    game difference for that score set and returns that value."""
    
    # Each individual game score.
    scores = []
    
    # The game difference value.
    game_difference = 0
    
    # Calculate the game difference.
    for score in (score_set.split(" "))[:-2]:
        if "(" not in score:
            scores.append(score)

    # Calculate game difference.
    for score in scores:
        game_difference = game_difference + int(score[0]) - int(score[2])
    game_difference = abs(game_difference)

    
    return game_difference



def calculate_average_game_difference(filename):
    """Calculates the game difference for each score set corresponding
    to each article in filename and uses this to compute the average
    score for each player mentioned in the articles and exports this
    data to a CSV file."""
    
    # Scores individual game differences and their averages for each player.
    player_scores = dd(list)
    player_score_averages = {}
    
    # Sum of game differences for a player.
    game_difference_sum = 0
    
    # Get article data from filename.
    article_data = pd.read_csv(filename, encoding = 'ISO-8859-1', index_col="url").loc[:,['player', 'score']]
   

    # Calculate game differences for each player.
    groups = article_data.groupby('player')
    for name, group in groups:   
        for score in group['score']:
            game_difference = calculate_game_difference(str(score))
            player_scores[name].append(game_difference)
        
    
    # Calculate average game difference for each player.
    for player in player_scores:
        
        game_difference_sum = 0
        for game_difference in player_scores[player]:
            game_difference_sum = game_difference_sum + game_difference
        
        player_score_averages[player] = \
                            game_difference_sum / (len(player_scores[player]))
    
    # Export player data to a CSV file.
    player_score_averages_series = pd.Series(player_score_averages)
    player_score_averages_series.index.name = 'player'
    player_score_averages_series.name = 'avg_game_difference'
    player_score_averages_series.to_csv("task3.csv")
    
    return 0
  
    
    
calculate_average_game_difference("task2.csv")



############################################################################

# Task 4
def determine_player_coverage(filename):
    """This function calculates the frequency of player coverage by
    articles for each player using the data from filename and exports
    this calculated data as a bar chart."""
    
    # These store the frequency of article coverage of the players.
    player_coverage = {}
    top_5 = {}
    
    # Get article data from filename.
    article_data = pd.read_csv(filename, encoding = 'ISO-8859-1', index_col="url")
    
    
    # Determine frequency of article coverage for each player.
    groups = article_data.groupby('player')
    for name, group in groups:
        count = 0
        for article in group["headline"]:
            count += 1
        player_coverage[str(name)] = count
   

    # Choose top five most frequently covered players. In event of a tie, then
    # select player occuring first in the dictionary, player_coverage.
    frequencies = list(sorted(player_coverage.values(), reverse=True))
    for i in range(0, 5):
        for player in player_coverage.keys():
            if player_coverage[player] == frequencies[i] and player not in top_5:
                top_5[player] = player_coverage[player]
                break
          
        
    # Construct and export a bar chart showing the top five players with most
    # article coverage frequency.
    plt.xticks(rotation='vertical')
    plt.bar(top_5.keys(), top_5.values())
    plt.ylabel('Frequency')
    plt.title("Players With Most Article Coverage")
    plt.tight_layout()
    plt.savefig('task4.png', dpi=200, transparent = True)
    plt.close()
    
    return 0
  
determine_player_coverage("task2.csv")



############################################################################

# Task 5



def get_win_percentage(filename, players):
    """This function gets the win percentages for the players in player
    from the json file, filename, and returns this data as a dictionary."""
   
    # Stores win percentages for each player.
    win_percentages = {}
    
    # Access the json file.
    with open(filename) as file:
        player_data = json.load(file)
    
    
    # Get the winning percentages for each player.
    for element in player_data:
        
        # Clean up the capitalisation of each name.
        name_list = (str(element["name"]).lower()).split()
        name = ""
        for word in name_list:
            name = name + " " + word.capitalize()
        name = name[1:] 
        
        # Add win percentages to dictionary.
        if name in players:
            win_percentages[name] = float(str(element["wonPct"])[:-1])
         
        
    return win_percentages
   
    

def determine_player_performance(filename):
    """This function gets the average game difference and winning
    percentage for each player in filename and exports a scatter
    plot showing the comparsion between these values for each
    player."""
    
    # Get game difference data from filename.
    game_difference_data = pd.read_csv(filename, 
                                       encoding = 'ISO-8859-1', index_col="player")
    
    # Get win percentages for each player.
    players = list(game_difference_data.index)
    win_percentages = get_win_percentage("tennis.json", players)
    
    # Combine win percentage and average game difference data for each player.
    win_percentages_series = pd.Series(win_percentages)
    win_percentages_series.index.name = 'players'
    win_percentages_series.name = 'Win Percentages (%)'
    game_difference_data["Win Percentages (%)"] = win_percentages_series
  
    
    # Construct scatter plot showing the comparsion between win percentage
    # and average game difference for each player. Add data first.
    plt.scatter(game_difference_data.iloc[:,0], game_difference_data.iloc[:,1], marker='x')
   
    # Add data and label axis and specificy their constraints.
    plt.xlim(-1,7)
    plt.ylim(40,90)
    plt.ylabel("Win Percentage (%)")
    plt.xlabel("Average Game Difference")
    plt.title("Players (Win Percentage vs Average Game Difference)")
    
    # Add legend and export scatter plot to a png file.
    plt.tight_layout()
    plt.grid(True)
    plt.savefig('task5.png', dpi=200, transparent = True)
    plt.close()
    
    return 0



determine_player_performance("task3.csv")
