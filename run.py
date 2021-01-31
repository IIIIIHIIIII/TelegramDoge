import datetime
import json
import math
import os
import requests
import time
from urllib.parse import urljoin

from block_io import BlockIo
from github import Github
import yaml
from markdown_it import MarkdownIt


# Global constants
TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
URL = f"https://api.telegram.org/bot{TOKEN}/"

UPDATES_OFFSET = 0


# Clients
BLOCKIO_API_KEY = os.environ['BLOCKIO_API_KEY']
BLOCKIO_PIN = os.environ['BLOCKIO_PIN']
VERSION = 2
block_io = BlockIo(BLOCKIO_API_KEY, BLOCKIO_PIN, VERSION)

GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
github_client = Github(GITHUB_ACCESS_TOKEN)


# Global objects
MD = MarkdownIt()
ACTIVE_USERS = {}


monikers_tuple  = [
	("sandwich","sandwiches",21),
	("coffee", "coffees",7),
	("tea", "teas",5),
	("lunch", "lunches",49)
]
monikers_dict = {n[i]: n[2] for n in monikers_tuple for i in range(2)}
monikers_flat = [monikers_tuple[i][j] for i in range(len(monikers_tuple)) for j in range(3)]
monikers_str  = '\n'.join(f"{i[0]}: {i[2]} doge" for i in monikers_tuple)


def getCount(chatid):
	n = []
	t = time.time()
	chat_users = ACTIVE_USERS[chatid]
	for i in chat_users:
		if t - chat_users[i] <= 600:
			n.append(i)
	return n

def sendMsg(message, chatid, mode=None):
	# Prepare request data
	endpoint = urljoin(URL, "sendMessage")
	data = {
		"chat_id": chatid,
		"text": message,
		"parse_mode": mode
	}

	# Send GET request
	resp = requests.get(endpoint, data=data)
	success = (200 <= resp.status_code <= 299)
	if success:
		print(f"just sent a message to - {chatid}")
	else:
		print(f"failed to send message to - {chatid}: " +
			  f"({resp.status_code}: {resp.reason})")

	return None

def returnBal(username):
	data = block_io.get_address_balance(labels=username)
	balance = data['data']['balances'][0]['available_balance']
	pending_balance = data['data']['balances'][0]['pending_received_balance']
	return (balance, pending_balance)

def myconverter(o):
	if isinstance(o, datetime.datetime):
		return o.__str__()

def process(message,firstname,username,chatid):
	message = message.split(" ")
	for i in range(message.count(' ')):
		message.remove(' ')

# /start
	if "/start" in message[0]:
		try:
			sendMsg("@" + str(username) + " welcome. I'm the the Peak Shift @ Work Bot\n\nHere's how it works.\n\nYou can use @dogeshift_bot by messaging it directly or in a group that it is a part of.\n\nAvailable Commands\n\n/register - Registers your username with the bot\n/tip @username 10 doge - use this to tip some doge from your balance to another user\n/address - Get your deposit address\n/withdraw 100 <address> - to withdraw your balance",chatid)
		except Exception as e:
			print("Error : 50 : "+str(e))

# /help
	elif "/help" in message[0]:
		try:
			sendMsg("@" + str(username) + " welcome. I'm the the Peak Shift @ Work Bot\n\nHere's how it works.\n\nYou can use @dogeshift_bot by messaging it directly or in a group that it is a part of.\n\nAvailable Commands\n\n/register - Registers your username with the bot\n/tip @username 10 doge - use this to tip some doge from your balance to another user\n/address - Get your deposit address\n/withdraw 100 <address> - to withdraw your balance",chatid)
		except Exception as e:
			print("Error : 55 : "+str(e))

# /register
	elif "/register" in message[0]:
		try:
			a = block_io.get_new_address(label=username)
			sendMsg("@"+username+" you are now registered.\nYour Address : <code>"+str(a['data']['address'])+"</code>",chatid)
		except:
			sendMsg("@"+username+" you are already registered.",chatid)

# /work
	elif "/work" in message[0]:
		repos = ['peakshift/telegram-dogecoin']
		msg1 = ""
		for rep in repos:
			repo = github_client.get_repo(rep)
			open_issues = repo.get_issues()
			a = 0
			msg1 += "\n<b>"+str(repo.full_name)+"</b>\n\n"
			for issue in open_issues:
				a += 1
				for x in issue.labels:
					if x.name == "reward":
						open_issues = repo.get_issue(number=int(issue.number))
						one = MD.parse(open_issues.body)
						ym = yaml.safe_load(one[0].content)
						ymm = json.loads(json.dumps(ym, default = myconverter))
						msg1 += "<code>#"+str(issue.number)+" > "+str(issue.title)+" -- "+str(ym['Reward'])+" 💰\n</code>"
		msg1 += "\n\nUse /body_[issue_number] , Example : <code>/body_13</code>"
		sendMsg(msg1,chatid,"html")

