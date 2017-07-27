""" Commands handled by the slack bot """
from datetime import datetime
from init import Message, BOT_ID
import os,logging,sqlite3,elosimple
from beautifultable import BeautifulTable
from elosimple import elo

conn = sqlite3.connect('pingpong.db')
c = conn.cursor()
try:
	import picamera
	camera = picamera.PiCamera()
except ImportError:
	logging.warning(' Failing to import picamera. DO NOT USE STATUS COMMAND.')

#message object has: channel to repond to, text of the command, user who sent the command
def handleMatchInput(message):
	correctFormat = "match [myScore] [@opponent] [opponentScore]"
	commandArgs = message.text.split()
	if len(commandArgs) != 4:
		return "text", "This is not a valid command! PLEASE use this format: " + correctFormat

	playerOneId = message.sender_id
	playerOneScore = commandArgs[1]
	playerTwoId = commandArgs[2]
	if (playerTwoId[:2] != '<@'):
		return "text", "Invalid command. Please tag your opponent using the '@' symbol."
	playerTwoId = playerTwoId.strip('<@>')
	playerTwoScore = commandArgs[3]

	if (playerOneId == playerTwoId):
		return "text", "You can't play against yourself, you moron!!"
	elif (playerTwoId == message.receiver_id):
		return "text", "You can't play against THE PongPal. You'd lose every time even if you tried."
	
	if (not playerOneScore.isdigit() or not playerTwoScore.isdigit()):
		return "text", "The scores have to be NUMBERS obviously"
	else:
		playerOneScore = int(playerOneScore)
		playerTwoScore = int(playerTwoScore)
	if (playerOneScore == playerTwoScore):
		return "text", "KEEP PLAYING. no ties allowed"
	timeStamp = datetime.now()

	c.execute('SELECT name, ELO FROM players WHERE user_id=?;', [playerOneId])
	playerOneRow = c.fetchone()
	playerOneName = playerOneRow[0]
	playerOneElo = playerOneRow[1]

	if playerOneElo == None:
		playerOneRank = None
		playerOneElo = 1200
	else: 
		playerOneRank = calculatePlayerRankFromElo(playerOneId, playerOneElo)

	c.execute('SELECT name, ELO FROM players WHERE user_id=?;', [playerTwoId])
	playerTwoRow = c.fetchone()
	if (playerTwoRow == None):
		return "text", "You entered an invalid opponent...awkward"
	playerTwoName = playerTwoRow[0]
	playerTwoElo = playerTwoRow[1]

	if (playerTwoElo == None):
		playerTwoElo = 1200
		playerTwoRank = None
	else:
		playerTwoRank = calculatePlayerRankFromElo(playerTwoId, playerTwoElo)

	c.execute('INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [timeStamp, playerOneName, playerOneScore, playerOneRank, playerOneElo, playerTwoName, playerTwoScore, playerTwoRank, playerTwoElo])
	""" calc new Elos here """
	newEloOne, newEloTwo = elo(playerOneElo, playerTwoElo, playerOneScore, playerTwoScore)
	c.execute('UPDATE players SET ELO=? WHERE user_id=?;', [newEloOne, playerOneId])
	c.execute('UPDATE players SET ELO=? WHERE user_id=?;', [newEloTwo, playerTwoId])
	conn.commit()

	if (playerTwoScore > playerOneScore):
		winnerName = playerTwoName
		winnerScore = playerTwoScore
		loserScore = playerOneScore
	else:
		winnerName = playerOneName
		winnerScore = playerOneScore
		loserScore = playerTwoScore

	return "text", "<@" + winnerName + ">" + " won! The score was " + str(winnerScore) + " - " + str(loserScore) + ". Your score has been recorded for posterity."

def calculatePlayerRankFromElo(playerId, elo):
	c.execute('SELECT COUNT(name) FROM players WHERE ELO>?;', [elo])
	rank = c.fetchone()[0] 
	return rank + 1

def sendHelpOptions(message):
	helpInfo = "Commands:\n*_help_* - Lists these commands here :table_tennis_paddle_and_ball:\n"
	statusInfo = "*_status_* - Sends you a picture of the current status of the ping-pong room\n"
	matchInfo = "*_match_* - Records your match and updates your overall ranking\n\t`match [myScore] [@opponent] [opponentScore]`\n"
	historyInfo = "*_history_* - Lists your match history, defaults to a list of 10. Takes an optional limit parameter as an integer or 'all'\n\t`history [limit?]`"
	return 'text', helpInfo + statusInfo + matchInfo + historyInfo

def sendRoomStatus(message):
	camera.capture('status.jpg')
	f = open('status.jpg','rb')
	return "file", {"comment":"Current status of the ping pong room:","filename":"Room Status","file":f}

def getMatchHistory(message):
	limit = 10
	textArray = message.text.split()
	c.execute("SELECT * FROM players WHERE user_id=?",(message.sender_id,))
	username = c.fetchone()[1]
	if len(textArray) > 2:
		return "text", "Invalid format. Format the history command as follows:\n\t`history [limit?]`\nType 'help' for more information."
	elif len(textArray) == 2:
		try:
			limit = int(textArray[1])
			if limit < 1:
				return "text", "'" + textArray[1] + "' is not a valid limit. Format the history command as follows:\n\t`history [limit?]`\nType 'help' for more information."
		except ValueError:
			if(textArray[1] == 'all'):
				limit = -1
			else:
				return "text", "'" + textArray[1] + "' is not a valid limit. Format the history command as follows:\n\t`history [limit?]`\nType 'help' for more information."
	c.execute("SELECT * FROM matches WHERE playerOne=? OR playerTwo=? ORDER BY date DESC LIMIT ?",(username,username,limit))
	results = c.fetchall()
	if results == []:
		return "text","Sorry, you have no previous matches!"
	table = BeautifulTable()
	table.column_headers = ["Date", "Match", "Score", "Winner"]
	wins = 0
	for result in results:
		winner = result[1] if int(result[2]) > int(result[6]) else result[5]
		table.append_row([datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d'),result[1] + " vs " + result[5], str(result[2]) + " - " + str(result[6]), winner])
		if winner == username:
			wins +=1
	title = str(int(float(wins)/float(len(results)) * 100)) + "% Win-Rate Over " + str(len(results)) + " Games\n"
	return "text", title+"```"+str(table)+"```"

def getPlayerStats(message):
	if len(message.text.split()) > 1:
		return "text", "Invalid format.\n Type 'help' for more information."
	c.execute("SELECT name,ELO FROM players WHERE user_id=?",(message.sender_id,))
	playerInfo = c.fetchone()
	username = playerInfo[0]
	ELO = playerInfo[1]
	c.execute("SELECT playerOne,scoreOne,playerTwo,scoreTwo FROM matches WHERE playerOne=? OR playerTwo=?",(username,username))
	results = c.fetchall()
	print(results)
	if results == []:
		return "text", "Sorry, you have no previous matches!"
	wins = 0
	losses = 0
	ptDiff = 0
	for result in results:
		playerOne = result[0]
		scoreOne = result[1]
		playerTwo = result[2]
		scoreTwo = result[3]
		winner = playerOne if scoreOne > scoreTwo else scoreTwo
		if(winner == username):
			wins+=1
		else:
			losses+=1

		if(playerOne == username):
			ptDiff += scoreOne - scoreTwo
		else:
			ptDiff += scoreTwo - scoreOne
	table = BeautifulTable()
	table.column_headers = ["ELO","Wins","Losses","Win-Rate","Point Diff", "Avg. Point Diff"]
	table.append_row([ELO,wins,losses,float(wins)/float(wins+losses),ptDiff,float(ptDiff)/float(wins+losses)])
	return "text", "```"+str(table)+"```"


