#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Standard imports
import sys
import os
import fnmatch
import re
import numpy as np
import pickle

# Contributed libraries imports
from PySide import QtGui, QtCore

# Local imports
from .proposer import PropositionTableModel
from .modelParameter import ModelParameterInstance, CustomParameterInstance, AbstractParameterInstance
from .settingsDlg import getSettings, SettingsDlg
from .utils import prettyPrintJSON

# Import from nat
from nat.modelingParameter import getParameterTypes
from nat.annotationSearch import ParameterSearch, ConditionAtom, CompiledCorpus
from nat.gitManager import GitManager


class IncompleteItem(QtGui.QListWidgetItem):

    def __lt__(self, other):
        return stripIncomplete(self.text()) < stripIncomplete(other.text())



def stripIncomplete(string):
    if string[:2] == "* ":
        return string[2:]
    return string


class ProjectSetup:
    def __init__(self, path):
        self.path = path
        self.files = {} # Indexed by file name


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
                "files": {fName:f.toJSON() for fName, f in self.files.items()}}


class ParamDic(dict):
    def __setitem__(self, key, value):
        if not isinstance(value, AbstractParameterInstance):
            raise TypeError
        super(ParamDic, self).__setitem__(key, value)

class FileSetup:

    def __init__(self, fileName):
        self.fileName = fileName
        self.parameters = ParamDic() # Indexed by parameter name

    def isComplete(self):
        for paramName in self.parameters:
            if not self.parameters[paramName].isComplete():
                return False
        return True


    def generateModel(self):
        with open(self.fileName, 'r') as f:
            text = f.read()

        for name, parameter in self.parameters.items():
            text = text.replace("#|" + name + "|#", str(parameter.value))

        with open(self.fileName.replace(".mm_", "."), 'w') as f:
            f.write(text)


    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"fileName": self.fileName,
                "parameters": {pName:p.toJSON() for pName, p in self.parameters.items()}}


