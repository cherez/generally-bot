from handlers import handle
import modules.league
import db

@handle('league-game-end')
def show_history(connection, event):
    match = event.arguments[0]
    url = 'http://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/{game_id}/{user_id}'
    session = connection.db()
    user_id = db.get(session, 'league', 'id')
    connection.say(url.format(game_id=match.game_id, user_id=user_id))