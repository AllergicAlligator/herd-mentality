import random
from prompts import *

def setupscoreboard(numofplayers,scoreboard):
    for i in range(numofplayers):
      scoreboard[f"player{i+1}"] = 0
    return numofplayers, scoreboard

def playersandinput(numofplayers, players):

  print(random.choice(prompts))

  for i in range(numofplayers):
      herd = input(f"player{i+1} please input your answer: ").lower()
      players[f"player{i+1}"] = herd

  return numofplayers, players

def countanswers(numofplayers, players):
  answers = []
  for value in players.values():
      answers.append(value)
  counts = {}

  for ans in answers:
      if ans in counts.keys():
          counts[ans] += 1
      else:
          counts[ans] = 1
  return counts

def winners(counts, players, scoreboard):
    maxvalue = max(counts.values())

    if maxvalue == 1:
        print("nobody gets points")
        return scoreboard

    winninganswer = max(counts, key=counts.get)

    for playername, answer in players.items():
        if answer == winninganswer:
            scoreboard[playername] += 1

    return scoreboard