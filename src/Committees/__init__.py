from .intro import intro
from .bar import Bar
from .physiX import Physix
from .example import Example
from .rowing import Rowing
from .xcinema import Xcinema

_temp = [Bar, Physix, Example, Rowing, Xcinema]
_objs = [ob() for ob in _temp]
names = [ob.name for ob in _objs]
committees = [ob.handler for ob in _objs]
