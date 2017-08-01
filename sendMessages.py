import os,time,sqlite3
from slackclient import SlackClient
from config import BOT_TOKEN
slack = SlackClient(BOT_TOKEN)
if __name__ == "__main__":
	print('hi')
	print(slack.rtm_connect())
	BOT_ID = slack.api_call("auth.test").get('user_id')
	for user in slack.api_call("users.list").get("members"):
		slack.api_call(
		"chat.postMessage",
		channel=user['id'],
		as_user = True,
		text="Hi! I'm PongPal. Do you play ping pong at Lucid? If so, type 'help' to get started!"
	)
	while True:
		print("finished")
		time.sleep(1)