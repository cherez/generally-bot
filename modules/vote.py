from commands import command, mod_only
import db
import re

voting = False
candidates = []
ballots = {}
num_pattern = re.compile("\d+")

@command
@mod_only
def start_vote(connection, event, body):
    global candidates, voting, ballots
    if not body:
        return "Usage: !start-vote option1;option2;..."
    args = body.split(';')
    if len(args) == 1:
        session = connection.db()
        name = args[0]
        items = db.find(session, db.ListItem, list=name).all()
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
def vote_options(connection, event, body):
    if not voting:
        return "There is not currently a vote."
    options = "Voting Options: "
    for index, candidate in enumerate(candidates):
        options += "{}: {}.  ".format(index+1, candidate)
    connection.say(options)

@command
def vote(connection, event, body):
    if not voting:
        return "There is not currently a vote."
    votes = num_pattern.findall(body)
    votes = {int(i)-1 for i in votes}
    voter = event.source.nick

    ballots[voter] = votes

@command
@mod_only
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
    winner = max(candidates, key=results.get)
    connection.say("Winner: {}!!!".format(winner))
