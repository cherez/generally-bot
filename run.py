#! /usr/bin/env python3

import yaml
import bot

if __name__ == '__main__':
    import logging
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    config = yaml.load(open('config'))
    bot.Bot(config).start()
    bot = bot.Bot(config['chan'], config['name'], config['pass'], config['server'])
    bot.start()
