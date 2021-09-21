from handlers import handle
import db


@handle('league-game-end')
def show_history(connection, event):
    match = event.arguments[0]
    url = 'https://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/{game_id}/{user_id}'
    user_id = db.get('league', 'account_id')
    url = f"https://app.mobalytics.gg/lol/match/na/{db.get('league', 'name')}/{match.game_id}"
    connection.say("Match complete! Match history: " + url)
