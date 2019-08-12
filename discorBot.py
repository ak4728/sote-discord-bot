# Work with Python 3.6
import random
import asyncio
import aiohttp
import json
from discord import Game
from discord.ext.commands import Bot
import sqlite3 as lite
from datetime import datetime
from shareUpdate import shareUpdate
from minnowutils import *
from steem import Steem as steemlib
import os,shutil
import pandas as pd

def listtoChat(liste):
    text = ''
    for el in liste:
        text += (str(el)+'\n')
    return text

BOT_PREFIX = ("?", "!")
TOKEN = ''

client = Bot(command_prefix=BOT_PREFIX)
adminAccounts = ["steinhammer#8727","soteyapanbot","bahcehane","collectiveaction"]
allowedAccounts = ["steinhammer#8727","soteyapanbot","bahcehane","collectiveaction"]



def bringList():
    con = lite.connect('log.db')
    cur = con.cursor()
    x = cur.execute("SELECT * FROM main.blackboard;")
    returned = ''
    for el in x:
        returned = returned + el[0] + '\n'
    con.close()
    return returned


def dbHandler(author,addedby,fcn='add'):
#try:
    con = lite.connect('log.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS `main`.`blackboard` (
  `author` VARCHAR(300) NOT NULL,
  `addedby` VARCHAR(300) NOT NULL,
  `createdat` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
''')
    con.close()
    con = lite.connect('log.db')
    cur = con.cursor()
    dt1 = str(datetime.now())
    dt = "'"+dt1+"'"
    if fcn == 'add':
        query = '''INSERT INTO `main`.`blackboard` (`author`,`addedby`,`createdat`) VALUES ('{}', '{}', '{}');'''.format(author,addedby,dt1)
    if fcn == 'remove':
        query = '''DELETE FROM `main`.`blackboard`  WHERE author='{}';'''.format(author)
    cur.execute(query)
    con.commit()
    con.close()
    msg = 'Success'
#except:
#    msg = 'Error occured while adding the author to the database.'
    return msg


@client.command(name='8ball',
                description="Answers a yes/no question.",
                brief="Answers from the beyond.",
                aliases=['eight_ball', 'eightball', '8-ball'],
                pass_context=True)
async def eight_ball(context):
    possible_responses = [
        'That is a resounding no',
        'It is not looking likely',
        'Too hard to tell',
        'It is quite possible',
        'Definitely',
    ]
    await client.say(random.choice(possible_responses) + ", " + context.message.author.mention)


@client.event
async def on_message(message):
    config = pd.read_csv('config.csv')
    accountname = config['accountname'][0]
    if message.author == client.user:
        return
    if str(message.author) in adminAccounts:
        if message.content.lower() == "blackboard":
            returned = '__Blackboard__ \n'+ bringList()
            await client.send_message(message.channel, returned)
        if message.content.lower().startswith( "burda misin sote"):
            returned = 'Burdayim abicim, burdayim...'
            await client.send_message(message.channel, returned)
        if message.content.lower().startswith( "nasilsin sote"):
            returned = 'Iyi valla, sizleri sormali?'
            await client.send_message(message.channel, returned)
        if message.content.lower().startswith( "sampiyon kim"):
            returned = 'Galatasaray :yellow_heart: :heart:'
            await client.send_message(message.channel, returned)
        if message.content.startswith("blackboard add"):
            username = message.content.rsplit(" ")[2]
            msg = '{} is added to the blackboard list by {}.'.format(username, message.author.mention)
            returned = dbHandler(username,message.author,'add')
            if returned.startswith('Success'):
                await client.send_message(message.channel, msg)
            if returned.startswith('Error'):
                await client.send_message(message.channel, returned)
        if message.content.startswith("blackboard remove"):
            username = message.content.rsplit(" ")[2]
            msg = '{} is removed from the blackboard list by {}.'.format(username, message.author.mention)
            returned = dbHandler(username,message.author,'remove')
            if returned.startswith('Success'):
                await client.send_message(message.channel, msg)
            if returned.startswith('Error'):
                await client.send_message(message.channel, returned)
        if message.content.lower() == "share update":
            returned = shareUpdate("soteyapanbot")
    if str(message.author) in allowedAccounts:
        if message.content.lower() == "sote voteque":
            newQue = list( set(postGetter(accountname)) - set(tempLinks()) )
            returned = '__Current Vote Queue__ \n'+ listtoChat(newQue)
            await client.send_message(message.channel, returned)
        if message.content.lower() == "sote latest":
            returned = '__Temp Links__ \n'+ listtoChat(tempLinks())
            await client.send_message(message.channel, returned)
        if message.content.lower() == "sote flushdb":
            # DB Variables
            closer()
            exists = os.path.isfile('elektroyazilim.db')
            conn = lite.connect(setupDB(accountname))
            if exists:
                os.chmod('elektroyazilim.db', 0o777)
                os.remove('elektroyazilim.db')
                returned = "The database is successfully flushed."
            else:
                returned = "No database is found."          
            await client.send_message(message.channel, returned)                
        if message.content.lower().startswith("sote sendbids"):
            await client.send_message(message.channel, f'{time.asctime()} -> {message.author.mention}')  
            inp =message.content.lower().rsplit(' ')
            failed = 0
            botname = inp[2]
            iteration = inp[4]
            returned = 'Waiting for the API response.'
            # Try to get the amount
            try:
                if isinstance(float(inp[3]), float) == True:
                    amount  = float(inp[3])
            except:
                failed = 1
                returned = 'The **amount** value should be the 4th item in the order\n\n __Example:__\n sote sendbids botname __*bidvalue*__ iteration linkname'
            # Try to get the memo
            try:
                if inp[5].startswith('http'):
                    memo = inp[5]
                else:
                    returned = 'The link should start with http.'
            except:
                failed = 1
                returned = 'The **link** should be the 5th item in the order\n\n __Example:__\n sote sendbids botname bidvalue iteration __*linkname*__'
            await client.send_message(message.channel, returned)
            if failed == 0:
                stm = steemlib()
                voted = votedList()
                voteQue = postGetter(accountname)
                balance = samount(stm.get_account(accountname)["balance"]).amount
                finished,memo2=sendBids(stm,balance,voteQue,voted,amount,critical=2,iteration=int(inp[4]), accountname= accountname,botname=botname,memo=memo)
                returned = 'The bid for {} has successfully transferred.'.format(memo2) 
            await client.send_message(message.channel, returned)
client.run(TOKEN)

@client.command()
async def square(number):
    squared_value = int(number) * int(number)
    await client.say(str(number) + " squared is " + str(squared_value))


@client.event
async def on_ready():
    await client.change_presence(game=Game(name="with humans"))
    print("Logged in as " + client.user.name)


@client.command()
async def bitcoin():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    async with aiohttp.ClientSession() as session:  # Async HTTP request
        raw_response = await session.get(url)
        response = await raw_response.text()
        response = json.loads(response)
        await client.say("Bitcoin price is: $" + response['bpi']['USD']['rate'])


async def list_servers():
    await client.wait_until_ready()
    while not client.is_closed:
        print("Current servers:")
        for server in client.servers:
            print(server.name)
        await asyncio.sleep(600)

try:
    client.loop.create_task(list_servers())
    client.run(TOKEN)
except:
    time.sleep(30)