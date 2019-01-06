# -*- coding: utf-8 -*-
"""
Created on Sat Dec 29 22:05:40 2018

@author: Emma
"""

import json
import os
import numpy as np
import pandas as pd
import sys, getopt
import matplotlib.pyplot as plt

# the names of all the issues in the domain for later use
issues = ["Fruit", "Juice", "Topping1", "Topping2"]

possible_strategies = ["Conceder", "Hard-headed", "Tit-for-Tat", "Random"]

transition_model = pd.DataFrame({'St-1': ["Sc", "Sh", "St", "Sr"],
                                 'P(Sc)': [1, 0, 0, 0],
                                 'P(Sh)': [0, 1, 0, 0],
                                 'P(St)': [0, 0, 1, 0],
                                 'P(Sr)': [0, 0, 0, 1]})

transition_model.set_index('St-1', inplace=True)

sensor_model = pd.DataFrame({'St': ["Sc", "Sh", "St", "Sr"],
                             'P(concession)': [0, 0, 0, 0],
                             'P(fortunate)': [0, 0, 0, 0],
                             'P(unfortunate)': [0, 0, 0, 0],
                             'P(selfish)': [0, 0, 0, 0],
                             'P(silent)': [0, 0, 0, 0]})

sensor_model.set_index('St', inplace=True)

move_count = pd.DataFrame({'Strategy': ["conceder", "hardheaded", "tft", "random"],
                           'concession': [0, 0, 0, 0],
                           'fortunate': [0, 0, 0, 0],
                           'unfortunate': [0, 0, 0, 0],
                           'selfish': [0, 0, 0, 0],
                           'silent': [0, 0, 0, 0]})

move_count.set_index('Strategy', inplace=True)


# a function that returns the utility of a certain bid given a preference profile
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
    elif delta1 >= 0 and delta2 > 0:
        return "fortunate"
    elif delta1 <= 0 and delta2 < 0:
        return "unfortunate"
    elif delta1 > 0 and delta2 <= 0:
        return "selfish"
    elif delta1 == 0 and delta2 == 0:
        return "silent"
    else:
        return "ERROR"


def return_strategies(filename):
    useful, trash = filename.split(".")
    strategies = useful.split("_")
    if not strategies[1].isalpha():
        strategies[1] = strategies[1][:-1]
    return strategies


def train():
    global pref1, pref2
    # get all the logs
    logs = os.listdir("./logs/training_logs")
    # open the first one
    for log in logs:
        with open(("./logs/training_logs/%s" % log), "r") as read_file:
            data = json.load(read_file)

        s1, s2 = return_strategies(log)
        # get the preference profiles of both agents
        pref1 = data["Utility1"]
        pref2 = data["Utility2"]

        # moves agent 1 is making
        for i in range(len(data["bids"])):
            if i > 0:
                if "accept" in data["bids"][i]:
                    break
                current_round = data["bids"][i]
                prev_round = data["bids"][i - 1]
                move = (type_of_move(current_round["agent1"], prev_round["agent1"],
                                     pref1, pref2))
                move_count.loc[s1, move] += 1

        # moves agent 2 is making
        for i in range(len(data["bids"])):
            if i > 0:
                if "accept" in data["bids"][i]:
                    break
                current_round = data["bids"][i]
                prev_round = data["bids"][i - 1]

                move = (type_of_move(current_round["agent2"], prev_round["agent2"],
                                     pref2, pref1))
                move_count.loc[s2, move] += 1
    tempSc = move_count.loc["conceder"] / move_count.loc["conceder"].sum()
    tempSh = move_count.loc["hardheaded"] / move_count.loc["hardheaded"].sum()
    tempSt = move_count.loc["tft"] / move_count.loc["tft"].sum()
    tempSr = move_count.loc["random"] / move_count.loc["random"].sum()
    sensor_model.loc["Sc"] = tempSc.values
    sensor_model.loc["Sh"] = tempSh.values
    sensor_model.loc["St"] = tempSt.values
    sensor_model.loc["Sr"] = tempSr.values

    sensor_model.to_csv("sensor_model.csv")


def normalize_list(normalize_list):
    return [float(i) / sum(normalize_list) for i in normalize_list]


def make_sensor_matrix(move_type):
    sensor_matrix = np.zeros((4, 4), float)
    np.fill_diagonal(sensor_matrix, sensor_model[['P(' + move_type + ')']].values)
    return sensor_matrix


def forward_algorithm(data, i):
    current_round = data["bids"][i]
    prev_round = data["bids"][i - 1]

    pref1 = data["Utility1"]
    pref2 = data["Utility2"]

    move1 = (type_of_move(current_round["agent1"], prev_round["agent1"],
                          pref1, pref2))
    move2 = (type_of_move(current_round["agent2"], prev_round["agent2"],
                          pref2, pref1))

    sensor_matrix1 = make_sensor_matrix(move1)
    sensor_matrix2 = make_sensor_matrix(move2)

    if i > 2:
        fa_rec_result1, fa_rec_result2 = forward_algorithm(data, i - 1)
        fa_result1 = np.dot(transition_model.values.transpose(), sensor_matrix1)
        fa_result1 = np.dot(fa_result1, fa_rec_result1)
        fa_result2 = np.dot(transition_model.values.transpose(), sensor_matrix2)
        fa_result2 = np.dot(fa_result2, fa_rec_result2)
    else:
        fa_result1 = np.matrix([[0.25], [0.25], [0.25], [0.25]])
        fa_result2 = fa_result1
    return fa_result1, fa_result2



