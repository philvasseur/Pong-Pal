""" Commands handled by the slack bot """
from datetime import datetime

import sqlite3
conn = sqlite3.connect('pingpong.db')
c = conn.cursor()

#message object has: channel to repond to, text of the command, user who sent the command
def handleMatchInput(message):
	commandArgs = message.text.split
	playerOneId = message.sender_id.strip('<@>')
	playerOneScore = commandArgs[1]
	playerTwoId = commandArgs[2].strip('<@>')
	playerTwoScore = commandArgs[3]
	timeStamp = datetime.now().date

	c.execute('SELECT * FROM players WHERE name=?;', playerOneId)
	playerOneRow = c.fetchone()
	playerOneElo = playerOneRow["ELO"]

	c.execute('SELECT * FROM players WHERE name=?;', playerTwoId)
	playerTwoRow = c.fetchone()
	playerTwoElo = playerTwoRow["ELO"]

	playerOneRank = calculatePlayerRankFromElo(playerOneId, playerOneElo)
	playerTwoRank = calculatePlayerRankFromElo(playerTwoId, playerTwoElo)

	c.execute('INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)', timeStamp, playerOneId, playerOneScore, playerOneRank, playerOneElo, playerTwoId, playerTwoScore, playerTwoRank, playerTwoElo)

	if (playerTwoScore > playerOneScore):
		winner = playerTwoId
	else:
		winner = playerOneId
	c.execute('SELECT name FROM players WHERE user_id=?', winner)

	return ("text", "temp message")


def calculatePlayerRankFromElo(playerId, elo):
	c.execute('SELECT COUNT(name) FROM players ELO > elo;')
	rank = c.fetchone()
	return rank

def sendHelpOptions(message):
	helpInfo = "Commands:\n'help' -\n\tLists these commands here :table_tennis_paddle_and_ball:\n"
	statusInfo = "'status' -\n\tSends you a picture of the current status of the ping-pong room\n"
	matchInfo = "'match' -\n\tRecords your match and updates your overall ranking\n\tUsage - match [myScore] [@opponent] [opponentScore]\n"
	historyInfo = "'history' -\n\tLists your match history, defaults to a list of 10. Takes an optional limit parameter as an integer or 'all'\n\tUsage - history [limit]?"
	return 'text',helpInfo + statusInfo + matchInfo + historyInfo

def sendRoomStatus():
	return null

def getMatchHistory():
	return null


# ("text", "message")
# ("file", "fileName")