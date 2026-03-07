# -*- coding: utf-8 -*-
from .translations import Translator
from ..utils import logger

PARAM_REGISTRY = {}


def toJson(obj):
    import json
    return json.dumps(obj, ensure_ascii=False)


def toBool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def toPositiveFloat(value):
    floatValue = float(value)
    return floatValue if floatValue > 0.0 else 0.0


def clamp(minValue, value, maxValue):
    if minValue is not None:
        value = max(minValue, value)
    if maxValue is not None:
        value = min(value, maxValue)
    return value


def toColorList(value):
    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise Exception("Provided color array does not have exactly 3 elements.")
        return [clamp(0, int(c), 255) for c in value]
    raise Exception("Color value must be a list or tuple, got: %s" % type(value).__name__)


def createTooltip(header=None, body=None, note=None, attention=None):
    resStr = ''
    if header is not None:
        resStr += '{HEADER}%s{/HEADER}' % header
    if body is not None:
        resStr += '{BODY}%s{/BODY}' % body
    if note is not None:
        resStr += '{NOTE}%s{/NOTE}' % note
    if attention is not None:
        resStr += '{ATTENTION}%s{/ATTENTION}' % attention
    return resStr


class BaseParameter(object):

    def __init__(self, path, defaultValue, disabledValue=None):
        self.name = path[-1]
        self.path = path
        self.tokenName = "-".join(self.path)

        self.value = defaultValue
        self.defaultValue = defaultValue
        self.disabledValue = disabledValue if disabledValue is not None else defaultValue

        PARAM_REGISTRY[self.tokenName] = self

    def readValueFromConfigDictSafely(self, configDict):
        value = self.readValueFromConfigDict(configDict)
        return value if value is not None else self.defaultValue

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

    def __call__(self):
        from ..settings import g_config
        if hasattr(g_config, 'configParams') and hasattr(g_config.configParams, 'enabled'):
            if not g_config.configParams.enabled.value:
                return self.disabledValue
        return self.value

    @property
    def jsonValue(self):
        return self.toJsonValue(self.value)

    @jsonValue.setter
    def jsonValue(self, jsonValue):
        try:
            self.value = self.fromJsonValue(jsonValue)
        except Exception as e:
            logger.error("Error saving parameter %s with jsonValue %s: %s",
                self.tokenName, jsonValue, e)

    @property
    def msaValue(self):
        return self.toMsaValue(self.value)

    @msaValue.setter
    def msaValue(self, msaValue):
        try:
            self.value = self.fromMsaValue(msaValue)
        except Exception as e:
            logger.error("Error saving parameter %s with msaValue %s: %s",
                self.tokenName, msaValue, e)

    @property
    def defaultMsaValue(self):
        return self.toMsaValue(self.defaultValue)

    @property
    def defaultJsonValue(self):
        return self.toJsonValue(self.defaultValue)

    def toMsaValue(self, value):
        raise NotImplementedError()

    def fromMsaValue(self, msaValue):
        raise NotImplementedError()

    def toJsonValue(self, value):
        raise NotImplementedError()

    def fromJsonValue(self, jsonValue):
        raise NotImplementedError()

    def renderParam(self, header, body=None, note=None, attention=None):
        raise NotImplementedError()

    def __repr__(self):
        return self.tokenName


class CheckboxParameter(BaseParameter):

    def __init__(self, path, defaultValue=None, disabledValue=None):
        super(CheckboxParameter, self).__init__(path, defaultValue, disabledValue)

    def toMsaValue(self, value):
        return value

    def fromMsaValue(self, msaValue):
        return bool(msaValue)

    def toJsonValue(self, value):
        return value

    def fromJsonValue(self, jsonValue):
        return toBool(jsonValue)

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "CheckBox",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "tooltip": createTooltip(
                header="{} ({}: {})".format(
                    header, 
                    Translator.DEFAULT_VALUE, 
                    Translator.CHECKED if self.defaultValue else Translator.UNCHECKED
                ),
                body=body,
                note=note,
                attention=attention
            )
        }


class NumericParameter(BaseParameter):

    def __init__(self, path, castFunction, minValue, step, maxValue, defaultValue, disabledValue=None):
        super(NumericParameter, self).__init__(path, defaultValue, disabledValue)
        self.castFunction = castFunction
        self.minValue = minValue
        self.step = step
        self.maxValue = maxValue

    def toMsaValue(self, value):
        return clamp(self.minValue, value, self.maxValue)

    def fromMsaValue(self, msaValue):
        return clamp(self.minValue, self.castFunction(msaValue), self.maxValue)

    def toJsonValue(self, value):
        return clamp(self.minValue, value, self.maxValue)

    def fromJsonValue(self, jsonValue):
        value = self.castFunction(jsonValue)
        return clamp(self.minValue, value, self.maxValue)

    def renderParam(self, header, body=None, note=None, attention=None):
        raise NotImplementedError()


