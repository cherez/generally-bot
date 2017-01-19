#! /usr/bin/env python3

import yaml
import bot

if __name__ == '__main__':
    import logging
    config = yaml.load(open('config'))
    if(config.get('debug')):
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    bot.Bot(config).start()
    bot = bot.Bot(config['chan'], config['name'], config['pass'], config['server'])
    bot.start()
