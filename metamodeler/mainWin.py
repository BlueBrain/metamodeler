#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Standard imports
import os
import re
import numpy as np
from copy import copy

# Contributed libraries imports
from PySide import QtGui, QtCore

# Local imports
from .projectParameterWgt import ProjectParameterModel
from .proposer import PropositionTableModel
from .modelParameter import ModelParameterInstance, CustomParameterInstance
from .settingsDlg import getSettings
from .tagParser import TagParser
from .projectSetup import ProjectSetup

# Import from nat
from nat.modelingParameter import getParameterTypes
from nat.annotationSearch import ParameterSearch, ConditionAtom, CompiledCorpus
from nat.gitManager import GitManager
from nat.tag import Tag

# Import from neurocurator
from neurocurator.modParamWidgets import RequiredTagsTableView


class IncompleteItem(QtGui.QListWidgetItem):

    def __lt__(self, other):
        return stripIncomplete(self.text()) < stripIncomplete(other.text())



def stripIncomplete(string):
    if string[:2] == "* ":
        return string[2:]
    return string



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
        #self.setupPropertiesGB()
        self.setupParamGB()
        self.setupPropositionsGB()
        self.setupCustomGB()
        self.setupSourceGB()

        # Main layout
        self.mainGrid = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.mainGrid.setOrientation(QtCore.Qt.Vertical)
        self.mainGrid.addWidget(self.projectGroupBox)
        #self.mainGrid.addWidget(self.propertiesGroupBox)
        self.mainGrid.addWidget(self.paramsGroupBox)
        self.mainGrid.addWidget(self.sourceGroupBox)

        self.sourceStack       = QtGui.QStackedWidget(self)
        self.sourceStack.addWidget(self.propositionsGroupBox)
        self.sourceStack.addWidget(self.customGroupBox)
        self.sourceStack.setCurrentIndex(0)
        self.mainGrid.addWidget(self.sourceStack)

        

        self.setCentralWidget(self.mainGrid)
        self.interfaceSetup = True


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
        if not self.interfaceSetup:
            return
        if checked:
            self.sourceStack.setCurrentIndex(0)


    def customToggled(self, checked):
        if not self.interfaceSetup:
            return
        if checked:
            self.sourceStack.setCurrentIndex(1)


    def setupProjectGB(self):
        # Widgets
        self.openProjectBtn     = QtGui.QPushButton("Open project")
        self.reloadBtn          = QtGui.QPushButton("Reload meta-model")
        self.generateBtn        = QtGui.QPushButton("Generate model")
        self.projectFiles       = QtGui.QListWidget()
        
        self.projectParamView      = RequiredTagsTableView()
        self.projectParamModel     = ProjectParameterModel(self)
        self.projectParamView.setModel(self.projectParamModel)
        self.projectParamView.setEnabled(False)
        self.projectParamModel.dataChanged.connect(self.projectPropertiesChanged)


        # Layout
        self.projectGroupBox = QtGui.QGroupBox("Project")
        grid                 = QtGui.QGridLayout(self.projectGroupBox)
        grid.addWidget(self.projectFiles, 0, 0, 1, 2)
        grid.addWidget(self.projectParamView, 0, 2, 1, 2)
        grid.addWidget(self.openProjectBtn, 1, 0)
        grid.addWidget(self.reloadBtn, 1, 1)
        grid.addWidget(self.generateBtn, 1, 2)

        # Signals
        self.openProjectBtn.clicked.connect(self.openProject)
        self.reloadBtn.clicked.connect(self.reloadMetamodel)
        self.generateBtn.clicked.connect(self.generateModel)
        self.projectFiles.currentTextChanged.connect(self.fileSelected)

        # Initial behavior
        self.generateBtn.setDisabled(True)
        self.reloadBtn.setDisabled(True)

    @QtCore.Slot(object, Tag)
    def projectPropertiesChanged(self, tag):
        self.projectSetup.properties = self.projectParamModel.getParamDict()
        self.projectSetup.save()
        
        # Refresh the proposition table so that the coloring reflect
        # the project properties.
        self.proposeValuesFromCuration()



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
        self.codeText.setReadOnly(True)


    def setupPropositionsGB(self):
        # Widgets
        self.propositionTblWdg         = QtGui.QTableView()
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

        self.projectParamView.setEnabled(True)
        self.reloadBtn.setEnabled(True)
        self.projectParamModel.setParamDict(self.projectSetup.properties)
        self.refreshFileList()


    def reloadMetamodel(self):
        self.projectSetup.reloadMM()
        self.projectParamModel.setParamDict(self.projectSetup.properties)
        self.refreshFileList()
        self.paramList.clear()


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



    def fileSelected(self, fileName):
        if fileName != "":
            self.refreshParamList(fileName)



    def refreshParamList(self, fileName, resetIndex = True):

        if resetIndex == False:
            row = self.paramList.currentRow()

        self.paramList.clear()

        fileName = stripIncomplete(fileName)

        for (name, args), param in self.projectSetup.files[fileName].parameters.items():
            if param.isComplete():
                item = IncompleteItem(name + "(" + str(args) + ")")
            else:
                item = IncompleteItem("* " + name + "(" + str(args) + ")")

            paramID = self.getIDFromName(name)
            if paramID is None:
                item.setBackground(QtCore.Qt.lightGray)
            self.paramList.addItem(item)

        if resetIndex == False:
            self.paramList.setCurrentRow(row)



    def updateCodeContext(self, parameterStr):
        nbLineContext = 3
        fileName = stripIncomplete(self.projectFiles.currentItem().text())

        with open(os.path.join(self.projectPath, fileName), 'r') as f:
            lines = f.readlines()


        
        reStr = TagParser.getREStr(paramName=parameterStr.split("(")[0])          
        p = re.compile(reStr)
        parser = TagParser()

        hits = []
        for noLine, line in enumerate(lines):
            if not p.search(line) is None:
                paramTagStr =  line.split("#|")[1].split("|#")[0]
                name, args = parser.getParamKey("#|" + paramTagStr + "|#")
                if name + "(" + str(args) + ")" == parameterStr:
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
        paramName = parameterStr.split("(")[0]
        if self.getIDFromName(paramName) is None:
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


    def __selectedParameter(self):
        paramKey = stripIncomplete(self.paramList.currentItem().text())
        paramName = paramKey.split("(")[0]
        paramKey = (paramName, paramKey[len(paramName)+1:-1])
        fileName = stripIncomplete(self.projectFiles.currentItem().text())
        return fileName, paramKey
   
    @property
    def selectedParameter(self):
        fileName, paramKey = self.__selectedParameter()
        return self.projectSetup.files[fileName].parameters[paramKey]
        
    @selectedParameter.setter
    def selectedParameter(self, param):
        fileName, paramKey = self.__selectedParameter()
        self.projectSetup.files[fileName].parameters[paramKey] = param
        
        
        

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

        paramName = stripIncomplete(self.paramList.currentItem().text()).split("(")[0]
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
        
        args = copy(self.projectParamModel.getParamDict())
        args.update(self.selectedParameter.args)  
        
        self.propositionTableModel.refreshData(resultDF, args) #annotatedInstances, self.currentModelingParam)
        


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


