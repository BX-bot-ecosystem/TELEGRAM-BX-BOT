from .intro import intro
from .bar import Bar
from .physiX import Physix
from .example import Example
from .rowing import Rowing

import json
import utils

with open(utils.config.ROOT + '/data/Committees/committees.json') as f:
    committees = json.load(f)
committees_list = [f'{committees[committee]["name"]} ({committees[committee]["command"]})' for committee in committees.keys()]
telegram_list = "\n -  ".join(committees_list)
_temp = [Bar, Physix, Example, Rowing]
committees = [ob().handler for ob in _temp]
