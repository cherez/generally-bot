import asyncio
from handlers import handle

from config import config

from commands import command, mod_only, short, long
from schedules import every
from template import render
import db

channel_id = None

headers = {
    'Accept': 'application/vnd.twitchtv.v5+json',
    'Client-ID': config['twitch_client']
}


async def set_game(connection, game):
    url = "https://api.twitch.tv/kraken/channels/{}".format(await channel_id)
    params = {
        'channel[game]': game,
        'oauth_token': config['twitch_token']
    }
    await connection.session.put(url, params=params, headers=headers)


async def set_title(connection, title):
    url = "https://api.twitch.tv/kraken/channels/{}".format(await channel_id)
    params = {
        'channel[status]': title,
        'oauth_token': config['twitch_token']
    }
    async with connection.session.put(url, params=params, headers=headers) as resp:
        await resp.text()


async def get_channel(connection):
    url = "https://api.twitch.tv/kraken/channel/"
    params = {
        'oauth_token': config['twitch_token']
    }
    async with connection.session.get(url, params=params, headers=headers) as r:
        print("async with")
        json = await r.json()
        print(json)
        return json


async def get_channel_id(connection):
    return (await get_channel(connection))['_id']


async def get_stream(connection):
    url = "https://api.twitch.tv/kraken/streams/{}".format(await channel_id)
    params = {
        'oauth_token': config['twitch_token']
    }
    print("getting", url)
    async with connection.session.get(url, params=params, headers=headers) as response:
        json = await response.json()
        print(json)
        return json.get('stream', None)


@every(120)
def update_title(connection):
    body = db.get('twitch', 'title')
    if not body:
        return
    text = render(body)
    asyncio.run_coroutine_threadsafe(set_title(connection, text), connection.loop)
    return text


@command
@mod_only
@short("Sets Twitch channel title")
def title(connection, event, body):
    db.put('twitch', 'title', body)
    title = update_title(connection)
    coro = set_title(connection, title)
    asyncio.run_coroutine_threadsafe(coro, connection.loop)
    return "Set title to: {}".format(title)


@command
@mod_only
@short("Sets Twitch game")
def game(connection, event, body):
    coro = set_game(connection, body)
    asyncio.run_coroutine_threadsafe(coro, connection.loop)
    return "Set game to: {}".format(body)


@handle("bot-start")
async def load_channel(connection, event):
    print('welcome')
    global channel_id
    channel_id = get_channel_id(connection)
