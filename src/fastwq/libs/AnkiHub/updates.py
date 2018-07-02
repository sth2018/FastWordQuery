# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'updates.ui'
#
# Created: Sat Sep 10 10:16:01 2016
#      by: PyQt4 UI code generator 4.11.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_DialogUpdates(object):
    def setupUi(self, DialogUpdates):
        DialogUpdates.setObjectName(_fromUtf8("DialogUpdates"))
        DialogUpdates.resize(500, 400)
        self.verticalLayout = QtGui.QVBoxLayout(DialogUpdates)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.labelUpdates = QtGui.QLabel(DialogUpdates)
        self.labelUpdates.setWordWrap(True)
        self.labelUpdates.setOpenExternalLinks(True)
        self.labelUpdates.setObjectName(_fromUtf8("labelUpdates"))
        self.verticalLayout.addWidget(self.labelUpdates)
        self.textBrowser = QtGui.QTextBrowser(DialogUpdates)
        self.textBrowser.setObjectName(_fromUtf8("textBrowser"))
        self.verticalLayout.addWidget(self.textBrowser)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.always = QtGui.QPushButton(DialogUpdates)
        self.always.setObjectName(_fromUtf8("always"))
        self.horizontalLayout.addWidget(self.always)
        self.update = QtGui.QPushButton(DialogUpdates)
        self.update.setObjectName(_fromUtf8("update"))
        self.horizontalLayout.addWidget(self.update)
        self.dont = QtGui.QPushButton(DialogUpdates)
        self.dont.setObjectName(_fromUtf8("dont"))
        self.horizontalLayout.addWidget(self.dont)
        self.never = QtGui.QPushButton(DialogUpdates)
        self.never.setObjectName(_fromUtf8("never"))
        self.horizontalLayout.addWidget(self.never)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(DialogUpdates)
        QtCore.QMetaObject.connectSlotsByName(DialogUpdates)

    def retranslateUi(self, DialogUpdates):
        DialogUpdates.setWindowTitle(_translate("DialogUpdates", "Update Checker", None))
        self.labelUpdates.setText(_translate("DialogUpdates", "<html><head/><body><p>A new version of {0} is available for download! </p><p>Do you want to update {1}to version {2}?</p><p>Changes from your version are listed below:</p></body></html>", None))
        self.always.setText(_translate("DialogUpdates", "Always update", None))
        self.update.setText(_translate("DialogUpdates", "Update", None))
        self.dont.setText(_translate("DialogUpdates", "Don\'t update", None))
        self.never.setText(_translate("DialogUpdates", "Never", None))

