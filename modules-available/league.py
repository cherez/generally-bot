from config import config

from commands import command, mod_only, short, long, alias
import db
from template import render
from schedules import every

from league_api.client import Client

client = Client(config['riot_token'], 'na1')
champs = client.get_champion_list(dataById=True)
current_game = None

queue_types = {
    0: 'Custom',
    2: 'Normal Blind',
    14: 'Normal Draft',
    8: 'Normal Twisted Treeline',
    318: 'ARURF',
    325: 'ARSR',
    400: 'Normal Draft',
    420: 'Ranked Solo',
    440: 'Ranked Flex',
    600: 'Blood Moon',
    610: 'Dark Star Singularity',
    65: 'ARAM'
}

@command
@mod_only
@short("Sets the current summoner name")
def set_summoner(connection, event, body):
    session = connection.db()
    db.put(session, 'league', 'name', body)
    summoner = client.get_by_summoner_name(body)
    db.put(session, 'league', 'id', summoner.id)
    return "Set Summon to " + body

@every(60)
def check_game(connection):
    global current_game
    session = connection.db()
    id = db.get(session, 'league', 'id')
    try:
        game = client.get_current_game_info_by_summoner(id)
    except:
        db.put(session, 'league', 'champion', '')
        db.put(session, 'league', 'mode', '')
        db.put(session, 'league', 'data', '')
        session.commit()
        if current_game is not None:
            connection.handle_event('league-game-end', None, None, [current_game])
            current_game = None
        return  # no game right now
    if current_game is None:
        current_game = game
        connection.handle_event('league-game-start', None, None, [current_game])
    elif current_game.game_id != game.game_id:
        connection.handle_event('league-game-end', None, None, [current_game])
        current_game = game
        connection.handle_event('league-game-start', None, None, [current_game])
    participants = game.participants
    me = [i for i in participants if str(i.summoner_id) == id][0]
    champ = champs.data[repr(me.champion_id)]
    db.put(session, 'league', 'champion', champ.name)
    queue = getattr(game, 'gameQueueConfigId', 0)  # missing on custom games
    mode = queue_types.get(queue, 'Game')
    db.put(session, 'league', 'mode', mode)
    set_data(session)
    session.commit()

def set_data(session):
    template = db.get(session, 'league', 'data-template')
    text = render(session, template, 'league')
    db.put(session, 'league', 'data', text)

@command
@mod_only
@short("Formats how current game data should be displayed")
def set_league_data_template(connection, event, body):
    session = connection.db()
    db.put(session, 'league', 'data-template', body)
    set_data(session)
    session.commit()
    check_game(connection)
    return "Set League data template to " + body


@alias('elo')
@alias('ranking')
@command
@short("Prints current League ranks")
def rank(connection, event, body):
    session = connection.db()
    id = db.get(session, 'league', 'id')
    league_entries = client.get_all_league_positions_for_summoner(id)
    # this is a list of each rank type
    for entry in league_entries:
        ranked, queue, size = entry.queue_type.split('_')
        queue = queue.title()
        size = size[0]
        tier = entry.tier.title()
        division = entry.rank
        lp = entry.league_points
        template = "{queue} {size}s: {tier} {division}, {lp} LP"
        if entry.miniSeries:
            series = entry.mini_series
            wins = series.wins
            losses = series.losses
            template += "; {wins}-{losses} in promos"
        connection.say(template.format(**locals()))
