#!/usr/bin/python3

__author__ = "Christian O'Reilly"


import quantities as pq
from copy import copy

from PySide import QtCore, QtGui

from nat.treeData import getChildrens
from nat.ontoManager import OntoManager  

from .referenceManager import ReferenceManager

class PropositionTableModel(QtCore.QAbstractTableModel):

    ontoMng = OntoManager()
    treeData = ontoMng.trees 
    dicData  = ontoMng.dics
    invDicData  = {value:key for key, value in dicData.items()}
    
    baseHeader = ["value", "unit", "authors", "year", "journal", "species", "cell type"]
    
    def __init__(self, *args):
        super(PropositionTableModel, self).__init__(*args)

        self.header = copy(PropositionTableModel.baseHeader)
        self.propositions = []
        self.refMng = ReferenceManager()

    def refreshData(self, parameterDF, attributes={}):
        self.propositions = []
        for index, row in parameterDF.iterrows():
            pubData = self.refMng.getInfoFromID(row["obj_annotation"].pubId)
            proposition = {}
            proposition["value"]     = row["Values"]
            proposition["unit"]      = row["Unit"]
            proposition["species"]    = "; ".join([spec.name + " (" + spec.id + ")" for spec in row["Species"]])
            proposition["speciesTag"]  = row["Species"]
            proposition["cell type"] = row["Cell"]
            proposition["authors"]  = pubData["authors"]
            proposition["year"]     = pubData["year"]
            proposition["journal"]  = pubData["journal"]
            proposition["obj_annotation"] = row["obj_annotation"]
            proposition["obj_parameter"]  = row["obj_parameter"]
            
            self.header = copy(PropositionTableModel.baseHeader)
            for reqTag in row["obj_parameter"].requiredTags:
                rootName = PropositionTableModel.dicData[reqTag.rootId]
                if rootName != "Cell":
                    self.header.append(rootName)
                    proposition[rootName] = reqTag.name
                        
            proposition["score"]          = 0.0
            proposition["color"]          = []
            self.propositions.append(proposition)
          
    
        self.computeScores(attributes)
        self.propositions = sorted(self.propositions, key=lambda prop: prop["score"], reverse=True)
        self.refresh()



    def computeScores(self, attributes):
        
        for proposition in self.propositions:        
            
            if "unit" in attributes:
                #weight -10            
                quant = pq.Quantity(proposition["value"], proposition["unit"])
                try:
                    quant = quant.rescale(attributes["unit"])
                    proposition["value"] = quant.item() 
                    proposition["unit"]  = str(quant.dimensionality)
                except:
                    proposition["score"] -= 10
                    proposition["color"].append("unit")
                            
            if "species" in attributes:
                # weight +/- 1  for right or wrong species... 
                # but would idealy consider the "distance" between species

                speciesHit = False
                if len(proposition["speciesTag"]) != 0:                         
                    # The requested species (e.g., Rat id)...                    
                    acceptableSpecies = [attributes["species"]]
                    # The sublases of the resquested species (e.g., Wistar rat id...)
                    acceptableSpecies.extend(getChildrens(attributes["species"]).keys())                
                    for species in proposition["speciesTag"]:
                        if species.id in acceptableSpecies:
                            speciesHit = True
                            break
                        
                if speciesHit:
                    proposition["score"] += 1                     
                else:
                    proposition["score"] -= 1
                    proposition["color"].append("species")


            if "cell_type" in attributes:
                hit = False
                for reqTag in proposition["obj_parameter"].requiredTags:
                    if reqTag.rootId in ["NIFCELL:sao1813327414", "sao1813327414"]:
                        acceptable = [attributes["cell_type"]]
                        # The sublases of the resquested species (e.g., Wistar rat id...)
                        acceptable.extend(getChildrens(attributes["cell_type"]).keys())  
                        if reqTag.id in acceptable:
                            hit = True
                            break
                if hit:
                    proposition["score"] += 2                     
                else:                        
                    proposition["score"] -= 2
                    proposition["color"].append("cell type")


            for reqTag in proposition["obj_parameter"].requiredTags:
                rootName = PropositionTableModel.dicData[reqTag.rootId] 
                if rootName in attributes:
                    attributeKey = PropositionTableModel.invDicData[attributes[rootName]] 
                    acceptable = [attributeKey]
                    acceptable.extend(getChildrens(attributeKey).keys())  
                    if reqTag.id in acceptable:
                        proposition["score"] += 1
                    else:
                        proposition["score"] -= 1
                        proposition["color"].append(rootName)
                            

                        
            #"brain_region"
  
    
            #if "cell_type" in attributes:
            #    #weight -2
            #    ...
            

    def rowCount(self, parent = None):
        return len(self.propositions)

    def columnCount(self, parent = None):
        return len(self.header)



    def data(self, index, role):
        if not index.isValid():
            return None


        #if role == QtCore.Qt.BackgroundRole:
        #    if self.checkIdFct(self.getID(index.row())):
        #        return QtGui.QBrush(QtGui.QColor(215, 214, 213), QtCore.Qt.SolidPattern)
        #    else:
        #        return None


        if role == QtCore.Qt.BackgroundRole:
            colorDic = self.propositions[index.row()]["color"]
            if self.header[index.column()] in colorDic:
                color = QtGui.QColor(255, 255, 0)
                return QtGui.QBrush(color, QtCore.Qt.SolidPattern)
            return None


        if role == QtCore.Qt.DisplayRole:
            try:
                return self.propositions[index.row()][self.header[index.column()]]
            except KeyError:
                return None
        return None


    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    #def sort(self, col, order):
    #    #sort table by given column number col
    #    self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
    #    reverse = (order == QtCore.Qt.DescendingOrder)
    #    self.refList = sorted(self.refList, key=lambda x: self.getByIndex(x, col), reverse = reverse)
    #    self.emit(QtCore.SIGNAL("layoutChanged()"))

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))



