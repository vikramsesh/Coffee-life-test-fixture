#!/usr/bin/env python3

"""
Coffee Life Test Fixture Application

Vikram Seshadri
December 4, 2020

"""
import os
import sys
import serial
import logging
import time
import datetime
import re
import csv

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

# GUI defaults
station = 1
unit = 1
mode = " "
size = " "
style = " "
macro = 0
start_cycle = 1
current_cycle = start_cycle  # current cycle number. Will increment with each brew
number_of_cycles = 2000
auto_shutoff_temp = 150  # in degC
boiler_cool_temp = 35  # in degC
vessel_cool_temp = 35  # in degC
cool_time = 5  # in minutes
max_brew_time = 10  # in minutes
filename_extra = " "
receiver_email = []

# file manager
file_dir = ' '
subfile_dir = ' '
filename = ' '
data_dir = ' '
summary_file = ' '

raw_data = ' '
summary_data = ' '

SKU_list = ['CFP300', 'CM400', 'CP300']
Build_list = ['P0', 'P1', 'P2', 'P3', 'P4', 'EB0', 'EB1', 'EB2', 'MP']
Mode_list = ['Coffee', 'K-Cup', 'Hot Water', 'Clean', 'Tea']
Style_list = ['Classic', 'Rich', 'Over Ice', 'Specialty', 'Hot', 'Very Hot', 'Herbal', 'Black', 'Oolong', 'White',
              'Green']
Size_list = ['Cup', 'Cup XL', 'Travel', 'Travel XL', '1/2 Carafe', '3/4 carafe', 'Full Carafe', '6oz', '8oz', '10z',
             '12oz']

# defaults
brew_weight = 0  # in g

# Serial ports
arduino_ser = " "
scale_ser = " "
unit_ser = " "

test_param = "Station: {}, Unit: {}, Mode: {}, Size: {}, Style: {}, Macro: {}, Start Cycle: {}, " \
             "Current Cycle: {}, Number of cycles: {}, Auto shutoff temp.: {}C, Boiler Cool temp.: {}C, " \
             "Vessel Cool temp: {}C, Cool time: {}min., Max Brew time: {}min, Filename Extra: {}" \
    .format(station, unit, mode, size, style, macro, start_cycle, current_cycle, number_of_cycles,
            auto_shutoff_temp, boiler_cool_temp, vessel_cool_temp, cool_time, max_brew_time, filename_extra)

# flags
unit_fan_flag = 0  # unit fans off
vessel_fan_flag = 0  # vessel fans off
vessel_drain_flag = 0  # vessel drain pump off
arduino_connect_flag = 0  # Arduino disconnected
unit_connect_flag = 0  # Unit disconnected
scale_connect_flag = 0  # Scale disconnected
start_stop_flag = 0  # Stopped


# Styling
class Styling:
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


# Arduino communication
class ArduinoComm(object):
    # Commands - Output
    RESERVOIR_PUMP_ON = "A"
    RESERVOIR_PUMP_OFF = "B"
    VESSEL_PUMP_ON = "C"
    VESSEL_PUMP_OFF = "D"
    UNIT_FANS_ON = "E"
    UNIT_FANS_OFF = "F"
    VESSEL_FANS_ON = "G"
    VESSEL_FANS_OFF = "H"
    STOP_ALL = "X"

    def __init__(self):
        self.threadpool = QtCore.QThreadPool()
        self.do_init = QtCore.QEvent.registerEventType()

    def pre_brew(self):
        # This function checks for all water float status (Reservoir, Vessel and Drain drum), power and scale weight
        try:
            # arduino_ser.open()
            # scale_ser.open()

            t_end = time.time() + 5  # 30 seconds

            while time.time() < t_end:
                # arduino_read_serial = arduino_ser.readline()
                # scale_read_serial = scale_ser.readline()
                # print(read_serial)
                print(time.time())
            logging.info("Pre-brew process has begun")

        except Exception as e:
            logging.exception("Exception occurred", exc_info=True)
            email_Send(e)

    def send_command(self):
        arduino_ser.write(STOP_ALL)


