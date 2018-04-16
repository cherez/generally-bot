import asyncio

import aiohttp

import db
from commands import command, mod_only, short, alias
from config import config
from handlers import handle
from league_api.client import Client
from schedules import background
from template import render

client = None
champs = None
current_game = None

queue_types = {
    0: 'Custom',
    1000: 'PROJECT: Overcharge',
    14: 'Normal Draft',
    2: 'Normal Blind',
    318: 'ARURF',
    325: 'ARSR',
    400: 'Normal Draft',
    420: 'Ranked Solo',
    440: 'Ranked Flex',
    450: 'ARAM',
    600: 'Blood Moon',
    610: 'Dark Star Singularity',
    65: 'ARAM',
    8: 'Normal Twisted Treeline',
}


@command
@mod_only
@short("Sets the current summoner name")
async def set_summoner(connection, event, body):
    db.put('league', 'name', body)
    summoner = await client.get_by_summoner_name(body)
    db.put('league', 'id', str(summoner.id))
    db.put('league', 'account_id', str(summoner.account_id))
    return "Set Summoner to " + body


@background
async def check_game(connection):
    global current_game
    await asyncio.wait_for(champs, None)
    id = db.get('league', 'id')
    game = await get_current_game(id)
    while True:
        while game is None:
            await asyncio.sleep(60)
            game = await get_current_game(id)

        current_game = game

        participants = game.participants
        me = [i for i in participants if str(i.summoner_id) == id][0]
        champ = champs.result().data[repr(me.champion_id)]
        queue = getattr(game, 'gameQueueConfigId', 0)  # missing on custom games
        mode = queue_types.get(queue, 'Game')  # Sane default when dealing with unknown game modes.

        db.put('league', 'champion', champ.name)
        db.put('league', 'mode', mode)
        set_data()

        connection.handle_event('league-game-start', None, None, [current_game])

        while game is not None:
            await asyncio.sleep(60)
            game = await get_current_game(id)

        asyncio.ensure_future(await_match(connection, current_game.game_id))
        current_game = game = None

        db.put('league', 'champion', '')
        db.put('league', 'mode', '')
        db.put('league', 'data', '')


async def get_current_game(id):
    try:
        return await client.get_current_game_info_by_summoner(id)
    except aiohttp.ClientError:
        return None


def set_data():
    template = db.get('league', 'data-template')
    text = render(template, 'league')
    db.put('league', 'data', text)


@command
@mod_only
@short("Formats how current game data should be displayed")
async def set_league_data_template(connection, event, body):
    db.put('league', 'data-template', body)
    set_data()
    await check_game(connection)
    return "Set League data template to " + body


@alias('elo')
@alias('ranking')
@command
@short("Prints current League ranks")
async def rank(connection, event, body):
    id = db.get('league', 'id')
    league_entries = await client.get_all_league_positions_for_summoner(id)
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


async def await_match(connection, match_id):
    id = db.get('league', 'id')
    global current_game
    while True:
        try:
            match = await client.get_match(match_id)
            break
        except aiohttp.ClientResponseError as e:
            if e.code == 404:
                await asyncio.sleep(60)
                continue

    if current_game and current_game.game_id == match.game_id:
        current_game = None
    me = [i for i in match.participant_identities if str(i.player.summoner_id) == id][0]
    me = match.participants[me.participantId-1]
    connection.handle_event('league-game-end', None, None, [match])
    if me.stats.win:
        connection.handle_event('win', None, None, [match])
    else:
        connection.handle_event('lose', None, None, [match])


@handle("bot-start")
def load_channel(connection, event):
    global league_dict, client, champs
    league_dict = db.find_or_make(db.Dict, name='league')
    client = Client(config['riot_token'], 'na1', connection.session)
    champs = asyncio.ensure_future(client.get_champion_list(dataById=True))
