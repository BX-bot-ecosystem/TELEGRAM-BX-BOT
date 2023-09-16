from .intro import intro
from .bar import Bar
# from .physiX import PhysiX
from .rowing import Rowing
from .xcinema import Xcinema
from .fightX import FightX
from .OnlyGains import OnlyGains
from .RunX import RunX
from .climbx import ClimbX
from .shuttlex import Badminton
from .CSC import CSC

_temp = [Bar, Rowing, Xcinema, FightX, OnlyGains, RunX, ClimbX, Badminton, CSC]
_objs = [ob() for ob in _temp]
names = [ob.name for ob in _objs]
committees = [ob.handler for ob in _objs]
