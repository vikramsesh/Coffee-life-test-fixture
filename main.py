#!/usr/bin/env python3

"""
Coffee Life Test Fixture Application

Vikram Seshadri
December 4, 2020

"""
import os
import GUI

# GUI
from PyQt5 import QtWidgets, QtCore


# Toggle unit and vessel fan
class AuxFunctions:
    def fan_toggle(unitfantoggle, vesselfantoggle):
        print("Unit fan and vessel fan is off")
        if unitfantoggle is True:
            # Turn unit fan on
            print("Unit fan is on")

        if vesselfantoggle is True:
            # Turn vessel fan on
            print("Vessel fan is on")


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        self.threadpool = QtCore.QThreadPool()
        self.do_init = QtCore.QEvent.registerEventType()
        QtWidgets.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()
        self.ui = GUI.Ui_MainWindow().setupUi(self)

        # Quit button and shortcut
        quit_action = QtWidgets.QAction('Quit', self)
        quit_action.setShortcuts(['Ctrl+Q', 'Ctrl+W'])
        quit_action.triggered.connect(QtWidgets.qApp.closeAllWindows)
        self.addAction(quit_action)


if __name__ == "__main__":
    import sys

    if sys.flags.interactive != 1:
        app = QtWidgets.QApplication(sys.argv)
        app.processEvents()
        program = MainWindow()

        # Stylesheet
        __location__ = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__)))
        file = open(os.path.join(__location__, r'custom\style.qss'))
        with file:
            qss = file.read()
            app.setStyleSheet(qss)

        program.show()
        app.exec_()
