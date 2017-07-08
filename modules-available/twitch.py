import asyncio
from asyncio import wait_for
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
    url = "https://api.twitch.tv/kraken/channels/{}".format(await wait_for(channel_id, None))
    params = {
        'channel[game]': game,
        'oauth_token': config['twitch_token']
    }
    await connection.session.put(url, params=params, headers=headers)


async def set_title(connection, title):
    url = "https://api.twitch.tv/kraken/channels/{}".format(await wait_for(channel_id, None))
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
        json = await r.json()
        return json


async def get_channel_id(connection):
    return (await get_channel(connection))['_id']


async def get_stream(connection):
    url = "https://api.twitch.tv/kraken/streams/{}".format(await wait_for(channel_id, None))
    params = {
        'oauth_token': config['twitch_token']
    }
    async with connection.session.get(url, params=params, headers=headers) as response:
        json = await response.json()
        return json.get('stream', None)


@every(120)
async def update_title(connection):
    body = db.get('twitch', 'title')
    if not body:
        return
    text = render(body)
    await set_title(connection, text)


@command
@mod_only
@short("Sets Twitch channel title")
async def title(connection, event, body):
    db.put('twitch', 'title', body)
    await update_title(connection)
    return "Set title to: {}".format(render(body))


@command
@mod_only
@short("Sets Twitch game")
async def game(connection, event, body):
    await set_game(connection, body)
    return "Set game to: {}".format(body)


@handle("bot-start")
async def load_channel(connection, event):
    global channel_id
    channel_id = asyncio.ensure_future(get_channel_id(connection))
