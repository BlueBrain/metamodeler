# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 09:19:25 2016

@author: oreilly
"""

from copy import deepcopy
import os
import pickle
import fnmatch
from collections import OrderedDict

from nat.modelingParameter import getParameterTypes

from .modelParameter import AbstractParameterInstance, CustomParameterInstance, ModelParameterInstance
from .tagParser import TagParser

class ParamDic(OrderedDict):
    def __setitem__(self, key, value):
        if not isinstance(value, AbstractParameterInstance):
            raise TypeError
        super(ParamDic, self).__setitem__(key, value)



class ProjectSetup:

    ignore_patterns = ["*.*~"]
        
    def __init__(self, path):
        self.path = path
        self.files = {} # Indexed by file name
        self.properties = {}


        self.reloadMM()


    def reloadMM(self):

        for root, dirnames, filenames in os.walk(self.path):
            for filename in fnmatch.filter(filenames, '*.mm_*'):
                ignore=False
                for ignore_pattern in ProjectSetup.ignore_patterns:
                    if fnmatch.fnmatch(filename, ignore_pattern):
                        ignore=True

                if not ignore:
                    name = (os.path.join(root, filename).split(self.path)[1])[1:]
                    if name in self.files:
                        self.files[name].reprocessFile(os.path.join(root, filename), self.path)
                    else:
                        self.files[name] = FileSetup(os.path.join(root, filename))
                        self.files[name].preprocessFile(os.path.join(root, filename), self.path)
        self.save()

    def isComplete(self):
        for f in self.files:
            if not self.files[f].isComplete():
                return False
        return True

    def save(self):
        with open(os.path.join(self.path, ".mmproject.pck"), 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path):
        try:
            with open(os.path.join(path, ".mmproject.pck"), 'rb') as f:
                return pickle.load(f)
        except:
            return None

    def generateModel(self):
        for f in self.files:
            self.files[f].generateModel()

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"path": self.path,
                "files": {fName:f.toJSON() for fName, f in self.files.items()},
                "properties":self.properties}


class FileSetup:

    parameterTypes = getParameterTypes()
    
    def getIDFromName(paramName):
        paramID = None
        for paramType in FileSetup.parameterTypes:
            if paramType.name == paramName:
                paramID = paramType.ID
                break
        return paramID

    def __init__(self, fileName):
        self.fileName = fileName
        self.parameters = ParamDic() # Indexed by parameter name

    def isComplete(self):
        for key in self.parameters:
            if not self.parameters[key].isComplete():
                return False
        return True


    def preprocessFile(self, fileName, projectPath):
        """
        parser = TagParser()

        with open(os.path.join(projectPath, fileName), 'r') as f:
            fileText = f.read()

        for paramStr in parser.getParamStr(fileText):
        
            parser.getArgs(paramStr)
            paramName = parser.getParamName(paramStr)
            args      = parser.getArgs(paramStr)
            paramKey  = (paramName, args)
               
            paramID = FileSetup.getIDFromName(paramName)
            if paramID is None:
                parameter = CustomParameterInstance(paramName)
            else:
                parameter = ModelParameterInstance(paramID)

            if "unit" in args:
                parameter.requiredUnit = args["unit"]
            parameter.args = args

            self.parameters[paramKey] = parameter
        """
        self.parameters = ParamDic()
        self.reprocessFile(fileName, projectPath)

    def reprocessFile(self, fileName, projectPath):
        parser = TagParser()

        with open(os.path.join(projectPath, fileName), 'r') as f:
            fileText = f.read()

        oldDic = deepcopy(self.parameters)
        self.parameters = ParamDic()
        for paramStr in parser.getParamStr(fileText):
        
            parser.getArgs(paramStr)            
            paramName = parser.getParamName(paramStr)   
            args      = parser.getArgs(paramStr)  
            paramKey  = parser.getParamKey(paramStr)

            if paramKey in oldDic:
                self.parameters[paramKey] = oldDic[paramKey]
            else:
                paramID = FileSetup.getIDFromName(paramName)
                if paramID is None:
                    parameter = CustomParameterInstance(paramName)
                else:
                    parameter = ModelParameterInstance(paramID)

                if "unit" in args:
                    parameter.requiredUnit = args["unit"]
                parameter.args = args
    
                self.parameters[paramKey] = parameter
    



    def generateModel(self):
        with open(self.fileName, 'r') as f:
            text = f.read()

        for name, parameter in self.parameters.items():
            parser = TagParser()
            tagStr = parser.getParamTagStr(name, text)            
            
            text = text.replace(tagStr, str(parameter.value))

        with open(self.fileName.replace(".mm_", "."), 'w') as f:
            f.write(text)


    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"fileName": self.fileName,
                "parameters": {pName:p.toJSON() for pName, p in self.parameters.items()}}



