# -*- coding: utf-8 -*-
from .utils import print_error, print_debug

PARAM_REGISTRY = {}

class Param(object):
    def __init__(self, path, defaultValue, disabledValue=None):
        self.name = path[-1]
        self.path = path
        self.tokenName = "-".join(self.path)
        self.value = defaultValue
        self.defaultValue = defaultValue
        self.disabledValue = disabledValue if disabledValue is not None else defaultValue
        PARAM_REGISTRY[self.tokenName] = self

    def readValueFromConfigDict(self, configDict):
        readValue = None
        prevConfigSection = configDict

        for pathSegment in self.path:
            if pathSegment not in prevConfigSection:
                return None
            dictSection = prevConfigSection[pathSegment]
            readValue = dictSection
            prevConfigSection = dictSection

        return readValue

    @property
    def jsonValue(self):
        return self.toJsonValue(self.value)

    @jsonValue.setter
    def jsonValue(self, jsonValue):
        try:
            self.value = self.fromJsonValue(jsonValue)
        except Exception as e:
            print_error("Error occurred while saving parameter %s with jsonValue %s, fallback to previous valid value: %s" % (self.tokenName, jsonValue, str(e)))

    @property
    def defaultMsaValue(self):
        return self.toMsaValue(self.defaultValue)

    @property
    def msaValue(self):
        return self.toMsaValue(self.value)

    @msaValue.setter
    def msaValue(self, msaValue):
        try:
            self.value = self.fromMsaValue(msaValue)
        except Exception as e:
            print_error("Error occurred while saving parameter %s with msaValue %s, fallback to previous valid value: %s" % (self.tokenName, msaValue, str(e)))

    def toMsaValue(self, value):
        return value

    def fromMsaValue(self, msaValue):
        return msaValue

    def toJsonValue(self, value):
        return value

    def fromJsonValue(self, jsonValue):
        return jsonValue

    def validate(self, value):
        return True


class BooleanParam(Param):
    def __init__(self, path, defaultValue=False, disabledValue=None):
        super(BooleanParam, self).__init__(path, defaultValue, disabledValue)

    def toMsaValue(self, value):
        return bool(value)

    def fromMsaValue(self, msaValue):
        return bool(msaValue)

    def toJsonValue(self, value):
        return bool(value)

    def fromJsonValue(self, jsonValue):
        return bool(jsonValue)

    def validate(self, value):
        return isinstance(value, bool)


class Option(object):
    def __init__(self, value, msaValue, displayName):
        self.value = value
        self.msaValue = msaValue
        self.displayName = displayName


class OptionsParam(Param):
    def __init__(self, path, options, defaultValue, disabledValue=None):
        super(OptionsParam, self).__init__(path, defaultValue, disabledValue)
        self.options = options

    def toMsaValue(self, value):
        option = self.getOptionByValue(value)
        return option.msaValue if option else 0

    def fromMsaValue(self, msaValue):
        option = self.getOptionByMsaValue(msaValue)
        return option.value if option else self.defaultValue

    def toJsonValue(self, value):
        return value

    def fromJsonValue(self, jsonValue):
        option = self.getOptionByValue(jsonValue)
        if option is None:
            raise Exception("Invalid value %s for config param %s" % (jsonValue, self.tokenName))
        return option.value

    def getOptionByValue(self, value):
        for option in self.options:
            if option.value == value:
                return option
        return None

    def getOptionByMsaValue(self, msaValue):
        for option in self.options:
            if option.msaValue == msaValue:
                return option
        return None

    def validate(self, value):
        return self.getOptionByValue(value) is not None


class ListParam(Param):
    def __init__(self, path, defaultValue=None, disabledValue=None):
        default = defaultValue if defaultValue is not None else []
        super(ListParam, self).__init__(path, default, disabledValue)

    def toMsaValue(self, value):
        return list(value) if isinstance(value, (list, tuple)) else self.defaultValue

    def fromMsaValue(self, msaValue):
        return list(msaValue) if isinstance(msaValue, (list, tuple)) else self.defaultValue

    def toJsonValue(self, value):
        return list(value) if isinstance(value, (list, tuple)) else self.defaultValue

    def fromJsonValue(self, jsonValue):
        return list(jsonValue) if isinstance(jsonValue, (list, tuple)) else self.defaultValue

    def validate(self, value):
        return isinstance(value, (list, tuple))


class ColorParam(Param):
    def __init__(self, path, defaultValue=None, disabledValue=None):
        default = defaultValue if defaultValue is not None else [255, 255, 255]
        super(ColorParam, self).__init__(path, default, disabledValue)

    def toMsaValue(self, value):
        try:
            if not self.validate(value):
                print_error('Invalid color value %s for %s, using default' % (value, self.tokenName))
                value = self.defaultValue
            return self._colorToHex(value)
        except Exception as e:
            print_error('Error converting color to hex for %s: %s' % (self.tokenName, str(e)))
            return self._colorToHex(self.defaultValue)

    def fromMsaValue(self, msaValue):
        try:
            if msaValue is None or msaValue == '':
                return list(self.defaultValue)
            return list(self._hexToColor(msaValue))
        except Exception as e:
            print_error('Error converting hex to color for %s: %s' % (self.tokenName, str(e)))
            return list(self.defaultValue)

    def toJsonValue(self, value):
        return list(value) if isinstance(value, (list, tuple)) else self.defaultValue

    def fromJsonValue(self, jsonValue):
        try:
            if isinstance(jsonValue, (list, tuple)) and len(jsonValue) >= 3:
                return [int(jsonValue[0]), int(jsonValue[1]), int(jsonValue[2])]
            return list(self.defaultValue)
        except Exception as e:
            print_error('Error converting JSON to color for %s: %s' % (self.tokenName, str(e)))
            return list(self.defaultValue)

    def getHexColor(self):
        """Метод для отримання кольору в hex форматі"""
        try:
            return '#' + self._colorToHex(self.value).lstrip('#')
        except Exception as e:
            print_error('Error getting hex color for %s: %s' % (self.tokenName, str(e)))
            return '#FFFFFF'

    def _hexToColor(self, hexColor):
        if not isinstance(hexColor, str):
            raise ValueError('Hex color must be string')
            
        hexColor = hexColor.lstrip('#').upper()
        
        if len(hexColor) != 6:
            raise ValueError('Hex color must be 6 characters long')
            
        try:
            return tuple(int(hexColor[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            raise ValueError('Invalid hex color format')

    def _colorToHex(self, color):
        if not isinstance(color, (list, tuple)) or len(color) < 3:
            raise ValueError('Color must be list or tuple with at least 3 elements')
            
        try:
            r, g, b = int(color[0]), int(color[1]), int(color[2])
            if not all(0 <= c <= 255 for c in [r, g, b]):
                raise ValueError('Color values must be between 0 and 255')
            return ("%02X%02X%02X" % (r, g, b))
        except (ValueError, TypeError):
            raise ValueError('Invalid color format')

    def validate(self, value):
        try:
            if not isinstance(value, (list, tuple)) or len(value) < 3:
                return False
            r, g, b = int(value[0]), int(value[1]), int(value[2])
            return all(0 <= c <= 255 for c in [r, g, b])
        except (ValueError, TypeError):
            return False