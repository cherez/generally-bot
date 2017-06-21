from handlers import handle
import db

@handle('league-game-start')
def show_history(connection, event):
    url = 'http://www.lolskill.net/game/NA/{name}'
    name = db.get('league', 'name')
    connection.say("New match started!")
    connection.say(url.format(name=name))
