# -*- coding: utf-8 -*-

class Template(object):
    
    def __init__(self, configParams):
        self.configParams = configParams
        self.modDisplayName = None
        self.column1Items = []
        self.column2Items = []

    def _defaultEnabled(self):
        enabledParam = getattr(self.configParams, 'enabled', None)
        return enabledParam.defaultValue if enabledParam else True

    def setModDisplayName(self, name):
        self.modDisplayName = unicode(name) if hasattr(__builtins__, 'unicode') else str(name)
        return self
    
    def addToColumn1(self, item):
        if isinstance(item, dict):
            self.column1Items.append(item)
        return self
    
    def addToColumn2(self, item):
        if isinstance(item, dict):
            self.column2Items.append(item)
        return self

    def addParameterToColumn1(self, paramName, header=None, body=None, note=None, attention=None):
        param = getattr(self.configParams, paramName, None)
        if param and hasattr(param, 'renderParam'):
            renderedParam = param.renderParam(
                header=header or paramName.title(),
                body=body,
                note=note,
                attention=attention
            )
            self.addToColumn1(renderedParam)
        return self

    def addParameterToColumn2(self, paramName, header=None, body=None, note=None, attention=None):
        param = getattr(self.configParams, paramName, None)
        if param and hasattr(param, 'renderParam'):
            renderedParam = param.renderParam(
                header=header or paramName.title(),
                body=body,
                note=note,
                attention=attention
            )
            self.addToColumn2(renderedParam)
        return self
    
    def clearColumns(self):
        self.column1Items = []
        self.column2Items = []
        return self
    
    def generateTemplate(self):  
        template = {
            'modDisplayName': self.modDisplayName,
            'enabled': self._defaultEnabled(),
            'column1': list(self.column1Items),
            'column2': list(self.column2Items)
        }
        
        return template