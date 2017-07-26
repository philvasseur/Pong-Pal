import os,time,sqlite3
from slackclient import SlackClient
from config import BOT_TOKEN

slack = SlackClient(BOT_TOKEN)

if __name__ == "__main__":
	if slack.rtm_connect():
		print('Connected and Ready To Go!')
		while True:
			time.sleep(1)
	else:
       print("Connection failed. Invalid Slack token or bot ID?")
