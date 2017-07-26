""" Commands handled by the slack bot """
from datetime import datetime
from init import Message, BOT_ID

import logging
import sqlite3
conn = sqlite3.connect('pingpong.db')
c = conn.cursor()
try:
    import picamera
    camera = picamera.PiCamera()
except ImportError:
    logging.warning(' Failing to import picamera. DO NOT USE STATUS COMMAND.')


#message object has: channel to repond to, text of the command, user who sent the command
def handleMatchInput(message):
	correctFormat = "match [your score] [opponent] [opponent score]"
	commandArgs = message.text.split()
	if len(commandArgs) != 4:
		return "text", "This is not a valid command! PLEASE use this format: " + correctFormat

	playerOneId = message.sender_id.strip('<@>')
	playerOneScore = commandArgs[1]
	playerTwoId = commandArgs[2].strip('<@>')
	playerTwoScore = commandArgs[3]

	if (playerOneId == playerTwoId):
		return "text", "You can't play against yourself, you moron!!"
	elif (playerOneId == BOT_ID):
		return "text", "You can't play against THE PongPal. You'd lose every time if you tried anyhow"
	
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
	if (playerOneElo == None):
		c.execute('UPDATE players SET ELO=1200 WHERE user_id=?;', [playerOneId])
		playerOneElo = 1200

	c.execute('SELECT name, ELO FROM players WHERE user_id=?;', [playerTwoId])
	if (playerOneRow == None):
		return "text", "You entered an invalid opponent...awkward"
	playerTwoRow = c.fetchone()
	playerTwoName = playerTwoRow[0]
	playerTwoElo = playerTwoRow[1]
	if (playerTwoElo == None):
		c.execute('UPDATE players SET ELO=1200 WHERE user_id=?;', [playerTwoId])
		playerTwoElo = 1200

	playerOneRank = calculatePlayerRankFromElo(playerOneId, playerOneElo)
	playerTwoRank = calculatePlayerRankFromElo(playerTwoId, playerTwoElo)

	c.execute('INSERT INTO matches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', [timeStamp, playerOneId, playerOneScore, playerOneRank, playerOneElo, playerTwoId, playerTwoScore, playerTwoRank, playerTwoElo])
	conn.commit()

	if (playerTwoScore > playerOneScore):
		winnerName = playerTwoName
		winnerScore = playerTwoScore
		loserScore = playerOneScore
	else:
		winnerName = playerOneName
		winnerScore = playerOneScore
		loserScore = playerTwoScore

	return "text", winnerName + " won! The score was " + str(winnerScore) + " - " + str(loserScore) + ". Your score has been recorded for posterity"


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

def sendRoomStatus():
	camera.capture('status.jpg')
	f = open('status.jpg','rb')
	return "file", {"comment":"Current status of the ping pong room:","filename":"Room Status","file":f}

def getMatchHistory():
	return null
	


# ("text", "message")
# ("file", "fileName")
