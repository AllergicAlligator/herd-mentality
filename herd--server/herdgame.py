import random
from prompts import *
from functions import *

numofplayers = int(input("number of players: "))

scoreboard = {}
players = {}

WINNING_SCORE = 8

# setup scoreboard once
for i in range(numofplayers):
    scoreboard[f"player{i+1}"] = 0


round_number = 1

while True:

    print("\n" + "=" * 40)
    print(f"ROUND {round_number}")
    print("=" * 40)

    # get answers
    numofplayers, players = playersandinput(numofplayers, players)

    # count answers
    counts = countanswers(numofplayers, players)

    # show herd result + update score
    scoreboard = winners(counts, players, scoreboard)

    # show scoreboard
    print("\n📊 SCOREBOARD")
    print(scoreboard)

    # check winner
    for player, points in scoreboard.items():

        if points >= WINNING_SCORE:
            print("\n🏆" + "=" * 30)
            print(f"{player} WINS THE GAME!")
            print("=" * 30)
            exit()

    round_number += 1