# /body
	elif "/body" in message[0]:
		spl = str(message[0]).split("_")
		if spl[1] != None:
			#sendMsg(spl[1],chatid)
			repo = github_client.get_repo('peakshift/telegram-dogecoin')
			open_issues = repo.get_issue(number=int(spl[1]))
			#one = MD.parse(open_issues.body)
			sendMsg(open_issues.body,chatid,"markdown")
		else:
			sendMsg("null",chatid)

# /balance
	elif "/balance" in message[0]:
		try:
			(balance, pending_balance) = returnBal(username)
			sendMsg("@"+username+"<b> Balance : </b>"+str(math.floor(float(balance)))+ " Doge \n(<b>Pending : </b>"+str(math.floor(float(pending_balance)))+" Doge)",chatid,"html")
		except Exception as e:
			print(e)
			sendMsg("@"+username+" you are not registered yet. use /register to register.",chatid)

# /tip
	elif "/tip" in message[0]:
		try:
			person = message[1].replace('@','')
			amount_msg = 1 if message[2] in ('a', 'an', '1') else message[2]
			amount = abs(float(amount_msg)) * monikers_dict.get(message[3], 1)

			if monikers_dict.get(message[3], 0) == 0:
				sin_plu = "doge"
			elif amount_msg == 1:
				sin_plu = monikers_tuple[monikers_flat.index(message[3])//3][0]
			else:
				sin_plu = monikers_tuple[monikers_flat.index(message[3])//3][1]

			block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_labels=person)
			sendMsg("@"+username+" tipped "+ str(amount_msg) + " " + sin_plu +
					("" if monikers_dict.get(message[3], 0) == 0 else f" ({str(amount)} doge)") +
					" to @"+person+"",chatid)
			(balance, pending_balance) = returnBal(person)
			sendMsg("@"+person+" Balance : "+math.floor(balance)+ "Doge ("+math.floor(pending_balance)+" Doge)",chatid)
		except ValueError:
			sendMsg("@"+username+" invalid amount.",chatid)
		except:
			sendMsg("@"+username+" insufficient balance or @"+person+" is not registered yet.",chatid)

# /address
	elif "/address" in message[0]:
		try:
			data = block_io.get_address_by_label(label=username)
			sendMsg("@"+username+" your address is "+data['data']['address']+"",chatid)
		except:
			sendMsg("@"+username+" you are not registered yet. use /register to register.",chatid)

# /withdraw
	elif "/withdraw" in message[0]:
		try:
			amount = abs(float(message[1]))
			address = message[2]
			data = block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_addresses=address)
		except ValueError:
			sendMsg("@"+username+" invalid amount.",chatid)
		except:
			sendMsg("@"+username+" insufficient balance or you are not registered yet.",chatid)

# /rain
	elif "/rain" in message[0]:
		try:
			users = getCount(chatid)
			if username in users:
				users.remove(username)
			number = len(users)

			amount = ("10," * (number - 1)) + '10'
			name = username
			username = ((username+',') * (number - 1)) + username
			if number < 2:
				sendMsg("@"+username+" less than 2 shibes are active.",chatid)
			else:
				print(amount)
				print(username)
				block_io.withdraw_from_labels(amounts=amount, from_labels=username, to_labels=','.join(users))
				sendMsg("@"+name+" is raining on "+','.join(users)+"",chatid)
		except:
			pass

# /monikers
	elif "/monikers" in message:
		sendMsg("--MONIKERS--\n" +
			monikers_str,chatid)

# /active
	elif "/active" in message:
		sendMsg("Current active : %d shibes" %(len(getCount(chatid))),chatid)
	else:
		try:
			ACTIVE_USERS[chatid][username] = time.time()
		except KeyError:
			ACTIVE_USERS[chatid] = {}
			ACTIVE_USERS[chatid][username] = time.time()

print("-- Bot Started Successfully >_<")

while True:
	try:
		updates_endpoint = urljoin(URL, "getUpdates")
		updates_data = {
			"offset": UPDATES_OFFSET,
		}

		resp = requests.get(updates_endpoint, data=updates_data)
		data = resp.json()

		UPDATES_OFFSET = data["result"][0]["update_id"] + 1
		try:
			username = data["result"][0]["message"]["from"]["username"]
		except:
			username = "UnKnown uname"

		try:
			firstname = data["result"][0]["message"]["from"]["first_name"]
		except Exception as e:
			print(e)
			firstname = "Unknown name"

		chatid = data["result"][0]["message"]["chat"]["id"]
		message = data["result"][0]["message"]["text"]
		process(message,firstname,username,chatid)

	except Exception as e:
		pass
