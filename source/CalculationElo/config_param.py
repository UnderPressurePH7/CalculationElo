import Keys
from .config_param_types import BooleanParam, OptionsParam, ColorParam, Option, PARAM_REGISTRY, SliderParam

class DisplayMode(object):
    ALWAYS = 'always'
    ON_HOTKEY_PRESSED = 'on-hotkey-pressed'

class HotKeyParam(object):
    def __init__(self, path, defaultValue=None):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue if defaultValue is not None else []
        self.defaultValue = self.value
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        if isinstance(value, list):
            self.value = value
        elif value is None:
            self.value = []
        else:
            self.value = [value]

class PositionParam(object):
    def __init__(self, path, defaultValue=None):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue if defaultValue is not None else [0, 0]
        self.defaultValue = self.value
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        if isinstance(value, list) and len(value) == 2:
            self.value = value
        else:
            self.value = [0, 0]

class ConfigParams(object):
    def __init__(self):
        self.enabled = BooleanParam(['enabled'], defaultValue=True)
        self.displayMode = OptionsParam(
            ['display-mode'],
            [
                Option(DisplayMode.ALWAYS, 0, "Always"),
                Option(DisplayMode.ON_HOTKEY_PRESSED, 1, "On HotKey Pressed")
            ],
            defaultValue=DisplayMode.ALWAYS
        )
        self.eloHotKey = HotKeyParam(['elo-hotkey'], defaultValue=[Keys.KEY_LALT])
        
        # Початкова позиція панелі
        self.panelPosition = PositionParam(['panel-position'], defaultValue=[565, 50])
        
        # Видимість окремих полів
        self.showPlayerNames = BooleanParam(['show-player-names'], defaultValue=True)
        self.showEloChanges = BooleanParam(['show-elo-changes'], defaultValue=True) 
        self.showWinrateAndBattles = BooleanParam(['show-winrate-battles'], defaultValue=True)
        
        # Прозорість фону панелі
        self.panelBackgroundAlpha = SliderParam(['panel-background-alpha'], minValue=0.0, maxValue=1.0, defaultValue=0.8)
        self.panelBackgroundColor = ColorParam(['panel-background-color'], defaultValue=[0, 0, 0])
        
        # Кольори для різних елементів
        self.headerColor = ColorParam(['header-color'], defaultValue=[255, 255, 255])
        self.alliesNamesColor = ColorParam(['allies-names-color'], defaultValue=[79, 134, 39])
        self.enemiesNamesColor = ColorParam(['enemies-names-color'], defaultValue=[154, 1, 1])
        self.alliesRatingColor = ColorParam(['allies-rating-color'], defaultValue=[79, 134, 39])
        self.enemiesRatingColor = ColorParam(['enemies-rating-color'], defaultValue=[154, 1, 1])
        self.eloGainColor = ColorParam(['elo-gain-color'], defaultValue=[0, 255, 0])
        self.eloLossColor = ColorParam(['elo-loss-color'], defaultValue=[255, 0, 0])
        self.winrateColor = ColorParam(['winrate-color'], defaultValue=[255, 255, 255])
        self.battlesColor = ColorParam(['battles-color'], defaultValue=[255, 255, 255])
        
        # Тінь для тексту
        self.textShadowEnabled = BooleanParam(['text-shadow-enabled'], defaultValue=True)
        self.textShadowColor = ColorParam(['text-shadow-color'], defaultValue=[0, 0, 0])
        self.textShadowAlpha = SliderParam(['text-shadow-alpha'], minValue=0.0, maxValue=1.0, defaultValue=0.5)
        self.textShadowDistance = SliderParam(['text-shadow-distance'], minValue=0, maxValue=10, defaultValue=1)
        self.textShadowBlur = SliderParam(['text-shadow-blur'], minValue=0, maxValue=10, defaultValue=2)

    @staticmethod
    def items():
        return PARAM_REGISTRY

g_configParams = ConfigParams()