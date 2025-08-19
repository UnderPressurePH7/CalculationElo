import BigWorld
from gui.modsSettingsApi import g_modsSettingsApi


from .clanAPI import ClanAPI
from .avgWN8 import AvgWN8
from .eloCalc import EloCalc
from .multiTextPanel import MultiTextPanel
from .config import g_config

g_clanAPI = ClanAPI()
g_avgWN8 = AvgWN8()
g_multiTextPanel = MultiTextPanel()
g_eloCalc = EloCalc()
