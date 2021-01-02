#!/usr/bin/env python3

"""
Coffee Life Test Fixture Application

Vikram Seshadri
December 4, 2020

"""
import os
import sys
import GUI
import serial
import logging
import time
import datetime

# GUI
from PyQt5 import QtWidgets, QtCore, QtGui, uic
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import *

# email
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import socket

# flags
unit_fan_flag = 0  # unit fans off
vessel_fan_flag = 0  # vessel fans off
vessel_drain_flag = 0  # vessel drain pump off
arduino_connect_flag = 0  # Arduino disconnected
unit_connect_flag = 0  # Unit disconnected
scale_connect_flag = 0  # Scale disconnected

# Styling
aux_button = (
    "background-color: transparent;"
    "height: 60px;"
    "border: 1px solid darkgray;"
    "font: bold;"
    "padding: 0px;"
    "font-size: 25px;"
)

connect_button = (
    "background-color: #1ED760;"
    "color:#ffffff;"
    "height: 30px;"
)

disconnect_button = (
    "background-color: #F44336;"
    "height: 30px;"
)

start_stop_exit_button = (
    "background-color: transparent;"
    "height: 60px;"
    "width: 20px;"
    "border: 0px solid darkgray;"
    "margin: 5px 5px 5px 5px;"
    "padding:-15px;"
)


class ArduinoComm:
    # Commands - Output
    RESERVOIR_PUMP_ON = "A"
    RESERVOIR_PUMP_OFF = "B"
    VESSEL_PUMP_ON = "C"
    VESSEL_PUMP_OFF = "D"
    UNIT_FANS_ON = "E"
    UNIT_FANS_OFF = "F"
    VESSEL_FANS_ON = "G"
    VESSEL_FANS_OFF = "H"

    FLOAT_SWITCH_INFO = "J"
    READ_CURRENT = "K"
    READ_AMBIENT = "L"
    READ_VESSEL_RTD = "M"
    READ_RTDS = "N"
    READ_PRESSURE = "O"
    PRINT_DATA = "P"
    PRINT_DATA_OFF = "Q"
    REFILL_RESERVOIR = "R"
    MAINTAIN_RESERVOIR = "S"
    MAINTAIN_RESERVOIR_OFF = "T"
    STOP_ALL = "X"