def forward_backward(data, t):
    #get pref profiles
    pref1 = data["Utility1"]
    pref2 = data["Utility2"]
    #init fv arrays per agent
    sv_1 = []
    sv_2 = []
    fv_1 = []
    fv_2 = []
    for i in range(t):
        fv_1.append(0)
        fv_2.append(0)
        sv_1.append(0)
        sv_2.append(0)
    #set prior
    fv_1[0] = np.identity(4)
    fv_2[0] = np.identity(4)
    b_1 = np.ones(4)
    b_2 = np.ones(4)

    #fw loop (store fv along the way to use in bw)
    for i in range(1, t):
        current_round = data["bids"][i]
        prev_round = data["bids"][i - 1]
        move1 = (type_of_move(current_round["agent1"], prev_round["agent1"],
                              pref1, pref2))
        move2 = (type_of_move(current_round["agent2"], prev_round["agent2"],
                              pref2, pref1))
        sensor_matrix1 = make_sensor_matrix(move1)
        sensor_matrix2 = make_sensor_matrix(move2)

        fv_1[i] = sensor_matrix1 * transition_model.values.transpose() * fv_1[i - 1]
        fv_2[i] = sensor_matrix2 * transition_model.values.transpose() * fv_2[i - 1]

    #bw loop, store smootherd estimates in sv_[agent id]
    for i in range(t-1, 0, -1):
        sv_1[i] = fv_1[i] * b_1
        sv_2[i] = fv_2[i] * b_2
        current_round = data["bids"][i]
        prev_round = data["bids"][i-1]
        move1 = (type_of_move(current_round["agent1"], prev_round["agent1"],
                              pref1, pref2))
        move2 = (type_of_move(current_round["agent2"], prev_round["agent2"],
                              pref2, pref1))
        sensor_matrix1 = make_sensor_matrix(move1)
        sensor_matrix2 = make_sensor_matrix(move2)
        b_1 = transition_model.values * sensor_matrix1 * b_1
        b_2 = transition_model.values * sensor_matrix2 * b_2

    return sv_1, sv_2


def test(file_name):
    if not os.path.isfile("sensor_model.csv"):
        print("No sensor model found, training first...")
        train()
    else:
        global sensor_model
        sensor_model = pd.read_csv("sensor_model.csv")

    with open(("./logs/test_logs/%s" % file_name), "r") as read_file:
        data = json.load(read_file)

        # Assuming the last bid entry is the "accepting" action
        n = len(data["bids"]) - 2

        # prediction1, prediction2 = forward_backward(data, 2)
        # prediction1_norm = normalize_list(np.diag(prediction1[1]))
        # prediction2_norm = normalize_list(np.diag(prediction2[1]))
        #
        # df = pd.DataFrame( columns = ["Conceder", "Hard-headed", "Tit-for-Tat", "Random", "Conceder_fb", "Hard-headed_fb", "Tit-for-Tat_fb", "Random_fb"])
        # df2 = pd.DataFrame(columns = possible_strategies)
        #
        #
        # for i in range(3, n):
        #     prediction1, prediction2 = forward_algorithm(data, i)
        #     prediction1_norm = normalize_list(np.diag(prediction1))
        #     prediction2_norm = normalize_list(np.diag(prediction2))
        #
        #     df_new = pd.DataFrame({'Agent 1': prediction1_norm, 'Agent 2': prediction2_norm}, index=possible_strategies)
        #
        #     appendedpred = prediction1_norm
        #
        #
        #     # df = pd.concat([df, df_new2])
        #
        #     prediction1, prediction2 = forward_backward(data, i)
        #     prediction1_norm = normalize_list(np.diag(prediction1[i-1]))
        #     prediction2_norm = normalize_list(np.diag(prediction2[i-1]))

            # df_new = pd.DataFrame({'Agent 1': prediction1_norm, 'Agent 2': prediction2_norm}, index=possible_strategies)

            # appendedpred = appendedpred + prediction1_norm
            #
            # df_new2 = pd.DataFrame([appendedpred],
            #                        columns=["Conceder", "Hard-headed", "Tit-for-Tat", "Random", "Conceder_fb",
            #                                 "Hard-headed_fb", "Tit-for-Tat_fb", "Random_fb"])
            #
            # df2 = pd.concat([df2, df_new2])


        print()
        # print(">>> FORWARD-BACKWARD given " + str(i + 1) + " round of bids :")
        # print(df)

        # df.index = range(n - 3)
        # df.plot()
        # df2.index = range(n - 3)
        # df2.plot(style=['-',':','-',':','-',':','-',':'], color=['blue', 'blue', 'red', 'red', 'yellow','yellow', 'green', 'green'])
        # plt.show()

        prediction1, prediction2 = forward_backward(data, n)

        prediction1_norm = normalize_list(np.diag(prediction1[n-1]))
        prediction2_norm = normalize_list(np.diag(prediction2[n-1]))

        df = pd.DataFrame({'Agent 1': prediction1_norm, 'Agent 2': prediction2_norm}, index=possible_strategies)
        print()
        print(">>> FORWARD-BACKWARD:")
        print(df)

        prediction1, prediction2 = forward_algorithm(data, n)

        prediction1_norm = normalize_list(np.diag(prediction1))
        prediction2_norm = normalize_list(np.diag(prediction2))

        df = pd.DataFrame({'Agent 1': prediction1_norm, 'Agent 2': prediction2_norm}, index=possible_strategies)
        print()
        print(">>> FORWARD:")
        print(df)




def usage():
    print("usage: python3 hmm.py [--train | --test filename | --help]")


def main():
    test("test7.json")
    sys.exit()
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:v", ["help", "train", "test="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "--train":
            print("Training...")
            train()
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in "--test":
            if os.path.isfile("./logs/test_logs/%s" % a):
                test(a)
            else:
                print("Invalid file: " + a)
        else:
            assert False, "Unhandled option"
    print()
    print("finished")

if __name__ == "__main__":
    main()
