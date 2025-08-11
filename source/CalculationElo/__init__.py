import BigWorld
from gui.modsSettingsApi import g_modsSettingsApi

from .utils import print_debug, print_error
from .config import Config

from .clanAPI import ClanAPI
from .eloCalc import EloCalc
from .multiTextPanel import MultiTextPanel

print_debug("[CalculationElo] Initializing global objects...")

try:
    g_clanAPI = ClanAPI()
    g_eloCalc = EloCalc()
    g_multiTextPanel = MultiTextPanel()
    
    g_config = Config()
    
    print_debug("[CalculationElo] Global objects initialized successfully")
    
except Exception as e:
    print_error("[CalculationElo] Error initializing global objects: %s" % str(e))
    
    # Fallback ініціалізація
    g_clanAPI = None
    g_eloCalc = None
    g_multiTextPanel = None
    g_config = None