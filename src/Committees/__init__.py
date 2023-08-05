from .bar import Bar
from .physiX import Physix
from .example import Example
from .rowing import Rowing

_temp = [Bar, Physix, Example, Rowing]
committees = [ob().handler for ob in _temp]
