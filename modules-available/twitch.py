from config import config

if 'twitch_client' in config and 'twitch_token' in config:
    from commands import command, mod_only, short, long
    from schedules import every
    from template import render
    import db
    import requests
    import threading

    channel_id = None

    headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': config['twitch_client']
            }

    def set_game(game):
        url = "https://api.twitch.tv/kraken/channels/{}".format(channel_id)
        params = {
                'channel[game]': game,
                'oauth_token': config['twitch_token']
                }
        r = requests.put(url, params=params, headers=headers)


    def set_title(title):
        url = "https://api.twitch.tv/kraken/channels/{}".format(channel_id)
        params = {
                'channel[status]': title,
                'oauth_token': config['twitch_token']
                }
        r = requests.put(url, params=params, headers=headers)

    def get_channel():
        url = "https://api.twitch.tv/kraken/channel/"
        params = {
                'oauth_token': config['twitch_token']
                }
        r = requests.get(url, params=params, headers=headers)
        json = r.json()
        return json

    def get_channel_id():
        return get_channel()['_id']

    def get_stream():
        url = "https://api.twitch.tv/kraken/streams/{}".format(channel_id)
        params = {
            'oauth_token': config['twitch_token']
        }
        r = requests.get(url, params=params, headers=headers)
        return r.json().get('stream', None)

    @every(120)
    def update_title(connection):
        session = connection.db()
        body = db.get(session, 'twitch', 'title')
        if not body:
            return
        text = render(session, body)
        #background this to not block the reactor
        thread = threading.Thread(target = set_title, args=(text,))
        thread.daemon = True
        thread.start()
        return text


    @command
    @mod_only
    @short("Sets Twitch channel title")
    def title(connection, event, body):
        db.put(connection.db(), 'twitch', 'title', body)
        title = update_title(connection)
        return "Set title to: {}".format(title)

    @command
    @mod_only
    @short("Sets Twitch game")
    def game(connection, event, body):
        set_game(body)
        return "Set game to: {}".format(body)

    channel_id = get_channel_id()
