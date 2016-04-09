import requests
import time
from block_io import BlockIo

token = "" #Telegram bot token
url = "https://api.telegram.org/bot%s/" %(token)
n = 0
version = 2
block_io = BlockIo('Blockio api key', 'Blockio pin', version)
active_users = {}

def getCount():
    n = []
    t = time.time()
    for i in active_users:
        if t - active_users[i] <= 600:
            n.append(i)
    return n

def sendMsg(message,chatid):
    requests.get(url + "sendMessage", data={"chat_id":chatid,"text":message})

def process(message,username,chatid):
    message = message.split(" ")
    for i in range(message.count(' ')):
        message.remove(' ')

    if "/register" in message[0]:
        try:
            block_io.get_new_address(label=username)
            sendMsg("@"+username+" you are now registered.",chatid)
        except:
            sendMsg("@"+username+" you are already registered.",chatid)
    elif "/balance" in message[0]:
        try:
            data = block_io.get_address_balance(labels=username)
            balance = data['data']['balances'][0]['available_balance']
            pending_balance = data['data']['balances'][0]['pending_received_balance']
            sendMsg("@"+username+" Balance : "+balance+ "Doge ("+pending_balance+" Doge)",chatid)
        except:
            sendMsg("@"+username+" you are not regsitered yet. use /register to register.",chatid)
    elif "/tip" in message[0]:
        try:
            person = message[1].replace('@','')
            amount = abs(float(message[2]))
            block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_labels=person)
            sendMsg("@"+username+" tipped "+ str(amount) + " doge to @"+person+"",chatid)
        except ValueError:
            sendMsg("@"+username+" invalid amount.",chatid)
        except:
            sendMsg("@"+username+" insufficient balance or @"+person+" is not registered yet.",chatid)
    elif "/address" in message[0]:
        try:
            data = block_io.get_address_by_label(label=username)
            sendMsg("@"+username+" your address is "+data['data']['address']+"",chatid)
        except:
            sendMsg("@"+username+" you are not registered yet. use /register to register.",chatid)
    elif "/withdraw" in message[0]:
        try:
            amount = abs(float(message[3]))
            address = message[2]
            data = block_io.withdraw_from_labels(amounts=str(amount), from_labels=username, to_addresses=address)
        except ValueError:
            sendMsg("@"+username+" invalid amount.",chatid)
        except:
            sendMsg("@"+username+" insufficient balance or you are not registered yet.",chatid)

    elif "/rain" in message[0]:
        try:
            users = getCount()
            if username in users:
                users.remove(username)
            number = len(users)

            amount = ("10," * (number - 1)) + '10'
            username = ((username+',') * (number - 1)) + username
            if number < 2:
                sendMsg("@"+username+" less than 2 shibes are active.",chatid)
            else:
                print(amount)
                print(username)
                block_io.withdraw_from_labels(amounts=amount, from_labels=username, to_labels=','.join(users))
                sendMsg("@"+username+" is raining on "+','.join(users)+"",chatid)
        except:
            pass

    elif "/active" in message:
        sendMsg("Current active : %d shibes" %(len(getCount())),chatid)
    else:
	global active_users
        active_users[username] = time.time()

while True:
    try:
        data = requests.get(url+"getUpdates", data={"offset":n}).json()
        n = data["result"][0]["update_id"] + 1
        username = data["result"][0]["message"]["from"]['username']
        chatid = data["result"][0]["message"]["chat"]["id"]
        message = data["result"][0]["message"]["text"]
        process(message,username,chatid)
    except:
        print(data)
