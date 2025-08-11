from .utils import print_error, print_debug

class Param(object):
    def __init__(self, path, defaultValue, disabledValue=None):
        self.tokenName = '-'.join(path)
        self.path = path
        self.value = defaultValue
        self.defaultValue = defaultValue
        self.disabledValue = disabledValue if disabledValue is not None else defaultValue
        self.msaValue = None

    def toMsaValue(self, value):
        """Конвертація значення для ModsSettingsAPI"""
        return value

    def fromMsaValue(self, msaValue):
        """Конвертація з ModsSettingsAPI"""
        return msaValue if msaValue is not None else self.defaultValue

    def validate(self, value):
        """Валідація значення"""
        return True

    def toJsonValue(self, value):
        """Конвертація для збереження в JSON"""
        return value

    def fromJsonValue(self, jsonValue):
        """Конвертація з JSON"""
        return jsonValue if jsonValue is not None else self.defaultValue


class BooleanParam(Param):
    def __init__(self, path, defaultValue=False, disabledValue=None):
        super(BooleanParam, self).__init__(path, defaultValue, disabledValue)

    def fromMsaValue(self, msaValue):
        try:
            return bool(msaValue) if msaValue is not None else self.defaultValue
        except (ValueError, TypeError):
            print_error('Invalid boolean value %s for %s' % (msaValue, self.tokenName))
            return self.defaultValue

    def validate(self, value):
        return isinstance(value, bool)


class KeysParam(Param):
    def __init__(self, path, defaultValue=None, disabledValue=None):
        default = defaultValue if defaultValue is not None else []
        super(KeysParam, self).__init__(path, default, disabledValue)

    def toMsaValue(self, value):
        if not isinstance(value, list):
            return []
        return value

    def fromMsaValue(self, msaValue):
        if msaValue is None:
            return []
        elif isinstance(msaValue, list):
            return msaValue
        else:
            return [msaValue]

    def validate(self, value):
        return isinstance(value, list)


class Option(object):    
    def __init__(self, value, msaValue, displayName):
        self.value = value
        self.msaValue = msaValue
        self.displayName = displayName

    def __repr__(self):
        return 'Option(value=%s, msaValue=%s, displayName=%s)' % (
            self.value, self.msaValue, self.displayName
        )


class OptionsParam(Param):
    def __init__(self, path, options, defaultValue, disabledValue=None):
        super(OptionsParam, self).__init__(path, defaultValue, disabledValue)
        self.options = options if options else []
        
        if not self.getOptionByValue(defaultValue):
            print_error('Default value %s not found in options for %s' % (defaultValue, self.tokenName))

    def toMsaValue(self, value):
        option = self.getOptionByValue(value)
        if option:
            return option.msaValue
        else:
            print_error('Option with value %s not found for %s' % (value, self.tokenName))
            default_option = self.getOptionByValue(self.defaultValue)
            return default_option.msaValue if default_option else 0

    def fromMsaValue(self, msaValue):
        option = self.getOptionByMsaValue(msaValue)
        if option:
            return option.value
        else:
            print_debug('Option with msaValue %s not found for %s, using default' % (msaValue, self.tokenName))
            return self.defaultValue

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
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            raise ValueError('Color must be list or tuple of 3 values')
            
        try:
            r, g, b = color
            return ("%02X%02X%02X" % (int(r), int(g), int(b)))
        except (ValueError, TypeError):
            raise ValueError('Color values must be integers')

    def validate(self, value):
        try:
            if not isinstance(value, (list, tuple)) or len(value) != 3:
                return False
            return all(isinstance(c, (int, float)) and 0 <= c <= 255 for c in value)
        except:
            return False


class IntParam(Param):    
    def __init__(self, path, defaultValue=0, minValue=None, maxValue=None, disabledValue=None):
        super(IntParam, self).__init__(path, defaultValue, disabledValue)
        self.minValue = minValue
        self.maxValue = maxValue

    def fromMsaValue(self, msaValue):
        try:
            value = int(msaValue) if msaValue is not None else self.defaultValue
            return self._clampValue(value)
        except (ValueError, TypeError):
            print_error('Invalid integer value %s for %s' % (msaValue, self.tokenName))
            return self.defaultValue

    def _clampValue(self, value):
        if self.minValue is not None and value < self.minValue:
            return self.minValue
        if self.maxValue is not None and value > self.maxValue:
            return self.maxValue
        return value

    def validate(self, value):
        try:
            int_value = int(value)
            if self.minValue is not None and int_value < self.minValue:
                return False
            if self.maxValue is not None and int_value > self.maxValue:
                return False
            return True
        except (ValueError, TypeError):
            return False


class FloatParam(Param):    
    def __init__(self, path, defaultValue=0.0, minValue=None, maxValue=None, disabledValue=None):
        super(FloatParam, self).__init__(path, defaultValue, disabledValue)
        self.minValue = minValue
        self.maxValue = maxValue

    def fromMsaValue(self, msaValue):
        try:
            value = float(msaValue) if msaValue is not None else self.defaultValue
            return self._clampValue(value)
        except (ValueError, TypeError):
            print_error('Invalid float value %s for %s' % (msaValue, self.tokenName))
            return self.defaultValue

    def _clampValue(self, value):
        if self.minValue is not None and value < self.minValue:
            return self.minValue
        if self.maxValue is not None and value > self.maxValue:
            return self.maxValue
        return value

    def validate(self, value):
        try:
            float_value = float(value)
            if self.minValue is not None and float_value < self.minValue:
                return False
            if self.maxValue is not None and float_value > self.maxValue:
                return False
            return True
        except (ValueError, TypeError):
            return False