class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()


        self.interfaceSetup = False
        self.sourceRef = None
        self.setupMenus()
        self.setupWindowsUI()
        self.dbPath = '/home/oreilly/Dropbox/code/curator/DB/'
        self.parameterTypes = getParameterTypes()
        #self.currentModelingParam = None
        self.projectSetup = None
        self.ignore_patterns = ["*.*~"]
        
        self.noUpdatePropositionSelection = False

        self.editPreferences()

        self.gitMng = GitManager(self.settings.config["GIT"])

        self.dbPath   = os.path.abspath(self.settings.config["GIT"]["local"])        
        self.compiledCorpus = CompiledCorpus(os.path.join(self.dbPath, "annotations.bin"))    
        self.compiledCorpus.compileCorpus(pathDB=self.dbPath)
        self.searcher = ParameterSearch(pathDB=self.dbPath, compiledCorpus=self.compiledCorpus)


    def editPreferences(self):
        # Load saved settings
        self.settings = getSettings()
        if self.settings is None:
            self.close()
            self.deleteLater()
            return





    def setupMenus(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        openPreferencesAction = QtGui.QAction(QtGui.QIcon(), '&Preferences', self)
        openPreferencesAction.setStatusTip('Edit preferences')
        openPreferencesAction.triggered.connect(self.editPreferences)


        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)

        editMenu = menubar.addMenu('&Edit')
        editMenu.addAction(openPreferencesAction)


    def setupWindowsUI(self) :

        self.setupProjectGB()
        self.setupPropertiesGB()
        self.setupParamGB()
        self.setupPropositionsGB()
        self.setupCustomGB()
        self.setupSourceGB()

        # Main layout
        self.mainWidget = QtGui.QWidget(self)
        self.mainGrid = QtGui.QVBoxLayout(self.mainWidget)
        self.mainGrid.addWidget(self.projectGroupBox)
        self.mainGrid.addWidget(self.propertiesGroupBox)
        self.mainGrid.addWidget(self.paramsGroupBox)
        self.mainGrid.addWidget(self.sourceGroupBox)

        self.setCentralWidget(self.mainWidget)
        self.interfaceSetup = True
        self.setSource("lit")



    def setupSourceGB(self):
        # Widgets
        self.fromLitRadio = QtGui.QRadioButton("From literature")
        self.customRadio = QtGui.QRadioButton("Custom value")

        # Layout
        self.sourceGroupBox = QtGui.QGroupBox("Source of parameter values")
        vbox = QtGui.QHBoxLayout()
        vbox.addWidget(self.fromLitRadio)
        vbox.addWidget(self.customRadio)
        vbox.addStretch(1)
        self.sourceGroupBox.setLayout(vbox)

        # Signals
        self.fromLitRadio.toggled.connect(self.fromLitToggled)
        self.customRadio.toggled.connect(self.customToggled)

        # Initial behavior
        self.fromLitRadio.setChecked(True)


    def fromLitToggled(self, checked):
        if checked:
            self.setSource("lit")


    def customToggled(self, checked):
        if checked:
            self.setSource("custom")

    def setSource(self, source):
        if not self.interfaceSetup:
            return
        if not self.sourceRef is None:
            self.mainGrid.removeWidget(self.sourceRef)

        if source == "lit":
            self.sourceRef = self.propositionsGroupBox
            self.customGroupBox.setVisible(False)
            self.propositionsGroupBox.setVisible(True)

        elif source == "custom":
            self.sourceRef = self.customGroupBox
            self.customGroupBox.setVisible(True)
            self.propositionsGroupBox.setVisible(False)
        else:
            raise ValueError

        self.mainGrid.addWidget(self.sourceRef)


    def setupProjectGB(self):
        # Widgets
        self.openProjectBtn = QtGui.QPushButton("Open project")
        self.generateBtn    = QtGui.QPushButton("Generate model")
        self.projectFiles   = QtGui.QListWidget()

        # Layout
        self.projectGroupBox = QtGui.QGroupBox("Project")
        grid                 = QtGui.QGridLayout(self.projectGroupBox)
        grid.addWidget(self.projectFiles, 0, 0, 1, 3)
        grid.addWidget(self.openProjectBtn, 1, 0)
        grid.addWidget(self.generateBtn, 1, 1)
        #grid.addWidget(QtGui.QSpacerItem(), 1, 2)

        # Signals
        self.openProjectBtn.clicked.connect(self.openProject)
        self.generateBtn.clicked.connect(self.generateModel)
        self.projectFiles.currentTextChanged.connect(self.fileSelected)

        # Initial behavior
        self.generateBtn.setDisabled(True)

    def setupPropertiesGB(self):
        # Widgets

        # Layout
        self.propertiesGroupBox     = QtGui.QGroupBox("")
        grid                         = QtGui.QGridLayout(self.propertiesGroupBox)

        # Signals

        # Initial behavior



    def setupParamGB(self):
        # Widgets
        self.paramList        = QtGui.QListWidget()
        self.paramList.setSortingEnabled(True)
        self.codeText        = QtGui.QTextEdit()

        # Layout
        self.paramsGroupBox     = QtGui.QGroupBox("Parameters")
        grid                     = QtGui.QGridLayout(self.paramsGroupBox)
        grid.addWidget(self.paramList, 0, 0)
        grid.addWidget(self.codeText, 0, 1)

        # Signals
        self.paramList.currentTextChanged.connect(self.parameterSelected)

        # Initial behavior
        self.codeText.setWordWrapMode(QtGui.QTextOption.NoWrap)


    def setupPropositionsGB(self):
        # Widgets
        self.propositionTblWdg      = QtGui.QTableView()
        self.propositionTableModel     = PropositionTableModel(self)
        self.propositionTblWdg.setModel(self.propositionTableModel)
        self.propositionTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #self.propositionTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.propositionTblWdg.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        # Layout
        self.propositionsGroupBox     = QtGui.QGroupBox("Proposed values from curated literature")
        grid                         = QtGui.QGridLayout(self.propositionsGroupBox)
        grid.addWidget(self.propositionTblWdg, 0, 0)


        # Signals
        selection = self.propositionTblWdg.selectionModel()
        selection.selectionChanged.connect(self.selectedPropositionChanged)
        self.propositionTblWdg.model().emit(QtCore.SIGNAL("layoutChanged()"))
        # Initial behavior






    def setupCustomGB(self):
        # Widgets
        self.customValue         = QtGui.QLineEdit(self)
        self.customUnit         = QtGui.QLineEdit(self)
        self.justification         = QtGui.QTextEdit(self)
        self.saveCustomBtn         = QtGui.QPushButton("Save", self)


        # Layout
        self.customGroupBox     = QtGui.QGroupBox("Use a custom value not linked with the literature")
        grid                     = QtGui.QGridLayout(self.customGroupBox)
        grid.addWidget(QtGui.QLabel("Value for the parameter"), 0, 0)
        grid.addWidget(self.customValue , 1, 0)
        grid.addWidget(QtGui.QLabel("Unit"), 0, 1)
        grid.addWidget(self.customUnit , 1, 1)
        grid.addWidget(self.saveCustomBtn , 1, 2)
        grid.addWidget(QtGui.QLabel("Please provide explanation of how this value has been chosen"), 2, 0, 1, 3)
        grid.addWidget(self.justification, 3, 0, 1, 3)

        # Signals
        self.saveCustomBtn.clicked.connect(self.saveCustom)

        # Initial behavior


    def clearCustom(self):
        self.customValue.setText("")
        self.customUnit.setText("")
        self.justification.setPlainText("")



    def openProject(self):
        self.projectPath = QtGui.QFileDialog.getExistingDirectory(self, "Select project folder", options = QtGui.QFileDialog.ShowDirsOnly)
        self.projectSetup = ProjectSetup.load(self.projectPath)

        if self.projectSetup is None:
            self.projectSetup = ProjectSetup(self.projectPath)

            matches = []
            for root, dirnames, filenames in os.walk(self.projectPath):
                for filename in fnmatch.filter(filenames, '*.mm_*'):
                    ignore=False
                    for ignore_pattern in self.ignore_patterns:
                        if fnmatch.fnmatch(filename, ignore_pattern):
                            ignore=True

                    if not ignore:
                        path = os.path.join(root, filename)
                        self.preprocessFile(path)

        self.refreshFileList()



    def refreshFileList(self):
        self.projectFiles.clear()

        for name in self.projectSetup.files:
            if not self.projectSetup.files[name].isComplete():
                name = "* " + name
            item = IncompleteItem(name)
            self.projectFiles.addItem(item) #name)

        self.generateBtn.setEnabled(self.projectSetup.isComplete())



    def refreshFileStatus(self):

        row = self.projectFiles.currentRow()
        fileName = self.projectFiles.item(row).text()
        fileName = stripIncomplete(fileName)

        if not self.projectSetup.files[fileName].isComplete():
            fileName = "* " + fileName

        self.projectFiles.item(row).setText(fileName)
        self.generateBtn.setEnabled(self.projectSetup.isComplete())


    def generateModel(self):
        self.projectSetup.generateModel()

    def getIDFromName(self, paramName):
        paramID = None
        for paramType in self.parameterTypes:
            if paramType.name == paramName:
                paramID = paramType.ID
                break
        return paramID



    def preprocessFile(self, fileName):
        name = (fileName.split(self.projectPath)[1])[1:]
        self.projectSetup.files[name] = FileSetup(fileName)

        p = re.compile('\#\|[0-9a-zA-Z_]+\|\#')

        with open(os.path.join(self.projectPath, fileName), 'r') as f:
            fileText = f.read()

        for param in p.findall(fileText):
            paramID = self.getIDFromName(param[2:-2])
            if paramID is None:
                self.projectSetup.files[name].parameters[param[2:-2]] = CustomParameterInstance(param[2:-2])
            else:
                self.projectSetup.files[name].parameters[param[2:-2]] = ModelParameterInstance(paramID)



    def fileSelected(self, fileName):
        if fileName != "":
            self.refreshParamList(fileName)



    def refreshParamList(self, fileName, resetIndex = True):

        if resetIndex == False:
            row = self.paramList.currentRow()

        self.paramList.clear()

        fileName = stripIncomplete(fileName)

        for name, param in self.projectSetup.files[fileName].parameters.items():
            if param.isComplete():
                item = IncompleteItem(name)
            else:
                item = IncompleteItem("* " + name)

            paramID = self.getIDFromName(name)
            if paramID is None:
                item.setBackground(QtCore.Qt.lightGray)
            self.paramList.addItem(item)

        if resetIndex == False:
            self.paramList.setCurrentRow(row)



    def updateCodeContext(self, parameterStr):
        nbLineContext = 3
        p = re.compile('\#\|' + parameterStr + '\|\#')

        fileName = stripIncomplete(self.projectFiles.currentItem().text())

        with open(os.path.join(self.projectPath, fileName), 'r') as f:
            lines = f.readlines()



        hits = []
        for noLine, line in enumerate(lines):
            if not p.search(line) is None:
                hits.extend(range(max(noLine-nbLineContext, 0), min(noLine+nbLineContext+1, len(lines))))

        hits = np.unique(hits)
        lastAddedLine = -1
        codeText = ""
        for hit in hits:
            if hit - lastAddedLine > 1 :
                codeText += "[...]\n"
            codeText += str(hit+1).ljust(5) + lines[hit]
            lastAddedLine = hit

        if lastAddedLine < len(lines)-1:
            codeText += "[...]\n"
        self.codeText.setText(codeText)

        match = p.search(codeText)
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtCore.Qt.yellow)
        cursor = QtGui.QTextCursor(self.codeText.document())
        cursor.setPosition(match.start(), QtGui.QTextCursor.MoveAnchor)
        cursor.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
        cursor.setCharFormat(fmt)





    def parameterSelected(self, parameterStr):

        if parameterStr == "":
            return
        needLoading = parameterStr[:2] != "* "

        parameterStr = stripIncomplete(parameterStr)

        self.updateCodeContext(parameterStr)

        if self.getIDFromName(parameterStr) is None:
            self.fromLitRadio.setEnabled(False)
            self.customRadio.setChecked(True)
        else:
            self.fromLitRadio.setEnabled(True)
            self.fromLitRadio.setChecked(True)
            self.proposeValuesFromCuration()

        if needLoading:
            self.loadParamValues(parameterStr)
        else:
            self.clearCustom()
            self.propositionTblWdg.clearSelection()


    @property
    def selectedParameter(self):
        paramName           = stripIncomplete(self.paramList.currentItem().text())
        fileName            = stripIncomplete(self.projectFiles.currentItem().text())
        return self.projectSetup.files[fileName].parameters[paramName]
        
    @selectedParameter.setter
    def selectedParameter(self, param):
        paramName           = stripIncomplete(self.paramList.currentItem().text())
        fileName            = stripIncomplete(self.projectFiles.currentItem().text())
        self.projectSetup.files[fileName].parameters[paramName] = param
        
        

    def loadParamValues(self, parameterStr):

        selectedParameter   = self.selectedParameter
        if isinstance(selectedParameter, CustomParameterInstance):
            self.customRadio.setChecked(True)
            self.customValue.setText(str(selectedParameter.value))
            self.customUnit.setText(selectedParameter.unit)
            self.justification.setText(selectedParameter.justification)

        elif isinstance(selectedParameter, ModelParameterInstance):
            self.fromLitRadio.setChecked(True)

            self.noUpdatePropositionSelection = True
            self.propositionTblWdg.selectionModel().clearSelection()
            for noProposition, proposition in enumerate(self.propositionTblWdg.model().propositions):
                if proposition["obj_parameter"].id in selectedParameter.ids :
                    #self.propositionTblWdg.selectRow(noProposition)
                    selected = self.propositionTblWdg.model().index(noProposition, 0)
                    flags = QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows
                    self.propositionTblWdg.selectionModel().select(selected, flags)
            self.noUpdatePropositionSelection = False

        else:
            raise TypeError("selectedParameter should be of type CustomParameterInstance or ParameterInstance. Type passed: " + str(type(selectedParameter)))






    def proposeValuesFromCuration(self):

        paramName = stripIncomplete(self.paramList.currentItem().text())
        #paramID = None
        #
        #for paramType in self.parameterTypes:
        #    if paramType.name == paramName:
        #        paramID = paramType.ID
        #        break
        #if paramID is None:
        #    raise ValueError("This parameter is not in our parameter dictionnary.")


        #self.currentModelingParam = ParameterInstance(paramID)
        #searcher.setSearchConditions(ConditionAtom("Parameter ID", paramID))
        self.searcher.setSearchConditions(ConditionAtom("Parameter name", paramName))
        self.searcher.expandRequiredTags = True
        self.searcher.onlyCentralTendancy = True
        resultDF = self.searcher.search()
        self.propositionTableModel.refreshData(resultDF) #annotatedInstances, self.currentModelingParam)


    def selectedPropositionChanged(self, selected, deselected):

        if self.noUpdatePropositionSelection:
            return

        selectedParameter = self.selectedParameter
        if isinstance(selectedParameter, CustomParameterInstance):
            return

        rows = []
        selectModel = self.propositionTblWdg.selectionModel()
        if selectModel.hasSelection():
            rows = [ind.row() for ind in selectModel.selectedRows()]

        selectedPropositions = [self.propositionTblWdg.model().propositions[row] for row in rows]
        referenceInstances = [prop["obj_parameter"] for prop in selectedPropositions]
        if set(referenceInstances) != set(selectedParameter.referenceInstances):
            selectedParameter.referenceInstances = referenceInstances
            fileName = stripIncomplete(self.projectFiles.currentItem().text())
            self.refreshParamList(fileName, resetIndex=False)
            self.refreshFileStatus()
            self.projectSetup.save()


    def saveCustom(self):
        paramName = stripIncomplete(self.paramList.currentItem().text())
        param = CustomParameterInstance(paramName, self.justification.toPlainText())
        param.setValue(float(self.customValue.text()), self.customUnit.text())
        self.selectedParameter = param
        
        fileName = stripIncomplete(self.projectFiles.currentItem().text())        
        self.refreshParamList(fileName, resetIndex=False) 
        self.refreshFileStatus()
        self.projectSetup.save()


