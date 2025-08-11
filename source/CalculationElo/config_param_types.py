PARAM_REGISTRY = {}

class Option(object):
    def __init__(self, value, msaValue, displayName):
        self.value = value
        self.msaValue = msaValue
        self.displayName = displayName

class BooleanParam(object):
    def __init__(self, path, defaultValue=False):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue
        self.defaultValue = defaultValue
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        self.value = bool(value)

class OptionsParam(object):
    def __init__(self, path, options, defaultValue):
        self.path = path
        self.tokenName = "-".join(path)
        self.options = options
        self.value = defaultValue
        self.defaultValue = defaultValue
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        for option in self.options:
            if option.value == self.value:
                return option.msaValue
        return 0

    @msaValue.setter
    def msaValue(self, value):
        for option in self.options:
            if option.msaValue == value:
                self.value = option.value
                return
        self.value = self.defaultValue

class ColorParam(object):
    def __init__(self, path, defaultValue=None):
        self.path = path
        self.tokenName = "-".join(path)
        self.value = defaultValue if defaultValue is not None else [255, 255, 255]
        self.defaultValue = self.value
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        if isinstance(value, list) and len(value) == 3:
            self.value = [int(v) for v in value]
        else:
            self.value = self.defaultValue

    def getHexColor(self):
        r, g, b = self.value
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

class SliderParam(object):
    def __init__(self, path, minValue=0, maxValue=1, defaultValue=0):
        self.path = path
        self.tokenName = "-".join(path)
        self.minValue = minValue
        self.maxValue = maxValue
        self.value = defaultValue
        self.defaultValue = defaultValue
        PARAM_REGISTRY[self.tokenName] = self

    @property
    def msaValue(self):
        return self.value

    @msaValue.setter
    def msaValue(self, value):
        try:
            self.value = max(self.minValue, min(self.maxValue, float(value)))
        except:
            self.value = self.defaultValue