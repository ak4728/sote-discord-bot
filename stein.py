import pandas as pd
import natsort
from collections import OrderedDict
import json
from rabona_python import RabonaClient
from lighthive.datastructures import Operation
from lighthive.client import Client
from datetime import datetime
import time 

ACCOUNTS = [
    {
        "username": "",
        "auto_train_type": "451",
        "posting_key": ""
    }    
    
    
]

types = {"1":"GOAL", "2":"DEF","3":"MID","4":"OFF"}

tactics = {
    "352": {"1": ["p1"],
            "2": ["p5","p2","p4"],
            "3" : ["p10","p6","p8","p7","p3"],
            "4" : ["p9","p11"]
           },
    "451":  {"1": ["p1"],
            "2": ["p4","p5","p2","p3"],
            "3" : ["p10","p6","p8","p7","p11"],
            "4" : ["p9"]
           }
   }



def getStartingEleven(user="soteyapanbot"):
    lineup = r.team(user=user,frozen=0)
    linedf = pd.DataFrame.from_dict(lineup['players'])
    sl = r.saved_lineup(user=user)
    del sl['formation']
    ini_list = [int(x.replace("p","")) for x in list(sl.keys()) ]
    starting11 = dict(zip(ini_list, list(sl.values()))) 
    starting11 =  dict(zip(starting11.values(), starting11.keys()))
    linedf['starting11'] = linedf['uid'].map(starting11)
    return(linedf, sl)


def create_custom_json_op(username, json_type,auto_type,mydict,matchid=""):
    if json_type == "set_formation":
        cmd = {"tr_var1":matchid, "tr_var2":auto_type,"tr_var3":mydict}
    else:
        cmd = {"tr_var1":auto_type, "tr_var2":mydict}
    train_json = json.dumps(
         {"username":username,"type":json_type,"command": cmd} )
    train_op = Operation('custom_json', {
        'required_auths': [],
        'required_posting_auths': [username, ],
        'id': 'rabona',
        'json': train_json,
    })
    return train_op

def inj_block_check(df, linedf, sl, btype="blocked"):
    if len(df) > 0:
        # List of suspended players
        for i in range(len(df)):
            print("Player %s is %s with uid=%s and position=%s" % 
                  (df['name'][i],btype,df['uid'][i], types[df['type'][i]]))
            # List of alternatives
            alts = linedf[linedf['type']==df['type'][i]].reset_index(drop=True)
            if(len(alts)>0):
                alts = alts[alts['starting11']>=12].reset_index(drop=True).sort_values(by=['overall_strength']).loc[0]
                print("The best alternative is %s with overall strength %s and uid %s" % 
                      (alts['name'],alts['overall_strength'], alts['uid']))
                # Swap players
                sl["p"+str(df['starting11'][i])] = alts['uid']
                sl["p"+str(alts['starting11'])] = df['uid'][i]

                keys = natsort.natsorted(sl.keys())    
                sl = dict(OrderedDict((k, sl[k]) for k in keys))
                for k, v in sl.items():
                    if v is None:
                        sl[k] = ""
                op = create_custom_json_op(account['username'],"save_formation","451",sl)
                c = Client(keys=[account["posting_key"]])
                c.broadcast(op=op)               
                print("[%s] OUT - [%s] IN" % (df['name'][i],alts['name'] ))
            else:
                "There are no subs that can be used in the squad."
    else:
        print("There are no %s player(s)." % (btype))
    linedf,sl = getStartingEleven(user=account['username'])
    return(linedf,sl)


def get_best_players(tnumber):
    defDict = {}
    formation = r.saved_lineup(user=account['username'])['formation']
    if tnumber == "1":
        ndefs = 1
    else:
        ndefs = int(str(formation)[int(tnumber)-2])
    # Find the best defenders
    defenders = linedf.loc[linedf['type']== tnumber].sort_values(by=['overall_strength'],ascending=False).reset_index(drop=True)
    if len(defenders) > ndefs:
        defenders = defenders.loc[0:ndefs-1]
        for i in range(len(defenders)):
            defDict[tactics[str(formation)][tnumber][i]] = defenders["uid"][i]
    else:
        "Not enough players"
    return(defDict)  


r = RabonaClient()

account = ACCOUNTS[1]

##############################################
# Check if there are any injuries or bookings#
##############################################

# Blockage check
linedf, sl = getStartingEleven(user=account['username'])

blocked =   linedf[linedf['games_blocked']>=1].reset_index(drop=True)
injured =   linedf[linedf['games_injured']>=1].reset_index(drop=True)

linedf,sl = inj_block_check(blocked, linedf, sl, btype="suspended")
linedf,sl = inj_block_check(injured, linedf, sl, btype="injured")

############################################
# Check if the squad is the best it can be #
############################################

# formation is 4-5-1
# find all the players that are not injured or booked

# Starting Eleven
linedf, sl = getStartingEleven(user=account['username'])

# Healthy and not suspended players
linedf = linedf.loc[linedf['games_blocked']==0]
linedf = linedf.loc[linedf['games_injured']==0]

# Get the formation
formation = r.saved_lineup(user=account['username'])['formation']

# Update starting eleven
sl = {}
for k,v in types.items():
    pdict = get_best_players(k)
    sl.update(pdict)

# Add subs
subs = linedf[~linedf['uid'].isin(list(sl.values()))]['uid'].reset_index(drop=True)
for i in range(len(subs)):
    sl["p"+str(i+12)] = subs[i]

# Add empty subs
nplayers = []
for k,v in sl.items():
    nplayers.append(int(k[1:]))
for i in range(max(nplayers)+1,22):
    sl["p"+str(i)] = ""

# Update Squad
keys = natsort.natsorted(sl.keys())  
sl = dict(OrderedDict((k, sl[k]) for k in keys))
op = create_custom_json_op(account['username'],"save_formation",str(formation),sl)
c = Client(keys=[account["posting_key"]])
c.broadcast(op=op)

########################################
# Setup the Squad for Upcoming Matches #
########################################
    
matches = r.matches(user=account['username'],limit=30, order="DESC")
games = pd.DataFrame.from_dict(matches['matches'])
played = list(games[games.goals_team_1 >=0]['match_id'].reset_index(drop=True))


for match in games['match_id']:
    if match not in played:
        op = create_custom_json_op(account['username'],"set_formation",str(formation),sl,str(match))
        c = Client(keys=[account["posting_key"]])
        c.broadcast(op=op)
    