""" Commands handled by the slack bot """
from datetime import datetime
from init import Message, BOT_ID, sendMessage, sendConfirmation
import os,logging,sqlite3,elo
from beautifultable import BeautifulTable
from processImage import eval_single_img
from elo import elo

conn = sqlite3.connect('pingpong.db')
c = conn.cursor()
try:
	import picamera
	camera = picamera.PiCamera()
	camera.vflip = True
	camera.hflip = True
except ImportError:
	logging.warning(' Failing to import picamera. DO NOT USE STATUS COMMAND.')

def confirmMatch(message):
	correctFormat = "confirm [matchNumber]"
	commandArgs = message.text.split()
	if len(commandArgs) != 2:
		return "text", "This is not a valid command! PLEASE use this format: " + correctFormat
	match = commandArgs[1]
	c.execute('SELECT confirmPermissions, playerOne, playerTwo, scoreOne, scoreTwo FROM matches WHERE matchNumber=?', [match])
	players = c.fetchone()
	if players == None:
		return "text", "Sorry, I can't find that match number to confirm it!"
	playerWithPermission = players[0]
	if playerWithPermission != message.sender_id:
		return "text", "Sorry! Only <@" + playerWithPermission + "> can confirm match " + str(match) + "."
	playerOne = players[1]
	playerTwo = players[2]
	playerOneScore = players[3]
	playerTwoScore = players[4]
	c.execute('SELECT user_id, ELO FROM players WHERE name=?', [playerOne])
	playerOneIdElo = c.fetchone()
	playerOneId = playerOneIdElo[0]
	playerOneElo = playerOneIdElo[1]
	c.execute('SELECT ELO FROM players WHERE name=?', [playerTwo])
	playerTwoElo = c.fetchone()[0]

	playerOneElo = playerOneElo if playerOneElo != None else 1200
	playerTwoElo = playerTwoElo if playerTwoElo != None else 1200

	""" calc new Elos here """
	newEloOne, newEloTwo = elo(playerOneElo, playerTwoElo, playerOneScore, playerTwoScore)
	playerOneRank = calculatePlayerRank(playerOne)
	playerTwoRank = calculatePlayerRank(playerTwo)

	c.execute('UPDATE matches SET confirmed=?,rankingOne=?, ELOOne=?,rankingTwo=?, ELOTwo=? WHERE matchNumber=?', [1, playerOneRank, newEloOne, playerTwoRank, newEloTwo, match])

	sendConfirmation("Your opponent <@" + playerTwo + "> confirmed the results of match #" + str(match) + ".", playerOneId)
	
	c.execute('UPDATE players SET ELO=? WHERE name=?;', [newEloOne, playerOne])
	c.execute('UPDATE players SET ELO=? WHERE name=?;', [newEloTwo, playerTwo])
	conn.commit()

	return "text", "Thanks! I confirmed match #" + str(match) + " and updated player rankings."

