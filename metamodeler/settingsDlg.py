#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui

import configparser

def getSettings(popDialog = False):
    
    def popDialogFct():
        form = SettingsDlg()
        if form.exec_() == QtGui.QDialog.Accepted:
            return getSettings()
        else:
            return None
    
    if popDialog:
        return popDialogFct()             
    
    try:
        return Settings()
    except FileNotFoundError:
        return popDialogFct()        
        

class Settings:
    def __init__(self):
        self.config = configparser.ConfigParser()
        with open('settings.ini') as configfile: # Raise an exception if file does not exist
            self.config.read('settings.ini')
            #self.config.read(configfile)

    def save(self):
        with open('settings.ini', 'w') as configfile:
          self.config.write(configfile)


class SettingsDlg(QtGui.QDialog):

    def __init__(self, settings = None, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setWindowTitle("Annotation corpus settings")
        self.setGeometry(100, 300, 1000, 200)

        self.settings = settings

        # Creating widgets with initial values
        self.gitProtocol = QtGui.QComboBox(self)
        protocols = ["http", "git+ssh"]
        self.gitProtocol.addItems(protocols)
        if self.settings is None:
            self.gitProtocol.setCurrentIndex(0)
            self.gitRemoteTxt     = QtGui.QLineEdit('github.com/christian-oreilly/corpus-thalamus.git', self)
            self.gitLocalTxt      = QtGui.QLineEdit('curator_DB', self)
            self.gitUserTxt       = QtGui.QLineEdit("git", self) #getpass.getuser(), self)
    
        else:
            if "protocol" in self.settings.config['GIT']:
                self.gitProtocol.setCurrentIndex(protocols.index(self.settings.config['GIT']['protocol']))
            else:
                self.gitProtocol.setCurrentIndex(0)
                
            self.gitRemoteTxt     = QtGui.QLineEdit(self.settings.config['GIT']['remote'], self)
            self.gitLocalTxt      = QtGui.QLineEdit(self.settings.config['GIT']['local'], self)
            self.gitUserTxt       = QtGui.QLineEdit(self.settings.config['GIT']['user'], self)


        self.okBtn            = QtGui.QPushButton('OK', self)

        # Signals
        self.okBtn.clicked.connect(self.writeConfig)

        # Layout
        layout = QtGui.QVBoxLayout()

        # GIT
        self.gitGroupBox = QtGui.QGroupBox("GIT")
        gridGIT = QtGui.QGridLayout(self.gitGroupBox)
        gridGIT.addWidget(QtGui.QLabel('Remove repository', self), 0, 0)
        gridGIT.addWidget(self.gitProtocol, 0, 1)
        gridGIT.addWidget(QtGui.QLabel('://', self), 0, 2)
        gridGIT.addWidget(self.gitUserTxt, 0, 3)
        gridGIT.addWidget(QtGui.QLabel('@', self), 0, 4)
        gridGIT.addWidget(self.gitRemoteTxt, 0, 5)
        gridGIT.addWidget(QtGui.QLabel('Local repository', self), 1, 0)
        gridGIT.addWidget(self.gitLocalTxt, 1, 1, 1, 5)

        layout.addWidget(self.gitGroupBox)
        layout.addWidget(self.okBtn)

        self.setLayout(layout)


        # Detect changes in git repository URL
        #self.gitProtocol.currentIndexChanged.connect(self.gitURLChanged)




    def writeConfig(self):
        config = configparser.ConfigParser()

        config['DEFAULT'] = {}

        config['GIT'] = {'protocol'        : self.gitProtocol.currentText(),
                         'remote'          : self.gitRemoteTxt.text(),
                         'local'           : self.gitLocalTxt.text(),
                         'user'            : self.gitUserTxt.text()}


        if self.settings is None:
            config['WINDOW'] = {}
        elif "WINDOW" in self.settings.config: 
            config['WINDOW'] = self.settings.config["WINDOW"]
        else:
            config['WINDOW'] = {}

        with open('settings.ini', 'w') as configfile:
          config.write(configfile)

        self.accept() 

