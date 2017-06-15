from handlers import handle
import modules.league
import db

@handle('league-game-start')
def show_history(connection, event):
    url = 'http://www.lolskill.net/game/NA/{name}'
    session = connection.db()
    name = db.get(session, 'league', 'name')
    connection.say(url.format(name=name))
