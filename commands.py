""" Commands handled by the slack bot """
from datetime import datetime


import sqlite3
conn = sqlite3.connect('pingpong.db')
c = conn.cursor()

#message object has: channel to repond to, text of the command, user who sent the command
def handleMatchInput(message):
	correctFormat = "match [your score] [opponent] [opponent score]"
	commandArgs = message.text.split
	if len(commandArgs) != 4:
		return "text", "This is not a valid command! PLEASE use this format: " + correctFormat

	playerOneId = message.sender_id.strip('<@>')
	playerOneScore = commandArgs[1]
	playerTwoId = commandArgs[2].strip('<@>')
	playerTwoScore = commandArgs[3]

	if (playerOneId == playerTwoId):
		return "text", "You can't play against yourself, you moron!!"
	elif (playerOneId == bot_id):
		return "text", "You can't play against THE PongPal. You'd lose every time if you tried anyhow"
	
	if (not playerOneScore.isdigit() or not playerTwoScore.isdigit()):
		return "text", "The scores have to be NUMBERS obviously"
	else:
		playerOneScore = int(playerOneScore)
		playerTwoScore = int(playerTwoScore)
	if (playerOneScore == playerTwoScore):
		return "text", "KEEP PLAYING. no ties allowed"
	timeStamp = datetime.now().date

	c.execute('SELECT name, ELO FROM players WHERE user_id=?;', playerOneId)
	playerOneRow = c.fetchone()
	playerOneElo = playerOneRow["ELO"]
	playerOneName = playerOneRow["name"]

	c.execute('SELECT name, ELO FROM players WHERE user_id=?;', playerTwoId)
	if (playerOneRow == None):
		return "text", "You entered an invalid opponent...awkward"
	playerTwoRow = c.fetchone()
	playerTwoElo = playerTwoRow["ELO"]
	playerTwoName = playerTwoRow["name"]

	playerOneRank = calculatePlayerRankFromElo(playerOneId, playerOneElo)
	playerTwoRank = calculatePlayerRankFromElo(playerTwoId, playerTwoElo)

	c.execute('INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?)', timeStamp, playerOneId, playerOneScore, playerOneRank, playerOneElo, playerTwoId, playerTwoScore, playerTwoRank, playerTwoElo)

	if (playerTwoScore > playerOneScore):
		winnerName = playerTwoName
		winnerScore = playerTwoScore
		loserScore = playerOneScore
	else:
		winnerName = playerOneName
		winnerScore = playerOneScore
		loserScore = playerTwoScore

	return "text", winnerName + "won! The score was " + winnerScore + " - " + loserScore + ". Your score has been recorded for posterity"


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

def main():
	


# ("text", "message")
# ("file", "fileName")