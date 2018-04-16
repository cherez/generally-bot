from handlers import handle
import db


@handle('league-game-end')
def show_history(connection, event):
    match = event.arguments[0]
    url = 'https://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/{game_id}/{user_id}'
    user_id = db.get('league', 'account_id')
    connection.say("Match complete! Match history: " + url.format(game_id=match.game_id, user_id=user_id))