# Aux functions - Unit and vessel cooling fans, Vessel Drain pump
class AuxFunctions:
    global scale_ser, brew_weight

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

    def scale_data(self):
        scale_output = scale_ser.readline()
        scale_output.strip()
        y = scale_output.decode("utf-8", "replace")
        scale_pattern = r"([\w]+)(,)([\+|-])([\d\.]+)(\s+)([\w]+)"

        match = re.match(scale_pattern, y)

        if match is not None:
            # print(match.group(3) + match.group(4))
            brew_weight = match.group(3) + match.group(4)
            print(brew_weight)


# CFP communication
class CFPComm:
    RESERVOIR_PUMP_ON = "A"


# GUI
class MainWindow(QtWidgets.QMainWindow):
    global station, unit, mode, size, style, macro, start_cycle, current_cycle, number_of_cycles, \
        auto_shutoff_temp, boiler_cool_temp, vessel_cool_temp, cool_time, max_brew_time, filename_extra, \
        test_param, receiver_email, file_dir, data_dir, subfile_dir, filename, summary_file

    def __init__(self):

        self.threadpool = QtCore.QThreadPool()
        self.do_init = QtCore.QEvent.registerEventType()
        QtWidgets.QMainWindow.__init__(self)
        super(MainWindow, self).__init__()

        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.ui = uic.loadUi(dir_path + "\GUI.ui", self)
        self.test_param_import()

        # update comboBox
        self.ui.CB_SKU.currentIndexChanged.connect(self.update_mode_combo)
        self.ui.CB_Mode.currentIndexChanged.connect(self.update_size_combo)
        self.ui.CB_Size.currentIndexChanged.connect(self.update_style_combo)
        self.ui.CB_Style.currentIndexChanged.connect(self.update_kcup_size_combo)

        # adds initial Text into SKU combobox
        self.ui.CB_SKU.clear()
        self.ui.CB_SKU.addItems(SKU_list)
        self.ui.CB_Build.clear()
        self.ui.CB_Build.addItems(Build_list)

        self.ui.DSB_Station.valueChanged.connect(self.file_manager)

        # Quit button and shortcut
        quit_action = QtWidgets.QAction('Quit', self)
        quit_action.setShortcuts(['Ctrl+Q', 'Ctrl+W'])
        quit_action.triggered.connect(QtWidgets.qApp.closeAllWindows)
        self.addAction(quit_action)
        self.ui.PB_Quit.clicked.connect(self.quit)

        # Push button styling
        self.ui.PB_UnitFans.setStyleSheet(Styling.aux_button)
        self.ui.PB_VesselFans.setStyleSheet(Styling.aux_button)
        self.ui.PB_VesselDrain.setStyleSheet(Styling.aux_button)
        self.ui.PB_ReservoirDrain.setStyleSheet(Styling.aux_button)
        self.ui.PB_Arduino_Connect.setStyleSheet(Styling.connect_button)
        self.ui.PB_Unit_Connect.setStyleSheet(Styling.connect_button)
        self.ui.PB_Scale_Connect.setStyleSheet(Styling.connect_button)
        self.ui.PB_Start_Stop.setStyleSheet(Styling.start_stop_exit_button)
        self.ui.PB_Quit.setStyleSheet(Styling.start_stop_exit_button)

        # Aux functions
        self.ui.PB_VesselFans.clicked.connect(AuxFunctions.vessel_fan_toggle)
        self.ui.PB_UnitFans.clicked.connect(AuxFunctions.unit_fan_toggle)
        self.ui.PB_VesselDrain.clicked.connect(AuxFunctions.vessel_drain_toggle)

        # Serial connections
        self.ui.PB_Arduino_Connect.clicked.connect(self.arduino_connect)
        self.ui.PB_Unit_Connect.clicked.connect(self.unit_connect)
        self.ui.PB_Scale_Connect.clicked.connect(self.scale_connect)

        # Start and Stop buttons
        self.ui.PB_Start_Stop.setEnabled(True)
        self.ui.PB_Start_Stop.clicked.connect(self.start_end_brew)

        icon = QtGui.QIcon()
        icon2 = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon/connect.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("icon/disconnect.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        icon.addPixmap(QtGui.QPixmap("icon/connect.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
        icon2.addPixmap(QtGui.QPixmap("icon/disconnect.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)

    def update_mode_combo(self):
        self.ui.CB_Mode.clear()
        if self.ui.CB_SKU.currentText() == 'CFP300':  # CFP300
            self.ui.CB_Mode.addItems(['Coffee', 'K-Cup', 'Hot Water', 'Clean'])
        elif self.ui.CB_SKU.currentText() == "CM400":  # CM400
            self.ui.CB_Mode.addItems(['Coffee', 'Clean'])
        elif self.ui.CB_SKU.currentText() == "CP300":  # CP300
            self.ui.CB_Mode.addItems(['Coffee', 'Tea', 'Clean'])

    def update_size_combo(self):
        self.ui.CB_Size.clear()

        if self.ui.CB_Mode.currentText() == 'Coffee':
            if self.ui.CB_SKU.currentText() == 'CFP300':
                self.ui.CB_Size.addItems(
                    ['Cup', 'Cup XL', 'Travel', 'Travel XL', '1/2 Carafe', '3/4 Carafe', 'Full Carafe'])
            elif self.ui.CB_SKU.currentText() == 'CM400' or 'CP300':
                self.ui.CB_Size.addItems(['Cup', 'CupXL', 'Travel', 'Travel XL', '1/2 Carafe', 'Full Carafe'])

        elif self.ui.CB_Mode.currentText() == 'Tea':
            self.ui.CB_Size.addItems(['Cup', 'CupXL', 'Travel', 'Travel XL', '1/2 Carafe', 'Full Carafe'])

        elif self.ui.CB_Mode.currentText() == 'K-Cup':
            self.ui.CB_Size.addItems(['6oz', '8oz', '10oz', '12oz'])

        elif self.ui.CB_Mode.currentText() == 'Hot Water':
            self.ui.CB_Size.addItems(
                ['Cup', 'Cup XL', 'Travel', 'Travel XL', '1/2 Carafe', '3/4 Carafe', 'Full Carafe'])

        elif self.ui.CB_Mode.currentText() == 'Clean':
            self.ui.CB_Size.addItem('Full Carafe')

    def update_kcup_size_combo(self):
        if self.ui.CB_Mode.currentText() == 'K-Cup':

            if self.ui.CB_Style.currentText() == 'Classic' or 'Over Ice':
                self.ui.CB_Size.addItems(['6oz', '8oz', '10oz', '12oz'])
            elif self.ui.CB_Style.currentText() == 'Rich':
                self.ui.CB_Size.addItems(['5oz', '7oz', '9oz', '11oz'])
            elif self.ui.CB_Style.currentText() == 'Specialty':
                self.ui.CB_Size.addItem('4oz')

    def update_style_combo(self):
        self.ui.CB_Style.clear()

        # CFP300
        if self.ui.CB_SKU.currentText() == 'CFP300':
            # Coffee
            if self.ui.CB_Mode.currentText() == 'Coffee':
                if self.ui.CB_Size.currentText() == 'Cup':
                    self.ui.CB_Style.addItems(['Classic', 'Rich', 'Over Ice', 'Specialty'])
                else:
                    self.ui.CB_Style.addItems(['Classic', 'Rich', 'Over Ice'])

            # K-Cup
            elif self.ui.CB_Mode.currentText() == 'K-Cup':
                self.ui.CB_Style.addItems(['Classic', 'Rich', 'Over Ice', 'Specialty'])

            # Hot Water
            elif self.ui.CB_Mode.currentText() == 'Hot Water':
                self.ui.CB_Style.addItems(Style_list[4:6])

        # CM400
        if self.ui.CB_SKU.currentText() == 'CM400':
            # Coffee
            if self.ui.CB_Mode.currentText() == 'Coffee':
                if self.ui.CB_Size.currentText() == Size_list[0]:
                    self.ui.CB_Style.addItems(Style_list[0:4])

                else:
                    self.ui.CB_Style.addItems(Style_list[0:3])

        if self.ui.CB_SKU.currentText() == 'CP300':
            # Coffee
            if self.ui.CB_Mode.currentText() == 'Coffee':
                if self.ui.CB_Size.currentText() == Size_list[0]:
                    self.ui.CB_Style.addItems(Style_list[0:4])

                else:
                    self.ui.CB_Style.addItems(Style_list[0:3])

            # Tea
            if self.ui.CB_Mode.currentText() == 'Tea':
                self.ui.CB_Style.addItems(Style_list[6:11])

        # Clean
        if self.ui.CB_Mode.currentText() == 'Clean':
            self.ui.CB_Style.clear()

    # Serial connections
    def arduino_connect(self):
        global arduino_connect_flag, arduino_ser

        if arduino_connect_flag == 0:
            try:
                # serial communication between Pi and Arduino
                # arduino_ser = serial.Serial(self.ui.LE_Arduino_Port.text(), 9600)
                # arduino_ser.open()
                # read_serial = arduino_ser.readline()
                # print(read_serial)
                logging.info('Arduino Connected: Port ' + self.ui.LE_Arduino_Port.text())
                self.ui.PB_Arduino_Connect.setText("Disconnect")
                self.ui.PB_Arduino_Connect.setStyleSheet(Styling.disconnect_button)
                arduino_connect_flag = 1
                self.ui.GB_Aux.setEnabled(True)
                self.ui.PB_ReservoirDrain.setEnabled(False)

            except Exception as e:
                self.ui.PB_Arduino_Connect.setCheckable(False)
                QMessageBox.critical(self, "Error", str(e))
                logging.exception("Exception occurred", exc_info=True)
                email_Send(e)

        else:
            try:
                logging.info('Arduino Disconnected: Port ' + self.ui.LE_Arduino_Port.text())
                self.ui.PB_Arduino_Connect.setText("Connect")
                self.ui.PB_Arduino_Connect.setStyleSheet(Styling.connect_button)
                arduino_connect_flag = 0
                self.ui.GB_Aux.setEnabled(False)
                # arduino_ser.close()

            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
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
            QMessageBox.critical(self, "Error", str(e))

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
            QMessageBox.critical(self, "Error", str(e))

    # File directory and Filename creation
    def file_manager(self):
        # SKU and station info
        global filename_extra, summary_file, filename
        file_dir = data_dir + '\\' + "{} {} Station {}".format(self.ui.CB_SKU.currentText(),
                                                               self.ui.CB_Build.currentText(),
                                                               str(int((self.ui.DSB_Station.value()))))

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        # Macro and Unit info
        subfile_dir = file_dir + '\\' + "#{} Macro {}".format(str(int((self.ui.DSB_Unit.value()))), str(
            int((self.ui.DSB_Macro.value()))))

        if not os.path.exists(subfile_dir):
            os.makedirs(subfile_dir)

        # Remove characters that don't follow file naming convention
        # *Do not use the following characters: /  \: * ? " < > |
        filename_extra = re.sub(r"([^\w])", "_", filename_extra)

        # summary file name
        summary_file = file_dir + '\\' + "{}_{}_Station{}_Unit{}_{}.csv".format(self.ui.CB_SKU.currentText(),
                                                                                self.ui.CB_Build.currentText(), station,
                                                                                unit, filename_extra)
        # data file name
        filename = subfile_dir + '\\' + "{}_{}_{}_Brew{}_{}.csv".format(self.ui.CB_Mode.currentText(),
                                                                        self.ui.CB_Size.currentText(),
                                                                        self.ui.CB_Style.currentText(),
                                                                        current_cycle, filename_extra)

        print('Data directory: {}'.format(data_dir))
        print('File directory: {}'.format(file_dir))
        print('Sub File directory: {}'.format(subfile_dir))
        print('Filename: {}'.format(filename))
        print('Summary Filename: {}'.format(summary_file))
        a = DataLogging()
        b = DataLogging()

        b.summary_file_log("Hello")
        b.raw_file_log("Hello")

    # Data Import - Get's the initial values from the Test parameters in the GUI
    def test_param_import(self):
        station = self.ui.DSB_Station.value()
        unit = self.ui.DSB_Unit.value()
        mode = self.ui.CB_Mode.currentText()
        size = self.ui.CB_Size.currentText()
        style = self.ui.CB_Style.currentText()
        macro = self.ui.DSB_Macro.value()
        start_cycle = self.ui.DSB_StartCycle.value()
        number_of_cycles = self.ui.DSB_CycleCount.value()
        auto_shutoff_temp = self.ui.DSB_AutoshutoffTemp.value()
        boiler_cool_temp = self.ui.DSB_BoilerTemp.value()
        vessel_cool_temp = self.ui.DSB_VesselTemp.value()
        cool_time = self.ui.DSB_CoolTime.value()
        max_brew_time = self.ui.DSB_MaxBrewTime.value()
        filename_extra = self.ui.LE_Filename.text()
        receiver_email = self.ui.LE_Email.text().split(",")

        test_param = "SKU: {},Build:{},Station:{}, Unit:{}, Mode:{}, Size:{}, Style:{}, Macro:{}, Start Cycle:{}," \
                     "Current Cycle:{}, Number of cycles:{}, Auto shutoff temp.:{}C, Boiler Cool temp.:{}C, " \
                     "Vessel Cool temp:{}C, Cool time:{}min., Max Brew time:{}min., Filename Extra:{}" \
            .format(self.ui.CB_SKU.currentText(), self.ui.CB_Build.currentText(), station, unit, mode, size, style,
                    macro, start_cycle, current_cycle, number_of_cycles, auto_shutoff_temp, boiler_cool_temp,
                    vessel_cool_temp, cool_time, max_brew_time, filename_extra)

        logging.info(test_param)

    def start_end_brew(self):
        global start_stop_flag

        if start_stop_flag == 0:
            self.ui.GB_Serial.setEnabled(False)
            self.ui.GB_TestParam.setEnabled(False)
            self.ui.GB_Aux.setEnabled(False)
            self.ui.GB_Misc.setEnabled(False)
            a = ArduinoComm()
            a.pre_brew()

            logging.info('Brew {} Started'.format(current_cycle))
            start_stop_flag = 1

        else:
            logging.info('Brew {} Ended'.format(current_cycle))
            self.ui.GB_Serial.setEnabled(True)
            self.ui.GB_TestParam.setEnabled(True)
            self.ui.GB_Aux.setEnabled(True)
            self.ui.GB_Misc.setEnabled(True)
            start_stop_flag = 0

    def quit(self):
        logging.info('Application closed')
        # Stop everything
        QtWidgets.qApp.closeAllWindows()


# Data logging
class DataLogging(object):
    def raw_file_log(self, data):
        global filename, filename_extra
        try:
            print(filename)
            # data = data.split(',')
            if os.path.exists(filename):
                with open(filename, 'a', newline='') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    filewriter.writerow(data)

            else:
                # Create and append
                with open(filename, 'w', newline='') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    filewriter.writerow(['Time', 'Boiler temp.', 'Outlet temp.', 'PTC temp.', 'Flow rate', '1 cup temp',
                                         '3 cup temp', '5 cup temp', '7 cup temp', 'Brew weight', 'Error code'])
                    filewriter.writerow(data)

        except Exception as e:
            logging.exception("Exception occurred", exc_info=True)

    def summary_file_log(self, data):
        global summary_file, filename_extra
        try:
            print(summary_file)
            # data = data.split(',')
            if os.path.exists(summary_file):
                with open(summary_file, 'a', newline='') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    filewriter.writerow(data)

            else:
                # Create and append
                with open(summary_file, 'w', newline='') as csvfile:
                    filewriter = csv.writer(csvfile, delimiter=',',
                                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    filewriter.writerow(
                        ['Brew Start time', 'Brew end time', 'Mode', 'Size', 'Style', 'Macro', 'Brew cycle',
                         'Max. Boiler temp (degC)', 'Max. Outlet temp (degC)', 'Initial weight (g)', 'Final weight (g)',
                         'Brew Volume (g)', 'Brew Volume (oz.)', 'Max. Ambient temperature (degC)',
                         'Max. Ambient humidity'])
                    filewriter.writerow(data)

        except Exception as e:
            logging.exception("Exception occurred", exc_info=True)


# Email
def email_Send(email_message):
    try:
        port = 465  # For SSL
        smtp_server = "smtp.gmail.com"
        sender_email = "sninja.test@gmail.com"
        password = '$#!N*&!0'

        message = email_message
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            for i in range(0, len(receiver_email)):
                server.sendmail(sender_email, receiver_email[i], message)
                print(receiver_email[i])
    except KeyboardInterrupt:
        print("1. Program Stopped - Keyboard Interrupt")
        sys.exit(1)

    except Exception as e:
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
        log_file = log_dir + "\log" + str(time.strftime("-%m-%d-%Y--%I-%M-%S %p")) + ".log"
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
