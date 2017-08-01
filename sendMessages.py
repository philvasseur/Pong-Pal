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
		text="If you ever want to play ping pong, just message me `status`. If you want to be notified when the room is open, type `notify`. I'll be out of service for a few minutes, but then I'll be back online! And don't worry, this is the last unsolicited message you'll receieve :smiley:"
	)
		print("Messaged "+ user['name']);
	while True:
		print("finished")
		time.sleep(1)