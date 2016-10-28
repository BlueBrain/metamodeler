# -*- coding: utf-8 -*-
"""
Created on Wed Oct 26 10:01:05 2016

@author: oreilly
"""

from PySide import QtCore


from nat.ontoManager import OntoManager  
from nat.tag import Tag

from collections import OrderedDict

class ProjectParameterModel(QtCore.QAbstractTableModel):

    dataChanged = QtCore.Signal(Tag)

    projectParamRootIDs = OrderedDict([("species", "NIFORG:birnlex_569"),         # "Eumetazoa"... includes almost all animals, except sponges, unicellular animals, and other obscure or existinct animals... according to Wikipedia
                                       ("brain_region", "NIFGA:birnlex_1167"),  # "Regional part of brain"
                                       ("cell_type", "sao1813327414")])          # "Cell"

    projectParamRootNames = OrderedDict([("species", "Eumetazoa"),         # includes almost all animals, except sponges, unicellular animals, and other obscure or existinct animals... according to Wikipedia
                                         ("brain_region", "Regional part of brain"), 
                                         ("cell_type", "Cell")]) 

    def __init__(self, parent, colHeader = ["Property", "Value"], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)

        self.colHeader             = colHeader
        self.nbCol                 = len(colHeader)

        ontoMng = OntoManager()
        self.treeData                  = ontoMng.trees 
        self.dicData                   = ontoMng.dics
    
        self.projectParamDict    = {"species": None, 
                                    "brain_region": None,
                                    "cell_type": None}


    def rowCount(self, parent=None):
        return len(self.projectParamDict)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        #print(role, int(QtCore.Qt.UserRole), int(QtCore.Qt.DisplayRole))
        if role == QtCore.Qt.DisplayRole:
            paramName = list(ProjectParameterModel.projectParamRootIDs.keys())[index.row()]
            if index.column() == 0:
                return paramName
            elif index.column() == 1:
                if self.projectParamDict[paramName] is None:
                    return ""
                return self.projectParamDict[paramName].name
            else:
                return None
        elif role == QtCore.Qt.UserRole:
            rootName = list(ProjectParameterModel.projectParamRootNames.values())[index.row()]            
            if index.column() == 0:
                return rootName
            else:
                return None
        else:
            return None



    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if value is None:
            value = ""

        if index.column() == 1:
            if self.checkTagValidity(index.row(), value):
                rootName = list(ProjectParameterModel.projectParamRootIDs.keys())[index.row()]                
                tagId = list(self.dicData.keys())[list(self.dicData.values()).index(value)]                    
                self.projectParamDict[rootName] = Tag(tagId, value)
                self.dataChanged.emit(self.projectParamDict[rootName])


    def checkTagValidity(self, row, tagName):
        rootId = list(ProjectParameterModel.projectParamRootIDs.values())[row]
        if not rootId in self.treeData:  
            raise ValueError("Tag '" + rootId + "' is not a treeData root. TreeData roots are the following:" + str(list(self.treeData.keys())))
        return tagName in list(self.treeData[rootId].values())


    def flags(self, index):
        if index.column() == 0:
            result = super(ProjectParameterModel, self).flags(index)
            result &= ~QtCore.Qt.ItemIsEditable
            return result
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.colHeader[section]        
        return None

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def getParamDict(self):
        return {key:tag.id for key, tag in self.projectParamDict.items() if not tag is None}


    def setParamDict(self, paramDic):
        for key in self.projectParamDict:
            if key in paramDic:
                self.projectParamDict[key] = Tag(paramDic[key], self.dicData[paramDic[key]])