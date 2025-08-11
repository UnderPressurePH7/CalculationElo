import Keys
from .config_param_types import *
from .utils import print_log, print_error, print_debug

# Реєстр параметрів для зворотної сумісності
PARAM_REGISTRY = {}

class DisplayMode(object):
    ALWAYS = 'always'
    ON_HOTKEY_PRESSED = 'on-hotkey-pressed'

class HotKeyParam(object):
    """Спеціальний клас для параметрів гарячих клавіш"""
    def __init__(self, path, defaultValue=None):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue if defaultValue is not None else [Keys.KEY_LALT]
        self.defaultValue = self.value
        self.msaValue = None
        PARAM_REGISTRY[self.tokenName] = self

    def toMsaValue(self, value):
        return value if isinstance(value, list) else [value] if value is not None else []

    def fromMsaValue(self, msaValue):
        if isinstance(msaValue, list):
            return msaValue
        elif msaValue is None:
            return self.defaultValue
        else:
            return [msaValue]

    def validate(self, value):
        return isinstance(value, list)

    def toJsonValue(self, value):
        return value

    def fromJsonValue(self, jsonValue):
        return jsonValue if jsonValue is not None else self.defaultValue

class ConfigParams(object):
    def __init__(self):
        # Основні налаштування
        self.enabled = BooleanParam(
            ["enabled"],
            defaultValue=True
        )
        
        # Режим відображення
        self.displayMode = OptionsParam(
            ["display-mode"],
            [
                Option(DisplayMode.ALWAYS, 0, "Завжди"),
                Option(DisplayMode.ON_HOTKEY_PRESSED, 1, "При натисканні клавіші")
            ],
            defaultValue=DisplayMode.ON_HOTKEY_PRESSED
        )
        
        # Гарячі клавіші
        self.eloHotKey = HotKeyParam(
            ["elo-hotkey"], 
            defaultValue=[Keys.KEY_LALT]
        )
        
        # Налаштування видимості
        self.eloVisible = BooleanParam(
            ["elo-visible"],
            defaultValue=True
        )
        
        self.enemiesFor28DaysVisible = BooleanParam(
            ["enemies-for-28-days-visible"],
            defaultValue=True
        )
        
        # Кольори
        self.alliesColor = ColorParam(
            ["allies-color"],
            defaultValue=[79, 134, 39]  # Зелений
        )
        
        self.enemiesColor = ColorParam(
            ["enemies-color"], 
            defaultValue=[154, 1, 1]  # Червоний
        )
        
        self.additionalColor = ColorParam(
            ["additional-color"],
            defaultValue=[255, 255, 255]  # Білий
        )
        
        # Позиція панелі (тільки позиція, розмір фіксований)
        self.panelX = IntParam(
            ["panel", "position", "x"],
            defaultValue=565,
            minValue=0,
            maxValue=1920
        )
        
        self.panelY = IntParam(
            ["panel", "position", "y"],
            defaultValue=50,
            minValue=0,
            maxValue=1080
        )
        
        # Налаштування прозорості
        self.panelAlpha = FloatParam(
            ["panel", "alpha"],
            defaultValue=0.7,
            minValue=0.0,
            maxValue=1.0
        )
        
        # Показувати рамку
        self.showBorder = BooleanParam(
            ["panel", "show-border"],
            defaultValue=True
        )

        # Реєстрація всіх параметрів у глобальному реєстрі
        self._register_all_params()

    def _register_all_params(self):
        """Реєстрація всіх параметрів у глобальному реєстрі"""
        params_to_register = [
            'enabled', 'displayMode', 'eloHotKey', 'eloVisible', 'enemiesFor28DaysVisible',
            'alliesColor', 'enemiesColor', 'additionalColor',
            'panelX', 'panelY', 'panelAlpha', 'showBorder'
        ]
        
        for param_name in params_to_register:
            param = getattr(self, param_name)
            if hasattr(param, 'tokenName'):
                PARAM_REGISTRY[param.tokenName] = param

    def items(self):
        """Повернення словника всіх параметрів для сумісності"""
        return {
            'enabled': self.enabled,
            'displayMode': self.displayMode,
            'eloHotKey': self.eloHotKey,
            'eloVisible': self.eloVisible,
            'enemiesFor28DaysVisible': self.enemiesFor28DaysVisible,
            'alliesColor': self.alliesColor,
            'enemiesColor': self.enemiesColor,
            'additionalColor': self.additionalColor,
            'panelX': self.panelX,
            'panelY': self.panelY,
            'panelAlpha': self.panelAlpha,
            'showBorder': self.showBorder
        }

    @staticmethod
    def getRegistry():
        """Статичний метод для отримання реєстру параметрів"""
        return PARAM_REGISTRY

g_configParams = ConfigParams()