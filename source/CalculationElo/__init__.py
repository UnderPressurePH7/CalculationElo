import BigWorld
from gui.modsSettingsApi import g_modsSettingsApi

from .utils import print_debug

from .clanAPI import ClanAPI
from .eloCalc import EloCalc
from .multiTextPanel import MultiTextPanel
from .config import g_config

g_clanAPI = ClanAPI()
g_eloCalc = EloCalc()
g_multiTextPanel = MultiTextPanel()