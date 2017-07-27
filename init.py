import os,time,sqlite3
from slackclient import SlackClient
from datetime import datetime
from config import BOT_TOKEN
import commands as commands

conn = sqlite3.connect('pingpong.db')
c = conn.cursor()
slack = SlackClient(BOT_TOKEN)
BOT_ID = None

class Message(object):
	def __init__(self,body):
		self.text = body.get('text')
		self.channel = body.get('channel')
		self.type = body.get("type")
		self.subtype = body.get("subtype")
		self.sender_id = body.get("user")
		self.receiver_id = BOT_ID
		self.isDM = self.channel and self.channel[0] == 'D'
		self.isNewMessage = self.subtype == None and self.type == "message"

def parseMessage(message):
	commandMap = {"help":commands.sendHelpOptions,"match":commands.handleMatchInput,"status":commands.sendRoomStatus, "history":commands.getMatchHistory,'stats':commands.getPlayerStats, "confirm":commands.confirmMatch}
	text = message.text
	if len(text.split()) == 0:
		sendMessage("Sorry, I didn't recognize your command. Type 'help' for a list of options.")
		return
	command = text.split()[0].lower()
	if command in commandMap:
		type,output = commandMap[command](message)
		if(type == 'text'):
			sendMessage(output,message.channel)
		elif(type == 'file'):
			uploadFile(output,message.channel)
	else:
		sendMessage("Sorry, I didn't recognize your command. Type 'help' for a list of options.",message.channel)

def uploadFile(data,channel):
	slack.api_call("files.upload", initial_comment=data['comment'],filename=data['filename'], channels=channel, file= data['file'])

def sendMessage(text,channel):
	slack.server.send_to_websocket({"type": "message", "channel": channel, "markdwn": True, "text": text})

def sendConfirmation(text, opponentId):
	slack.api_call(
		"chat.postMessage",
		channel=opponentId,
		as_user = True,
		text=text
	)

def getBotId():
	return BOT_ID

if __name__ == "__main__":
	if slack.rtm_connect():
		BOT_ID = slack.api_call("auth.test").get('user_id')
		users = []
		for user in slack.api_call("users.list").get("members"):
			users.append((datetime.now(),user["name"],user["id"],None))
		c.executemany("INSERT OR IGNORE INTO players VALUES(?,?,?,?)",users)
		conn.commit()
		conn.close()
		print('PongPal - Connected and Ready To Go!')
		while(True):
			for event in slack.rtm_read():
				msg = Message(event)
				if msg.sender_id == BOT_ID or not msg.isNewMessage or not msg.isDM:
					continue;
				parseMessage(msg)
			time.sleep(1)
	else:
		print("Connection failed. Invalid Slack token or bot ID?")
		conn.close()


