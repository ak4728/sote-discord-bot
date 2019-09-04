# Work with Python 3.6
import random
import asyncio
import aiohttp
import json
from discord import Game
from discord.ext.commands import Bot
from datetime import datetime
from shareUpdate import shareUpdate
from minnowutils import *
from steem import Steem as steemlib
import os,shutil
import pandas as pd


BOT_PREFIX = ("?", "!")
TOKEN = os.environ['discor_API_TOKEN']

client = Bot(command_prefix=BOT_PREFIX)
adminAccounts = ["steinhammer#8727"]
allowedAccounts = ["steinhammer#8727","etasarim#2115"]


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
        if len(message.content)==14 and message.content.lower() == "sote kar zarar":
            accountname = str(message.author).rsplit("#")[0]
            print(message.author,' requested rshare calculation.')
            print(len(message.content))
            returned = 'Thank you for your message '
            try:
                rewards,rewardsold,steemp = getBreakeven()
                returned += str(message.author.mention)+'\nThe breakeven point requires = {}k Steem power.\nThis equals to= ${:0.2f}'.format(int(steemp/1000), rewards)
            except:
                returned += "\n We cannot calculate the breakeven point at the moment. Sorry for the inconvenience."
            await client.send_message(message.channel, returned)
        if len(message.content)==11 and message.content.lower() == "sote rshare":
            accountname = str(message.author).rsplit("#")[0]
            print(message.author,' requested rshare calculation.')
            print(len(message.content))
            returned = 'Thank you for your message '
            try:
                rshares = getRshares(accountname)
                returned += str(message.author.mention)+'\n Your rshare is = {}'.format(rshares)
            except:
                returned += "\n We cannot find your username on steemit."
            await client.send_message(message.channel, returned)
        if len(message.content)>11:
            if message.content.startswith("sote"):
                if message.content.endswith("rshare"):
                    accountname = message.content.rsplit(" ")[1]
                    print(message.author,' requested rshare calculation.')
                    returned = 'Thank you for your message '
                    try:
                        rshares = getRshares(accountname)
                        returned += str(message.author.mention)+"\n {}'s rshare is = {}".format(accountname,rshares)
                    except:
                        returned += "\n We cannot find your username on steemit."
                    await client.send_message(message.channel, returned)
        if message.content.lower() == "sote voteque":
            newQue = list( set(postGetter(accountname)) - set(tempLinks()) )
            returned = '__Current Vote Queue__ \n'+ listtoChat(newQue)
            await client.send_message(message.channel, returned)
        if message.content.lower() == "sote latest":
            returned = '__Temp Links__ \n'+ listtoChat(tempLinks())
            await client.send_message(message.channel, oreturned)            
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