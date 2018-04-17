from handlers import handle
import db

@handle('league-game-start')
def show_history(connection, event):
    url = 'https://porofessor.gg/live/na/{name}'
    name = db.get('league', 'name')
    connection.say("New match started!")
    connection.say(url.format(name=name))