class SliderParameter(NumericParameter):

    def __init__(self, path, castFunction, minValue, step, maxValue, defaultValue, 
                 disabledValue=None, formatStr='{{value}}'):
        super(SliderParameter, self).__init__(
            path, castFunction, minValue, step, maxValue, defaultValue, disabledValue
        )
        self.formatStr = formatStr

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "Slider",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "minimum": self.minValue,
            "maximum": self.maxValue,
            "snapInterval": self.step,
            "format": self.formatStr,
            "tooltip": createTooltip(
                header="{} ({}: {})".format(header, Translator.DEFAULT_VALUE, self.defaultMsaValue),
                body=body,
                note=note,
                attention=attention
            )
        }


class ColorParameter(BaseParameter):

    def __init__(self, path, defaultValue=None, disabledValue=None):
        if defaultValue is not None:
            defaultValue = list(defaultValue)
        super(ColorParameter, self).__init__(path, defaultValue, disabledValue)

    def toMsaValue(self, value):
        return self._colorToHex(value)

    def fromMsaValue(self, msaValue):
        return list(self._hexToColor(msaValue))

    def toJsonValue(self, value):
        if isinstance(value, tuple):
            return list(value)
        return value

    def fromJsonValue(self, jsonValue):
        return toColorList(jsonValue)

    def getHexColor(self):
        return '#' + self._colorToHex(self.value)

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "ColorChoice",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "tooltip": createTooltip(
                header="{} ({}: #{})".format(header, Translator.DEFAULT_VALUE, self.defaultMsaValue),
                body=body,
                note=note,
                attention=attention
            )
        }

    def _hexToColor(self, hexColor):
        if isinstance(hexColor, (list, tuple)):
            return hexColor
        hexColor = str(hexColor)
        if hexColor.startswith('#'):
            hexColor = hexColor[1:]
        return [int(hexColor[i:i + 2], 16) for i in (0, 2, 4)]

    def _colorToHex(self, color):
        if isinstance(color, (list, tuple)) and len(color) == 3:
            return ("%02X%02X%02X" % (int(color[0]), int(color[1]), int(color[2])))
        return "FFFFFF"


class OptionItem(object):

    def __init__(self, value, msaValue, displayName):
        self.value = value
        self.msaValue = msaValue
        self.displayName = displayName


class DropdownParameter(BaseParameter):

    def __init__(self, path, options, defaultValue, disabledValue=None):
        super(DropdownParameter, self).__init__(path, defaultValue, disabledValue)
        self.options = options

    def toMsaValue(self, value):
        for i, option in enumerate(self.options):
            if option.value == value:
                return i
        return 0

    def fromMsaValue(self, msaValue):
        try:
            index = int(msaValue)
            if 0 <= index < len(self.options):
                return self.options[index].value
        except (ValueError, TypeError):
            pass
        return self.defaultValue

    def toJsonValue(self, value):
        return value

    def fromJsonValue(self, jsonValue):
        option = self.getOptionByValue(jsonValue)
        if option is None:
            raise Exception("Invalid value {} for config param {}".format(jsonValue, self.tokenName))
        return option.value

    def getOptionByValue(self, value):
        foundOptions = [option for option in self.options if option.value == value]
        return foundOptions[0] if len(foundOptions) > 0 else None

    def getOptionByMsaValue(self, msaValue):
        try:
            index = int(msaValue)
            if 0 <= index < len(self.options):
                return self.options[index]
        except (ValueError, TypeError):
            pass
        return self.getOptionByValue(self.defaultValue)

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "Dropdown",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "options": [
                {"label": option.displayName} for option in self.options
            ],
            "tooltip": createTooltip(
                header="{} ({}: {})".format(
                    header, 
                    Translator.DEFAULT_VALUE, 
                    self.getOptionByValue(self.defaultValue).displayName
                ),
                body=body,
                note=note,
                attention=attention
            ),
            "width": 200
        }


class RadioButtonGroupParameter(DropdownParameter):

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "RadioButtonGroup",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "options": [
                {"label": option.displayName} for option in self.options
            ],
            "tooltip": createTooltip(
                header="{} ({}: {})".format(
                    header, 
                    Translator.DEFAULT_VALUE, 
                    self.getOptionByValue(self.defaultValue).displayName
                ),
                body=body,
                note=note,
                attention=attention
            )
        }


class HotkeyParameter(BaseParameter):

    def __init__(self, path, defaultValue=None, disabledValue=None):
        if defaultValue is None:
            defaultValue = []
        super(HotkeyParameter, self).__init__(path, defaultValue, disabledValue)

    def toMsaValue(self, value):
        return value if value else []

    def fromMsaValue(self, msaValue):
        return msaValue if isinstance(msaValue, list) else []

    def toJsonValue(self, value):
        return value if value else []

    def fromJsonValue(self, jsonValue):
        return jsonValue if isinstance(jsonValue, list) else []

    def renderParam(self, header, body=None, note=None, attention=None):
        currentValue = self.toMsaValue(self.value)
        return {
            "type": "HotKey",
            "text": header,
            "varName": self.tokenName,
            "value": currentValue,
            "tooltip": createTooltip(
                header="{}".format(header),
                body=body,
                note=note,
                attention=attention
            )
        }


class LabelParameter(object):

    def renderParam(self, header, body=None, note=None, attention=None):
        return {
            'type': 'Label',
            'text': header,
            "tooltip": createTooltip(
                header=header,
                body=body,
                note=note,
                attention=attention
            )
        }
