# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 22:05:40 2018

@author: Emma
"""

import json
import os


#the names of all the issues in the domain for later use
issues = ["Fruit", "Juice", "Topping1", "Topping2"]


#a function that returns the utility of a certain bid given a preference profile
def calc_util(bid, pref):
    bids = bid.split(",")
    util = (pref[issues[0]][bids[0]] * pref[issues[0]]["weight"]
            + pref[issues[1]][bids[1]] * pref[issues[1]]["weight"]
            + pref[issues[2]][bids[2]] * pref[issues[2]]["weight"]
            + pref[issues[3]][bids[3]] * pref[issues[3]]["weight"])
    return util

def type_of_move(bid, prevbid, pref1, pref2):
    delta1 = calc_util(bid, pref1) - calc_util(prevbid, pref1)
    delta2 = calc_util(bid, pref2) - calc_util(prevbid, pref2)
    
    if delta1 < 0 and delta2 >= 0:
        return "concession"
    elif delta1  >= 0 and delta2 > 0:
        return "fortunate"
    elif delta1 <= 0 and delta2 < 0:
        return "unfortunate"
    elif delta1 > 0 and delta2 <= 0:
        return "selfish"
    elif delta1 == 0 and delta2 == 0:
        return "silent"
    else:
        return "ERROR"

#get all the logs
logs = os.listdir("./logs/training_logs")

#open the first one
with open(("./logs/training_logs/%s" % logs[0]), "r") as read_file:
    data = json.load(read_file)

#get the preference profiles of both agents
pref1 = data["Utility1"]
pref2 = data["Utility2"]


#calculate the utility of agent 1's bid for both agents
for turn in data["bids"]:
    if "accept" in turn:
        break
    util_1 = calc_util(turn["agent1"], pref1)
    util_2 = calc_util(turn["agent1"], pref2)
    print("Agent 1 util: ",util_1," Agent 2 util: ",util_2)

#This prints the type of moves agent 1 is making
for i in range(len(data["bids"])):
    if i > 0:
        if "accept" in data["bids"][i]:
            break       
        current_round = data["bids"][i]
        prev_round = data["bids"][i-1]
        print(type_of_move(current_round["agent1"], prev_round["agent1"],
                           pref1, pref2))
        
        
    
    