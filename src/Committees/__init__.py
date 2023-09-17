from .intro import intro
from .bar import Bar
from .physix import PhysiX
from .rowing import Rowing
from .xcinema import Xcinema
from .fightX import FightX
from .OnlyGains import OnlyGains
from .RunX import RunX
from .climbx import ClimbX
from .shuttlex import Badminton
from .CSC import CSC
from .Bside import Bside
from .gamex import GameX
from .lgbtqx import LGBTQX
from .bmathx import BmathX
from .volunteerx import VolunteerX
from .greench import Greench
from .cookx import CookX
from .knittix import KnittiX
from .music import Music


_temp = [Bar, PhysiX, Rowing, Xcinema, FightX, OnlyGains, RunX, ClimbX, Badminton, CSC, Bside, GameX, LGBTQX, BmathX, VolunteerX, Greench, CookX, KnittiX, Music]
_objs = [ob() for ob in _temp]
names = [ob.name for ob in _objs]
committees = [ob.handler for ob in _objs]