#message object has: channel to repond to, text of the command, user who sent the command
def handleMatchInput(message):
	correctFormat = "match [myScore] [@opponent] [opponentScore]"
	commandArgs = message.text.split()
	if len(commandArgs) != 4:
		return "text", "Invalid input! Format the match command as follows:\n\t" + correctFormat + " Type 'help' for more information."
	playerOneId = message.sender_id
	playerOneScore = commandArgs[1]
	playerTwoId = commandArgs[2]
	if (playerTwoId[:2] != '<@'):
		return "text", "Invalid command. Please tag your opponent using the '@' symbol."
	playerTwoId = playerTwoId.strip('<@>')
	playerTwoScore = commandArgs[3]

	if (playerOneId == playerTwoId):
		return "text", "You can't play against yourself, silly goose!"
	elif (playerTwoId == message.receiver_id):
		return "text", "You can't play against me! I might know a lot about pong, but I have no limbs."
	
	if (not playerOneScore.isdigit() or not playerTwoScore.isdigit()):
		return "text", "Invalid input! The scores must be numbers."
	else:
		playerOneScore = int(playerOneScore)
		playerTwoScore = int(playerTwoScore)
	if (playerOneScore == playerTwoScore):
		return "text", "KEEP PLAYING. No ties allowed."
	timeStamp = datetime.now()

	c.execute('SELECT name FROM players WHERE user_id=?;', [playerOneId])
	playerOneRow = c.fetchone()
	c.execute('SELECT name FROM players WHERE user_id=?;', [playerTwoId])
	playerTwoRow = c.fetchone()

	if (playerTwoRow == None):
		return "text", "The opponent you entered isn't a valid player."

	playerOneName = playerOneRow[0]
	playerTwoName = playerTwoRow[0]

	c.execute('INSERT INTO matches (date, confirmPermissions, confirmed, playerOne, scoreOne, rankingOne, ELOOne, playerTwo, scoreTwo, rankingTwo, ELOTwo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [timeStamp, playerTwoId, 0, playerOneName, playerOneScore, None, None, playerTwoName, playerTwoScore, None, None])
	c.execute('SELECT matchNumber FROM matches WHERE date=?', [timeStamp])
	matchNum = c.fetchone()[0]
	conn.commit()

	if (playerTwoScore > playerOneScore):
		winnerName = playerTwoName
		winnerScore = playerTwoScore
		loserScore = playerOneScore
	else:
		winnerName = playerOneName
		winnerScore = playerOneScore
		loserScore = playerTwoScore

	result = "<@" + winnerName + ">" + " won! The score was " + str(winnerScore) + " - " + str(loserScore) + "."
	sendConfirmation("Congrats on another match! Type `confirm " + str(matchNum) + "` to confirm the result: " + result, playerTwoId)
	return "text", result + " Match #" + str(matchNum) + " is awaiting confirmation from your opponent."

def calculatePlayerRank(playerName):
	c.execute('SELECT ELO FROM players where name = ?;', [playerName])
	elo = c.fetchone()[0]
	if elo is None:
		return None
	else:
		c.execute("SELECT COUNT(name) FROM players WHERE ELO > ?;", [elo])
		rank = c.fetchone()[0] 
		return rank + 1

def calculatePlayerRankInGroup(playerName, groupName):
	members = getGroupMembers(groupName)
	question_marks = ','.join(['?'] * len(members))
	c.execute('SELECT COUNT(name) FROM players WHERE ELO > (SELECT ELO FROM players where name = ?) AND name IN ('+question_marks+');', [playerName] + members)
	rank = c.fetchone()[0] 
	return rank + 1

def getGroupMembers(groupName):
	c.execute('SELECT username FROM groups WHERE groupname=?', [groupName])
	rows = c.fetchall()
	memberlist = []
	for row in rows:
		memberlist.append(row[0])
	return memberlist

def displayRankings(message):
	limit = 10
	forOnePlayer = False
	commandArgs = message.text.split()
	if (len(commandArgs) > 2):
		return "text", "Invalid input for match command. Type 'help' for more information."
	elif (len(commandArgs) == 2):
		arg = commandArgs[1]
		if (not isValidUserName(arg)):
			if arg.isdigit():
				limit = arg
			else:
				return "text", "Invalid input for match command. Type 'help' for more information."
		else:
			player = arg.strip('<@>')
			forOnePlayer = True
	table = BeautifulTable(max_width=100)
	table.column_headers = ["Player Name","ELO", "Rank"]
	if forOnePlayer:
		c.execute('SELECT name, ELO FROM players WHERE user_id=?', (player,))
		row = c.fetchone()
		name, ELO = row[0], row[1]
		rank = calculatePlayerRank(name)
		table.append_row([name, ELO, rank])
		return "text", "Ranking of <@" + name + ">\n```"+str(table)+"```"
	else:
		c.execute('SELECT name, ELO FROM players ORDER BY ELO DESC LIMIT ?', (limit,))
		results = c.fetchall()
		index = 0
		for r in results:
			name, ELO = r[0], r[1]
			if (ELO is not None):
				index += 1
				table.append_row([name, ELO, index])
		return "text", "Displaying top " + str(index) + " player(s) at Lucid\n```"+str(table)+"```"

def handleGroupsInput(message):
	commandArgs = message.text.split()
	if (len(commandArgs) > 3 or len(commandArgs) < 2):
		return "text", "Invalid groups command. Type 'help' for more information."
	action = commandArgs[1]
	if (action == "view" and len(commandArgs) == 2):
		c.execute('SELECT DISTINCT groupname from groups;')
		groups = c.fetchall()
		groupsList = ""
		for g in groups:
			groupsList = groupsList + g[0] + "\n"
		return "text", "List of all pong groups at Lucid:\n" + groupsList
	elif (action == "new" and len(commandArgs) == 3):
		groupName = commandArgs[2]
		c.execute('SELECT name FROM players WHERE user_id=?;', [message.sender_id])
		userName = c.fetchone()[0]
		createGroup(groupName, userName)
		return "text", "Congrats, you have created a new group called *" + groupName + "*!"
	else:
		return "text", "Invalid groups command. Type 'help' for more information."

def handleMembersInput(message):
	commandArgs = message.text.split()
	if (len(commandArgs) < 3):
		return "text", "Invalid members command. Type 'help' for more information."
	action = commandArgs[1]
	groupName = commandArgs[2]
	c.execute("SELECT groupname FROM groups WHERE groupname=?", [groupName])
	results = c.fetchone()
	if (results == None):
		return "text", "This group doesn't exist!"
	if (action == "add" and len(commandArgs) > 3):
		memberlist = getMembersFromCommand(commandArgs[3:])
		membersAdded = ""
		for m in memberlist:
			c.execute("SELECT groupname FROM groups WHERE username=?", [groupName])
			groups = c.fetchall()
			alreadyInGroup = False
			for g in groups:
				if g[0] == groupName:
					alreadyInGroup = True
					print("don't add duplicate")
			if (not alreadyInGroup):
				c.execute("INSERT INTO groups VALUES (?, ?)", [m, groupName])
				conn.commit()
				membersAdded = membersAdded + "<@" + m + ">" + "\n"
		return "text", "The following members were succesfully added to group " + groupName + ":\n" + membersAdded
	elif (action == "view" and len(commandArgs) == 3):
		c.execute("SELECT username FROM groups WHERE groupname=?", [groupName])
		members = c.fetchall()
		resultText = "Here are the members of group *" + groupName + "*:\n"
		for row in members:
			resultText = resultText + str(row[0]) + "\n"
		return "text", resultText
	else:
		return "text", "Invalid members command. Type 'help' for more information."

def sendHelpOptions(message):
	helpInfo = "Commands:\n*_help_* - Lists these commands here :table_tennis_paddle_and_ball:\n"
	statusInfo = "*_status_* - Sends you a picture of the current status of the ping-pong room\n"
	matchInfo = "*_match_* - Records your match and updates your overall ranking\n\t`match [myScore] [@opponent] [opponentScore]`\n\t_Example usage_: `match 21 <@pongpal> 5`\n"
	historyInfo = "*_history_* - Lists your match history, defaults to a list of 10. Takes an optional limit parameter as an integer or 'all'\n\t`history [limit?]`\n"
	statsInfo = "*_stats_* - Shows a player's stats, defaults to your stats. Can show a player's stats within a group, defaults to the entire company. Takes an optional player username parameter and an optional group parameter. \n\t`stats [@player?] [group?]`\n\t_Example usage_: `stats <@pongpal> bot-group`\n"
	rankingsInfo = "*_rankings_* - Displays company-wide rankings, defaults to a list of the top 10 players at Lucid. Takes an optional player parameter, to display one player's rank. Also takes an optional limit parameter as an integer or 'all'. \n\t`rankings [@player?] [limit?]`\n"
	groupsInfo = "*_groups_* - Create a new group or view all existing groups. Creating a new group automatically adds you to the group. Groups allow you to view group members' stats within the context of their group\n\t Type `groups new [groupname]` to create a new group\n\t Type `groups view` to view all existing groups\n"
	membersInfo = "*_members_* - Add a list of members to a group or view all members in a group\n\tType `members add [groupname] [@member1] [@member2?] [@member3?] ...` to add new members to a group\n\tType `members view [groupname]` to view members of a group"
	return 'text', helpInfo + statusInfo + matchInfo + historyInfo + statsInfo + rankingsInfo + groupsInfo + membersInfo

def sendRoomStatus(message):
	filename = "room_status.jpg"
	camera.capture(filename, resize=(1080, 811))
	f = open(filename,"rb")
	img_res = eval_single_img(filename)
	print(img_res)
	result = "It looks like the room is open!" if img_res == 0 else "Sorry, looks like the room is being used!"
	sendMessage(result,message.channel)
	return "file", {"comment":None,"filename":"However, check for yourself:","file":f}

def getMatchHistory(message):
	limit = 10
	textArray = message.text.split()
	c.execute("SELECT * FROM players WHERE user_id=?",(message.sender_id,))
	username = c.fetchone()[1]
	if len(textArray) > 2:
		return "text", "Invalid format. Format the history command as follows:\n\t`history [limit?]` Type 'help' for more information."
	elif len(textArray) == 2:
		try:
			limit = int(textArray[1])
			if limit < 1:
				return "text", "'" + textArray[1] + "' is not a valid limit. Format the history command as follows:\n\t`history [limit?]` Type 'help' for more information."
		except ValueError:
			if(textArray[1] == 'all'):
				limit = -1
			else:
				return "text", "'" + textArray[1] + "' is not a valid limit. Format the history command as follows:\n\t`history [limit?]` Type 'help' for more information."
	c.execute("SELECT * FROM matches WHERE (playerOne=? OR playerTwo=?) AND confirmed=? ORDER BY date DESC LIMIT ?",(username,username,1,limit))
	results = c.fetchall()
	if results == []:
		return "text","Sorry, you have no previous matches!"
	table = BeautifulTable(max_width=100)
	table.column_headers = ["Match #","Date", "Player Names", "Score", "Winner","Post Match Elo"]
	wins = 0
	for result in results:
		winner = result[4] if int(result[5]) > int(result[9]) else result[8]
		table.append_row([result[0],datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d'),result[4] + " vs " + result[8], str(result[5]) + " - " + str(result[9]), winner, str(int(result[7])) + " - " + str(int(result[11]))])
		if winner == username:
			wins +=1
	title = str(int(float(wins)/float(len(results)) * 100)) + "% Win-Rate Over " + str(len(results)) + " Games\n"
	return "text", title+"```"+str(table)+"```"

def getPlayerStats(message):
	commandArgs = message.text.split()
	groupId = None
	playerIsYou = True
	if len(commandArgs) > 3:
		return "text", "Invalid format. Type 'help' for more information."
	elif len(commandArgs) == 3:
		playerId = commandArgs[1]
		if (not isValidUserName(playerId)):
			return "text", "Invalid command. Please tag a player using the '@' symbol. Type 'help' for more information."
		playerId = playerId.strip('<@>')
		c.execute("SELECT name,ELO FROM players WHERE user_id=?",(playerId,))
		playerInfo = c.fetchone()
		playerIsYou = False
		groupId = commandArgs[2]
		c.execute('SELECT groupname FROM groups WHERE groupname=?', (groupId,))
		result = c.fetchone()
		if (result == None):
			return "text", "The group you entered doesn't exist!"
	elif len(commandArgs) == 2:
		optionalArg = commandArgs[1]
		if (not isValidUserName(optionalArg)):
			c.execute('SELECT groupname FROM groups WHERE groupname=?', (optionalArg,))
			result = c.fetchone()
			if (result == None):
				return "text", "The optional argument you entered is neither a valid user nor a valid group. Type 'help' for more information."
			else:
				groupId = optionalArg
				c.execute("SELECT name,ELO FROM players WHERE user_id=?",(message.sender_id,))
				playerInfo = c.fetchone()
		else:
			playerIsYou = False
			playerId = optionalArg.strip('<@>')
			c.execute("SELECT name,ELO FROM players WHERE user_id=?",(playerId,))
			playerInfo = c.fetchone()
			if playerInfo == None:
				return "text", "The opponent you entered isn't a valid player."			
	else:
		c.execute("SELECT name,ELO FROM players WHERE user_id=?",(message.sender_id,))
		playerInfo = c.fetchone()

	username = playerInfo[0]
	ELO = playerInfo[1]
	if groupId:
		rank = calculatePlayerRankInGroup(username, groupId)
		groupmembers = getGroupMembers(groupId)
		print(groupmembers)
		question_marks = ','.join(['?'] * len(groupmembers))
		c.execute('SELECT playerOne,scoreOne,playerTwo,scoreTwo FROM matches WHERE confirmed=? AND (playerOne=? AND playerTWO IN ('+ question_marks +') OR playerTwo=? AND playerOne IN (' + question_marks + '))',[1] + [username] + groupmembers + [username] + groupmembers)
	else:
		rank = calculatePlayerRank(username)
		c.execute("SELECT playerOne,scoreOne,playerTwo,scoreTwo FROM matches WHERE confirmed = ? AND (playerOne=? OR playerTwo=?)",(1,username,username))
	results = c.fetchall()
	if results == []:
		if playerIsYou:
			return "text", "Sorry, you have no previous matches!"
		else:
			return "text", "Sorry, <@" + username + '> has no previous matches!' 
	wins, losses, ptDiff = calcStats(results, username)
	table = BeautifulTable(max_width=100)
	table.column_headers = ["Rank","Elo","Wins","Losses","Win-Rate","Point Diff", "Avg. Point Diff"]
	table.append_row([rank,int(ELO),wins,losses,str(float(wins)/float(wins+losses)*100) + "%",ptDiff,float(ptDiff)/float(wins+losses)])
	messageHeader = "Stats for <@" + username + ">"
	if groupId:
		messageHeader = messageHeader + " in group *" + groupId + "*"
	return "text", messageHeader + "\n```"+str(table)+"```"

def calcStats(results, username):
	wins = 0
	losses = 0
	ptDiff = 0
	for result in results:
		playerOne = result[0]
		scoreOne = result[1]
		playerTwo = result[2]
		scoreTwo = result[3]
		winner = playerOne if scoreOne > scoreTwo else playerTwo
		if(winner == username):
			wins+=1
		else:
			losses+=1

		if(playerOne == username):
			ptDiff += scoreOne - scoreTwo
		else:
			ptDiff += scoreTwo - scoreOne
	return wins, losses, ptDiff


def isValidUserName(str):
	if (str[:2] != '<@'):
		return False
	return True

#automatically adds you to group
def createGroup(groupname, username):
	c.execute("SELECT groupname FROM groups WHERE groupname=?", [groupname])
	results = c.fetchone()
	if (results != None):
		return "text", "Sorry, a group with this name already exists!"
	c.execute("INSERT INTO groups VALUES (?, ?)", [username, groupname])
	conn.commit()

def getMembersFromCommand(inputtedMembers):
	memberlist = []
	i = 0
	while i < len(inputtedMembers):
		m = inputtedMembers[i]
		if (not isValidUserName(m)):
			return "text", m + " is not a valid user."
		c.execute("SELECT name FROM players WHERE user_id=?", [m.strip('<@>')])
		membername = c.fetchone()[0]
		memberlist.append(membername)
		i += 1
	return memberlist

	

	
	
	
