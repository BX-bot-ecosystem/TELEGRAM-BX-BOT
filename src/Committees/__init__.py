from .bar import Bar
from .physiX import Physix
from .example import Example

_temp = [Bar, Physix, Example]
committees = [ob() for ob in _temp]
