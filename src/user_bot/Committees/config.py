import json
import utils


with open(utils.config.ROOT + '/data/Committees/committees.json') as f:
    committees = json.load(f)
committees_list = [f'{committees[committee]["name"]} ({committees[committee]["command"]})' for committee in committees.keys()]
telegram_list = "\n -  ".join(committees_list)
