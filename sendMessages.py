import os,time,sqlite3
from slackclient import SlackClient
from config import BOT_TOKEN
slack = SlackClient(BOT_TOKEN)
if __name__ == "__main__":
	print(slack.rtm_connect())
	BOT_ID = slack.api_call("auth.test").get('user_id')
	slack.api_call(
	"chat.postMessage",
	channel="U5N89N3K2",
	as_user = True,
	text="Test Message To Stephen Slater"
	)
	print("Messaged Stephen");
