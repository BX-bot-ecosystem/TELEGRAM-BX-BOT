from .intro import intro
from .bar import Bar
from .physiX import Physix
from .example import Example
from .rowing import Rowing

committees_list = "\n -  ".join(["",".9 bar🍻🍻 (/bar)", "PhysiX⚛️⚛️ (/Physix)", "ClimbX (/ClimbX)", "BX/B- (/rowing)"])
_temp = [Bar, Physix, Example, Rowing]
committees = [ob().handler for ob in _temp]
