from config import config

if 'riot_token' in config:
    from commands import command, mod_only, short, long
    import db
    from template import render
    from schedules import every

    from riotwatcher import RiotWatcher

    watcher = RiotWatcher(config['riot_token'])
    champs = watcher.static_get_champion_list()['data']
    champs_by_id = {champs[key]['id']: key for key in champs.keys()}

    queue_types = {
            0: 'Custom',
            2: 'Normal Blind',
            14: 'Normal Draft',
            8: 'Normal Twisted Treeline',
            400: 'Normal Draft',
            420: 'Ranked Solo',
            440: 'Ranked Flex',
            600: 'Blood Moon',
            65: 'ARAM'
            }

    @command
    @mod_only
    @short("Sets the current summoner name")
    def set_summoner(connection, event, body):
        session = connection.db()
        db.put(session, 'league', 'name', body)
        summoner = watcher.get_summoner(name=body)
        db.put(session, 'league', 'id', summoner['id'])
        return "Set Summon to " + body

    @every(60)
    def check_game(connection):
        session = connection.db()
        id = db.get(session, 'league', 'id')
        try:
            game = watcher.get_current_game(id)
        except:
            db.put(session, 'league', 'champion', '')
            db.put(session, 'league', 'mode', '')
            db.put(session, 'league', 'data', '')
            return #no game right now
        participants = game['participants']
        me = [i for i in participants if str(i['summonerId']) == id][0]
        champ = champs_by_id[me['championId']]
        db.put(session, 'league', 'champion', champ)
        queue = game.get('gameQueueConfigId', 0) #missing on custom games
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


    @command
    @short("Prints current League ranks")
    def rank(connection, event, body):
        session = connection.db()
        id = db.get(session, 'league', 'id')
        try:
            #there should be exactly one result since we send exactly one id
            league_entries = watcher.get_league_entry([id])[id]
        except:
            raise
            return "No rank found."
        #this is a list of each rank type
        for entry in league_entries:
            ranked, queue, size = entry['queue'].split('_')
            queue = queue.title()
            size = size[0]
            tier = entry['tier'].title()
            division = entry['entries'][0]['division']
            lp = entry['entries'][0]['leaguePoints']
            template = "{queue} {size}s: {tier} {division}, {lp} LP"
            connection.say(template.format(**locals()))
