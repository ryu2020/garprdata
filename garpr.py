import json
import requests
from datetime import datetime
import csv
import time
import re

#region variable, found in garpr url
region = 'newjersey'

#specify start and endtimes of season to collect data from (can be any timeframe)
seasonstart = datetime(2019, 9, 23)
seasonend = datetime(2020, 3, 15)

#Player class
class Player:
    def __init__(self, id, name):
        #id taken from GARPR player page
        self.id = id
        #name is name that will display in all output formats
        self.name = name

#specify maximum number of retries that can occur during request to the server
maxretries = 20

#read in excluded tournaments
excluded = []
with open("ignore.txt", "r") as filestream:
    for line in filestream:
        excluded.append(line.rstrip())


#read in players
players = []
with open("players.txt", "r") as filestream:
    for line in filestream:
        if not re.match('#', line):
            line = line.rstrip().split(',')
            player = Player(line[1], line[0])
            print(line)
            players.append(player)

print(players)

#uncomment for reading to text file
results = open("h2hs.txt","a")

#initialize the results list
resultslist = []

#initialize the list of headings (containing opponent names)
headingslist = ['Players (W / L)']

for player in players:

    #add wins and losses vs. player to headings list
    headingslist.append(player.name + ' W')
    headingslist.append(player.name + ' L')

    #initialize list of player wins and losses
    playerlist = [player.name]

    #for each opponent (every other player)
    for opponent in players:

        #check to make sure opponent is different from player
        if(player != opponent):

            #generate URL to pull head-to-head json data from
            url = "https://notgarpr.com:3001/" + region + "/matches/" + player.id + "?opponent=" + opponent.id + "&fbclid=IwAR3V8QosRC1_d-tBrPtSLB7pHKWuwXlea6fuKVjU645bq6dKNEshOvL7tv8"

            #initialize response
            response = ''

            #initialize number of retries to connect to server
            numretries = 0

            #create loop to try to generate response
            while(response == ''):
                try:
                    #load json response from url
                    response = requests.get(url)
                    break
                #if a keyboardinterupt occurs abort execution
                except (KeyboardInterrupt, SystemExit):
                    raise
                #if an exception occurs due to connection refusal
                except:
                    #if we have exceeded the maximum number of retries raise an
                    #exception
                    if(numretries > maxretries):
                        raise Exception("Exceeded maximum number of retries to connect to the server")
                    #otherwise sleep for five seconds and then retry the request
                    print("Connection refused by the server")
                    print("Waiting to retry")
                    time.sleep(5)
                    print("Retrying connection")

                    #increment number of retries then retry connection
                    numretries += 1
                    continue

            #load data from the reponse
            data = json.loads(response.text)

            #initialize counts of wins and losses for given matchup
            wins = 0
            losses = 0

            #boolean to check if players have played during timeframe
            played = False

            #sometimes GARPR will not return match data (this only happens when
            #the players have not played, but sometiems GARPR will also just
            #give match data with 0s), check for this case to avoid index not
            #found error

            match_included = True

            if('matches' in data):
                print('found matches')
                #look at each match sub-dictionary within the pulled data
                for match in data['matches']:

                    #checks if the tournament is counted
                    tournament = match['tournament_name']
                    for t in excluded:
                        regex = re.compile('(' + t + ')', re.IGNORECASE)
                        if regex.match(tournament):
                            print('match ignored:' + tournament)
                            match_included = False
                            break

                    if(match_included):
                        #check to make sure the match date is within the timeframe
                        date = datetime.strptime(match['tournament_date'], '%m/%d/%y')
                        if(seasonstart <= date <= seasonend):
                            #read the match result (win or loss), update the
                            #counts accordingly, and indicate that the players have
                            #played
                            if(match['result'] == 'win'):
                                wins += 1
                                played = True
                            #check to make sure match isn't excluded (in which case
                            #it would have a result of 'excluded')
                            elif(match['result'] == 'lose'):
                                losses += 1
                                played = True

            #if the players have played, print the head-to-head to the console
            #and record the win and loss counts in the playerlist
            if(played):
                print(player.name + " vs. " + opponent.name + "\r\n")
                print(str(wins) + " - " + str(losses))
                #uncomment to write to text file
                results.write(player.name + " vs. " + opponent.name + "\r\n")
                results.write(str(wins) + " - " + str(losses) + "\r\n")
                playerlist.append(str(wins))
                playerlist.append(str(losses))
            #if the players have not played, append empty strings to the player
            #list to match the desired csv output
            else:
                playerlist.append('')
                playerlist.append('')
        #similarly create empty strings if there is no match data for the given
        #matchup
        else:
            playerlist.append('')
            playerlist.append('')
    #add given player list to end of the results list to create one list of all
    #player data
    resultslist.append(playerlist)

#once all matchups have been recorded, insert the completed list of headings
#at the beginning of the resultslist
resultslist.insert(0, headingslist)

#initialize number of retries to access the csv file
numretries = 0

#initialize boolean to determine if we can write to csv file
csvWrite = False

#create loop to try to access file
while(not csvWrite):

    try:
        #open the csv output file and avoid creating extra spacing lines
        csvFile = open("h2hresults.csv", "w", newline='')

        #specify that we can now write
        csvWrite = True

    #if a keyboardinterupt occurs abort execution
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        #if we have exceeded the maximum number of retries raise an
        #exception
        if(numretries > maxretries):
            raise Exception("Exceeded maximum number of retries to access the file")
        #otherwise sleep for five seconds and then retry the request
        print("Permission to access csv file denied, please close any programs with the file open")
        print("Waiting to retry write request to file")
        time.sleep(5)
        print("Retrying write request")

        #increment number of retries then retry connection
        numretries += 1

        continue

#truncate the csv file to remove old results
csvFile.truncate()

#write each element in the results list to the csv file
with csvFile:
    csv
    writer = csv.writer(csvFile)
    writer.writerows(resultslist)
csvFile.close()

#indicate the program has completed (typically takes a while, time will
#increase quadratically with more opponents)
print("done")
