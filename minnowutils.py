# first, we initialize Steem class
import urllib.request, json, datetime    
import time
from random import *
import string
import random
import requests
from bs4 import BeautifulSoup
import steem_func
from dateutil.parser import parse
from datetime import datetime, timedelta
from dhooks import Webhook
import pprint
import pytz
from beem.vote import AccountVotes, ActiveVotes
import pandas as pd  
import math
import datetime
from beem import Steem
import sqlite3
from retrying import retry
from steem import Steem as steemlib
from steem.amount import Amount as samount
from steem.converter import Converter


#steem.set_default_nodes(['https://steemd.privex.io'])

def listtoChat(liste):
    '''
    list to chat
    ''' 
    text = ''
    for el in liste:
        text += (str(el)+'\n')
    return text

def bringList():
    '''
    Blackboard DB brings the list
    ''' 
    con = sqlite3.connect('log.db')
    cur = con.cursor()
    x = cur.execute("SELECT * FROM main.blackboard;")
    returned = ''
    for el in x:
        returned = returned + el[0] + '\n'
    con.close()
    return returned


def dbHandler(author,addedby,fcn='add'):
    '''
    Blackboard DB
    ''' 
    try:
        con = sqlite3.connect('log.db')
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS `main`.`blackboard` (
      `author` VARCHAR(300) NOT NULL,
      `addedby` VARCHAR(300) NOT NULL,
      `createdat` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
    ''')
        con.close()
        con = sqlite3.connect('log.db')
        cur = con.cursor()
        dt = str(datetime.datetime.now())
        bList = [x[0] for x in cur.execute("SELECT * FROM main.blackboard;")]
        query = ''
        if fcn == 'add':
            if author in bList:
                msg = 'Error, the author is already in the list.'
            else:
                query = '''INSERT INTO `main`.`blackboard` (`author`,`addedby`,`createdat`) VALUES ('{}', '{}', '{}');'''.format(author,addedby,dt)
                msg = 'Success.'           
        if fcn == 'remove':
            if author in bList:
                query = '''DELETE FROM `main`.`blackboard`  WHERE author='{}';'''.format(author)
                msg = 'Success.'
            else:
                msg = 'Error, the author is not in the list.'
        cur.execute(query)
        con.commit()
        con.close()
    except Exception as e:
        msg = 'Error occured while adding the author to the database.\n'+str(e)
    
    return msg


def setupDB(accountname):
    # DB Variables
    dbname = accountname + '.db'
    return dbname

config = pd.read_csv('config.csv')
accountname = config['accountname'][0]
key = config['key'][0]

# DB Variables
conn = sqlite3.connect(setupDB(accountname))
c = conn.cursor()
c.execute('''CREATE TABLE  IF NOT EXISTS  votedque (link text)''')
conn.commit()
c.execute('''CREATE TABLE IF NOT EXISTS sentlinks  (link text, val real)''')
conn.commit()


def closer():
    conn.close()

def postGetter(accountname='soteyapanbot'):
    """
        Outputs comments by the author.
        Finds the ones that are not voted by minnowvotes.
        indicator goes up by 1 everytime a minnowvotes has seen.
        aVotes = [{voter:x, value:y},
                    {voter:z,value:k}]
        voteQue = [url1, url2, url3, ...]

    """
    s = steemlib()
    utc=pytz.UTC
    dt5 = utc.localize(datetime.datetime.now() - datetime.timedelta(days=6))
    dt4 = utc.localize(datetime.datetime.now() - datetime.timedelta(days=0))
    last5days = utc.localize(datetime.datetime.now() - datetime.timedelta(days=6))
    # Get posts of selected account
    posts = s.get_discussions_by_author_before_date(author=accountname, 
                                                    start_permlink = '', 
                                                    before_date =dt5.strftime("%Y-%m-%dT%H:%M:%S"),
                                                    limit=50 )
    voteQue = []
    

    for post in posts:
        adjDt =  utc.localize(parse(post['created'])-datetime.timedelta(hours=4))
        if(adjDt>dt5)==True:
            if(adjDt<dt4)==True:
                url = 'https://steemit.com'+post['url']
                aVotes = post['active_votes']
                indicator = 0
                if len(aVotes)>0:
                    for i in range(len(aVotes)):
                        if aVotes[i]['voter']=='minnowvotes':
                            indicator += 1
                if indicator>=1:
                    pass
                else:
                    voteQue.append(url)
        
    return voteQue

def commentGetter(accountname):
    """
        Outputs comments by the author.
        Finds the ones that are not voted by minnowvotes.
        indicator goes up by 1 everytime a minnowvotes has seen.
        aVotes = [{voter:x, value:y},
                    {voter:z,value:k}]
        voteQue = [url1, url2, url3, ...]

    """
    s = steemlib()
    utc=pytz.UTC
    dt5 = utc.localize(datetime.datetime.now() - datetime.timedelta(days=6))
    dt4 = utc.localize(datetime.datetime.now() - datetime.timedelta(days=0))
    stop = datetime.datetime.utcnow() - timedelta(days=5)
    voteQue = []
    query2 = {
    "limit":50, #number of comments
    "start_author":accountname #selected user
    }
    # get comments of selected account
    comments = s.get_discussions_by_comments(query2)
    for comment in comments:
        indicator = 0
        url = "https://steemit.com"+comment['url']
        aVotes = comment['active_votes']
        adjDt =  utc.localize(parse(comment['created'])-datetime.timedelta(hours=4))
        if(adjDt>dt5)==True:
            if(adjDt<dt4)==True:
                if len(aVotes)>0:
                    for i in range(len(aVotes)):
                        if aVotes[i]['voter']=='minnowvotes':
                            indicator += 1
                if indicator>=1:
                    pass
                else:
                    voteQue.append(url)
    return voteQue

def votedList():
    """
        Retrieves the voted links for the active round and the next.
        Returns votedList list.
    """
    x = pd.read_sql_query("SELECT * FROM votedque;", conn)
    url = "https://steembottracker.net/bid_bots/minnowvotes"
    with urllib.request.urlopen(url) as url2:
        data = json.loads(url2.read().decode())
        for el in data:
            for i in range(len(data[el])):
                text = str(data[el][i]['url'])
                if text not in x['link'].tolist():
                    c.execute("INSERT INTO votedque VALUES ('{}')".format(text))
                    conn.commit()
    x =pd.read_sql_query("SELECT * FROM votedque;", conn)
    return(x['link'].tolist())


def tempLinks():
    """
        Retrieves the sent links in the last 3 rounds.
        Returns sentLinks in the last 3 rounds query output.
    """
    rowids = pd.read_sql_query("SELECT rowid FROM sentlinks;", conn)
    last3 = rowids['rowid'].tolist()[-3:]
    if len(last3)<3:
        for i in range(3-len(last3)):
            c.execute("INSERT INTO sentlinks VALUES ('{}', '{}')".format('testlink','val'))
            conn.commit()
        rowids = pd.read_sql_query("SELECT rowid FROM sentlinks;", conn)
        last3 = rowids['rowid'].tolist()[-3:]
    linktable = pd.read_sql_query("SELECT * FROM sentlinks WHERE rowid in {};".format(tuple(last3)), conn)
    return linktable['link'].tolist()

def defineWallet(key,stm,accountname,amount,memo,toacc='minnowvotes',amounttype = 'STEEM'):
    """
        This may be updated to transfer.
        Defines wallet and executes the transfer.
    """
    steem = steemlib(keys=[key])
    steem.transfer(toacc, amount, amounttype, memo,account=accountname)
    
def sendBids(stm,balance,voteQue,voted,amount = 4.5,iteration = 4,critical = 4.5,timesleep=3,
             accountname='soteyapanbot',botname='minnowvotes',memo='notgiven'):
    """
        This is the main function that sends out bids to the bot.
        Checks if memo is voted before or balance is lower than the critical value.
        Outputs finished and memo.
        finished = 0 : No successful transfers
        finished > 1 : Successful transfers
    """
    finished = 0
    newQue = list( set(voteQue) - set(tempLinks()) )
    if memo == 'notgiven':
        memo = newQue[-1]
    if balance >= critical:
        if memo not in voted:
            print('STEEM: ',balance)
            for i in range(iteration):
                amount = amount + 0.001                    
                defineWallet(key,stm,accountname,amount,memo,toacc=botname)#botname)
                print((' The bot is successfully transferred {} steem for:\n {}').format(amount,memo))
                if memo not in tempLinks():
                    c.execute("INSERT INTO sentlinks VALUES ('{}', '{}')".format(memo,amount))   
                    conn.commit()    
                else:
                    pass
                time.sleep(timesleep)
                finished = finished + 1
    return finished, memo

def getBotTime(botname,accountname='soteyapanbot', amount = 4.5,iteration = 4,critical = 4.5, timesleep=3,minsBefore = 0.97):
    """
        Retrieves bot voting time given the botname.
    """    
    url = "https://steembottracker.net/bid_bots"
    stm = steemlib()
    with urllib.request.urlopen(url) as url2:
        data = json.loads(url2.read().decode())
        for i in range(len(data)):
            if data[i]['name']==botname:
                minsLeft = data[i]['next']/(60*1000)
                if minsLeft < minsBefore:
                    # Retrieve updated balance, voted List and vote queue
                    balance = samount(stm.get_account(accountname)["balance"]).amount
                    voted = votedList()
                    voteQue = postGetter(accountname)
                    print(("{} minutes left for the next minnowvotes round.").format(minsLeft))
                    # Send bids for the existing round
                    finished, memo = sendBids(stm,balance,voteQue,voted,amount,iteration,critical,timesleep,accountname,botname)
                    # Finished will be bigger than one after a successful round
                    if finished>=1:
                        print("Sleeping after successful round for 5 minutes.")
                        time.sleep(300) #180
                else:
                    time.sleep(1)



def getRshares(accountname='soteyapanbot'):
    s = steemlib()
    c = Converter()
    account = s.get_account(accountname)
    vests = samount(account['vesting_shares']).amount
    delegated_vests = samount(account['delegated_vesting_shares']).amount
    received_vests = samount(account['received_vesting_shares']).amount
    current_vests = float(vests) - float(delegated_vests) + float(received_vests)
    steem_power = c.vests_to_sp(current_vests)
    rshares = c.sp_to_rshares(steem_power)
    return(rshares)


def rshares_to_sp(rshares=1000000):
    used_power = 200
    vesting_shares = rshares  / used_power /100
    sp  = c.vests_to_sp(vesting_shares)
    return(sp)

def getClaims(rshares):
    cnst = 2000000000000
    claims = (rshares* (rshares +2*cnst)) / (rshares + 4 * cnst)
    return(claims)

def rwdComp(claims,rshares,steemPower,steemPrice,s ,c ):
    cnstOld = 1.59838903372e-12
    steemRewards = steemPrice * claims * float(s.get_reward_fund('post')['reward_balance'].replace("STEEM","")) /float(s.get_reward_fund('post')['recent_claims'])
    steemRewardsOld = cnstOld*steemPrice * 200 * 100 * steemPower/ (samount(c.steemd.get_dynamic_global_properties()['total_vesting_fund_steem']).amount/samount(c.steemd.get_dynamic_global_properties()['total_vesting_shares']).amount)
    return(steemRewards, steemRewardsOld)

def getBreakeven():
    s = steemlib()
    c = Converter()
    steemPrice = float(s.get_current_median_history_price()['base'].replace("SBD",""))/float(s.get_current_median_history_price()['quote'].replace("STEEM",""))
    for i in range(400000,500000,1000):
        rshares = c.sp_to_rshares(i)
        claims = getClaims(rshares)
        steemRewards, steemRewardsOld = rwdComp(claims,rshares,i,steemPrice, s ,c  )
        if math.fabs(steemRewards - steemRewardsOld) <= 0.001:
            print(steemRewards, steemRewardsOld,i)
            break
    return(steemRewards, steemRewardsOld, i)