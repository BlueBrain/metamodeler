# -*- coding: utf-8 -*-
"""
Created on Tue Oct 25 16:39:06 2016

@author: oreilly
"""

import re
from collections import OrderedDict

class TagParser:
    
    acceptedCharQuote   = '"[0-9a-zA-Z_\(\)\-\+*^/\s]+"'
    acceptedCharNoQuote = '[0-9a-zA-Z_]+'
    attributeKeyVal     =  "(?:" + acceptedCharQuote + "|" + acceptedCharNoQuote + ")"
    
    reBeginMarker       = '\#\|'
    reParamName         = '[0-9a-zA-Z_]+'
    argAndValue         = attributeKeyVal + '\s*=\s*' + attributeKeyVal           
    optionalParenthesis = '(?:\({0}(?:\s*,\s*{0})*\))?'.format(argAndValue)
    reEndMarker         = '\|\#'
    paramREStr = reBeginMarker + reParamName +  optionalParenthesis + reEndMarker    
    p = re.compile(paramREStr)

    def getParamStr(self, text):
        return TagParser.p.findall(text)
    
    def getParamName(self, paramStr):
        return re.match(TagParser.reParamName, paramStr[2:-2]).group(0)      

        
    def getArgs(self, paramStr):
        argAndValueList = re.findall(TagParser.argAndValue, paramStr)
        args = OrderedDict()
        for argAndValueStr in argAndValueList:
            arg, value = argAndValueStr.split("=")
            value = value.strip()
            if value[0] == '"':
                value = value[1:-1]
            arg = arg.strip()
            if arg[0] == '"':
                arg = arg[1:-1]            
            args[arg] = value 
        return args
    
    def getREStr(paramName=None):
        if paramName is None:
            return TagParser.paramREStr
        else:
            return TagParser.reBeginMarker + paramName +  TagParser.optionalParenthesis + TagParser.reEndMarker  
        
    def getParamTagStr(self, paramName, text):
        return re.search(TagParser.getREStr(paramName), text).group(0)      
        
    def getParamKey(self, paramStr):
        paramName = self.getParamName(paramStr)   
        args      = self.getArgs(paramStr)  
        return (paramName, ", ".join(['"' + key + '"="' + val + '"'  for key, val in args.items()]))
        