from commands import command, mod_only, short, long
import db
import re
import random

voting = False
candidates = []
ballots = {}
num_pattern = re.compile("\d+")

@command
@mod_only
@short("Starts a new election")
@long("""!start-vote list
        Starts an election over the given list.
        !start-vote item1;item2;...
        Starts an election ove the listed items""")
def start_vote(connection, event, body):
    global candidates, voting, ballots
    if not body:
        return "Usage: !start-vote option1;option2;..."
    args = body.split(';')
    if len(args) == 1:
        name = args[0]
        list = db.List.find(name=name)
        items = db.ListItem.where(list=list)
        args = [item.value for item in items]
        if len(args) == 0:
            return "There is nothing in the {} list.".format(name)
    candidates = [i.strip() for i in args]
    voting = True
    ballots = {}
    connection.say("Voting has begun!")
    vote_options(connection, event, body)
    connection.say("To vote: !vote [index] [index] ...")

@command
@short("Lists the candidates of the current election.")
def vote_options(connection, event, body):
    if not voting:
        return "There is not currently a vote."
    options = "Voting Options: "
    for index, candidate in enumerate(candidates):
        options += "{}: {}.  ".format(index+1, candidate)
    connection.say(options)

@command
@short("Casts a vote")
@long("""!vote [number ...]
        Casts a vote for each numbered candidate.
        Further votes will replace previous votes.""")
def vote(connection, event, body):
    if not voting:
        return "There is not currently a vote."
    votes = num_pattern.findall(body)
    votes = {int(i)-1 for i in votes}
    voter = event.source.nick

    ballots[voter] = votes

@command
@mod_only
@short("Ends the current election and prints results and winner.")
def end_vote(connection, event, body):
    global voting
    voting = False
    results = {}
    votes = []
    for ballot in ballots.values():
        votes.extend(ballot)
    results = {candidate: votes.count(index) for index, candidate in enumerate(candidates)}
    connection.say("Voting has closed! Results:")
    for candidate in candidates:
        connection.say("{}: {}".format(candidate, results[candidate]))
    #add a random value to the key to randomly select among ties
    winner = max(candidates, key=lambda candidate: [results[candidate], random.random()])
    connection.say("Winner: {}!!!".format(winner))