# Aux functions - Unit and vessel cooling fans, Vessel Drain pump
class AuxFunctions:
    def vessel_fan_toggle(self):
        global vessel_fan_flag
        try:
            if vessel_fan_flag == 0:
                logging.info('Vessel fans are on')
                vessel_fan_flag = 1
            else:
                logging.info('Vessel fans are off')
                vessel_fan_flag = 0

        except Exception:
            logging.exception("Exception occurred", exc_info=True)

    def unit_fan_toggle(self):
        global unit_fan_flag
        try:
            if unit_fan_flag == 0:
                logging.info('Unit fans are on')
                unit_fan_flag = 1
            else:
                logging.info('Unit fans are off')
                unit_fan_flag = 0

        except Exception:
            logging.exception("Exception occurred", exc_info=True)

    def vessel_drain_toggle(self):
        global vessel_drain_flag
        try:
            if vessel_drain_flag == 0:
                logging.info('Vessel Draining')
                vessel_drain_flag = 1
            else:
                logging.info('Vessel stopped draining')
                vessel_drain_flag = 0

        except Exception:
            logging.exception("Exception occurred", exc_info=True)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        self.threadpool = QtCore.QThreadPool()
        self.do_init = QtCore.QEvent.registerEventType()
        QtWidgets.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()

        dir_path = os.path.dirname(os.path.realpath(__file__))

        self.ui = uic.loadUi(dir_path + "\GUI.ui", self)

        # Quit button and shortcut
        quit_action = QtWidgets.QAction('Quit', self)
        quit_action.setShortcuts(['Ctrl+Q', 'Ctrl+W'])
        quit_action.triggered.connect(QtWidgets.qApp.closeAllWindows)
        self.addAction(quit_action)
        self.ui.PB_Quit.clicked.connect(QtWidgets.qApp.closeAllWindows)

        self.ui.PB_UnitFans.setStyleSheet(aux_button)
        self.ui.PB_VesselFans.setStyleSheet(aux_button)
        self.ui.PB_VesselDrain.setStyleSheet(aux_button)
        self.ui.PB_ReservoirDrain.setStyleSheet(aux_button)
        self.ui.PB_Arduino_Connect.setStyleSheet(connect_button)
        self.ui.PB_Unit_Connect.setStyleSheet(connect_button)
        self.ui.PB_Scale_Connect.setStyleSheet(connect_button)
        self.ui.PB_Start_Stop.setStyleSheet(start_stop_exit_button)
        self.ui.PB_Quit.setStyleSheet(start_stop_exit_button)

        # Aux functions
        self.ui.PB_VesselFans.clicked.connect(AuxFunctions.vessel_fan_toggle)
        self.ui.PB_UnitFans.clicked.connect(AuxFunctions.unit_fan_toggle)
        self.ui.PB_VesselDrain.clicked.connect(AuxFunctions.vessel_drain_toggle)

        # Serial connections
        self.ui.PB_Arduino_Connect.clicked.connect(self.arduino_connect)
        self.ui.PB_Unit_Connect.clicked.connect(self.unit_connect)
        self.ui.PB_Scale_Connect.clicked.connect(self.scale_connect)

    # Serial connections
    def arduino_connect(self):
        global arduino_connect_flag
        try:
            if arduino_connect_flag == 0:
                self.ui.PB_Arduino_Connect.setText("Disconnect")
                self.ui.PB_Arduino_Connect.setStyleSheet(disconnect_button)
                logging.info('Arduino Connected')
                arduino_connect_flag = 1
                self.ui.GB_Aux.setEnabled(True)
                self.ui.PB_ReservoirDrain.setEnabled(False)

            else:
                self.ui.PB_Arduino_Connect.setText("Connect")
                self.ui.PB_Arduino_Connect.setStyleSheet(connect_button)
                logging.info('Arduino Disconnected')
                arduino_connect_flag = 0
                self.ui.GB_Aux.setEnabled(False)

        except Exception:
            logging.exception("Exception occurred", exc_info=True)

    def unit_connect(self):
        global unit_connect_flag
        try:
            # Current SKU selection
            selected_SKU = self.ui.CB_SKU.currentText()
            if selected_SKU == "CFPxxx":
                if unit_connect_flag == 0:
                    self.ui.PB_Unit_Connect.setStyleSheet(disconnect_button)
                    self.ui.PB_Unit_Connect.setText("Disconnect")
                    logging.info(selected_SKU + ' Connected')
                    unit_connect_flag = 1
                    self.ui.PB_ReservoirDrain.setEnabled(True)
                    self.ui.PB_Start_Stop.setEnabled(True)
                    self.ui.GB_TestParam.setEnabled(True)

                else:
                    self.ui.PB_Unit_Connect.setStyleSheet(connect_button)
                    self.ui.PB_Unit_Connect.setText("Connect")
                    logging.info(selected_SKU + ' Disconnected')
                    unit_connect_flag = 0
                    self.ui.PB_ReservoirDrain.setEnabled(False)
                    self.ui.PB_Start_Stop.setEnabled(False)
                    self.ui.GB_TestParam.setEnabled(False)

        except Exception:
            logging.exception("Exception occurred", exc_info=True)

    def scale_connect(self):
        global scale_connect_flag
        try:
            if scale_connect_flag == 0:
                self.ui.PB_Scale_Connect.setStyleSheet(disconnect_button)
                self.ui.PB_Scale_Connect.setText("Disconnect")
                logging.info('Scale Connected')
                scale_connect_flag = 1

            else:
                self.ui.PB_Scale_Connect.setStyleSheet(connect_button)
                self.ui.PB_Scale_Connect.setText("Connect")
                logging.info('Scale Disconnected')
                scale_connect_flag = 0

        except Exception:
            logging.exception("Exception occurred", exc_info=True)


if __name__ == "__main__":

    if sys.flags.interactive != 1:

        dirpath = os.path.dirname(__file__)  # Current directory
        data_dir = dirpath + r'\RAW'  # RAW data folder
        log_dir = dirpath + r'\Logs'  # Log files folder

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Logging
        log_file = log_dir + "\CFP" + str(time.strftime("-%m-%d-%Y--%I-%M-%S %p")) + ".log"
        logging.basicConfig(filename=log_file, filemode='w', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        logging.getLogger().addHandler(logging.StreamHandler())

        app = QtWidgets.QApplication(sys.argv)
        app.processEvents()
        program = MainWindow()

        # Stylesheet
        file = open(dirpath + r'\style\style.qss')
        with file:
            qss = file.read()
            app.setStyleSheet(qss)

        program.setMinimumSize(810, 850)
        program.show()
        app.exec_()
