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

def sendHelpOptions():
	return null

def sendRoomStatus():
	return null

def getMatchHistory():
	return null


# ("text", "message")
# ("file", "fileName")