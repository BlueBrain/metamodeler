#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import sys
from PySide import QtGui, QtCore

from nat.id import getInfoFromID

class PropositionTableModel(QtCore.QAbstractTableModel):

    def __init__(self, *args):
        super(PropositionTableModel, self).__init__(*args)

        self.header = ["value", "unit", "authors", "year", "journal"]
        self.nbCol = len(self.header)
        self.propositions = []

    def refreshData(self, parameterDF):
        self.propositions = []
        for index, row in parameterDF.iterrows():
            pubData = getInfoFromID(row["obj_annotation"].pubId)
            proposition = {}
            proposition["value"]    = row["Values"]
            proposition["unit"]     = row["Unit"]
            proposition["authors"]  = pubData["authors"]
            proposition["year"]     = pubData["year"]
            proposition["journal"]  = pubData["journal"]
            proposition["obj_annotation"] = row["obj_annotation"]
            proposition["obj_parameter"]  = row["obj_parameter"]
            self.propositions.append(proposition)

        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def rowCount(self, parent = None):
        return len(self.propositions)

    def columnCount(self, parent = None):
        return self.nbCol 



    def data(self, index, role):
        if not index.isValid():
            return None


        #if role == QtCore.Qt.BackgroundRole:
        #    if self.checkIdFct(self.getID(index.row())):
        #        return QtGui.QBrush(QtGui.QColor(215, 214, 213), QtCore.Qt.SolidPattern)
        #    else:
        #        return None

        if role == QtCore.Qt.DisplayRole:
            try:
                return self.propositions[index.row()][self.header[index.column()]]
            except KeyError:
                return ""
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



