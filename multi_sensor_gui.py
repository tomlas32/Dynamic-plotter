import pyqtgraph as pgt
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QFileDialog, QMainWindow, QWidget, QPushButton, QComboBox, QMessageBox, QLabel, QLCDNumber, QLineEdit
from PyQt5.QtWidgets import QSizePolicy, QSpacerItem, QTextEdit, QAction
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtGui import QIcon
from buffer import CircularBuffer
import csv
import time
import database as db
from SerialMonitor import SerialPortMonitor
import sys
import os

class MultiSensorPlotter(QMainWindow):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.window_main = parent
        self.closed = pyqtSignal()

        icon = QIcon(self.resource_path("assets/sensor.ico"))
        self.setWindowIcon(icon)
        # initialize variables
        self.sensor_data = {}                                                                       # dictionary for storing the data
        self.com_port_names = []                                                                    # list for storing active COM ports
        self.data_records = {}                                                                      # list for storing sensor data for export
        self.buffer_size = 20000
        self.is_connected = False
        self.is_paused = False
        self.first_time_point = None

        ########## FIle menu #########
        self.menubar = self.menuBar() 
        self.file_menu = self.menubar.addMenu("File")
        self.settings_menu = self.menubar.addMenu("Settings")
        self.help_menu = self.menubar.addMenu("Help")
        
        # Connection submenu
        self.connect_action = QAction("Connect", self)
        self.connect_action.triggered.connect(self.toggle_connect)
        self.connect_action.setEnabled(False)
        self.disconnect_action = QAction("Disconnect", self)
        self.disconnect_action.setEnabled(False)
        self.disconnect_action
        self.clear_action = QAction("Clear", self)
        self.clear_action.triggered.connect(self.clear_data)
        self.clear_action.setEnabled(False)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        self.file_menu.addAction(self.connect_action)
        self.file_menu.addAction(self.disconnect_action)
        self.file_menu.addAction(self.clear_action)
        self.file_menu.addAction(exit_action)

        ########## define GUI window dimentions characteristics #########################
        self.setWindowTitle("Dynamic Temerature Viewer")
        self.setFixedSize(1024, 520)

        ########## define plot area widget characteristics ##############################
        self.plot_widget = pgt.PlotWidget()
        self.plot_widget.setBackground("#000000")
        self.plot_widget.setLabel("left", "Temperature (Celsius)")
        self.plot_widget.setLabel("bottom", "Time (s)")
        self.plot_widget.showGrid(True, True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.setClipToView(True)

        ########## build the viewer widgets #############################################
        self.main_layout = QHBoxLayout()                                                                 # main layout to store 2 VBoxes
        self.window = QWidget() 

        # left panel Widgets
        self.left_layout = QVBoxLayout()                                                                
        self.left_panel = QWidget()                                                                    
        self.left_panel.setLayout(self.left_layout)
        self.left_layout.addWidget(self.plot_widget)

        # right panel Widgets
        self.right_layout = QVBoxLayout()                                                                # layout for data entry
        self.right_panel = QWidget()
        self.right_panel.setLayout(self.right_layout)

        # initilize right panel layouts for storing widgets
        self.exp_layout = QHBoxLayout()
        self.sample_layout = QHBoxLayout()
        self.sensor_layout = QHBoxLayout()
        self.user_input_layout = QHBoxLayout()
        self.instrument_layout = QHBoxLayout()
        self.protocol_input_layout = QHBoxLayout()
        self.notes_layout = QHBoxLayout()
        self.buttons_layout = QHBoxLayout()
        self.LCD_layout = QVBoxLayout()
        self.LCD_sublayout1 = QHBoxLayout()
        self.LCD_sublayout2 = QHBoxLayout()
        self.LCD_sublayout3 = QHBoxLayout()
        self.COM_layout = QVBoxLayout()
        self.top_container = QVBoxLayout()
        self.top_container_widget = QWidget()
        self.top_container_widget.setLayout(self.top_container)

        spacer_1 = QSpacerItem(300, 10, QSizePolicy.Fixed, QSizePolicy.Fixed)
        # add to right panel layouts
        self.top_container.addLayout(self.LCD_layout)
        self.top_container.addSpacerItem(spacer_1)
        self.top_container.addLayout(self.user_input_layout)
        self.top_container.addLayout(self.exp_layout)
        self.top_container.addLayout(self.sensor_layout)
        self.top_container.addLayout(self.instrument_layout)
        self.top_container.addLayout(self.protocol_input_layout)
        self.top_container.addLayout(self.sample_layout)
        self.top_container.addLayout(self.notes_layout)
        self.top_container.addLayout(self.COM_layout)
        self.top_container.addLayout(self.buttons_layout)

        self.right_layout.addWidget(self.top_container_widget, alignment=Qt.AlignTop)

        # LCD widget and label
        self.LCD_label = QLabel("Current Sensor Value (deg C)")
        self.LCD_layout.addWidget(self.LCD_label)
        self.LCD_label_ch1 = QLabel("Ch1:")
        self.LCD_label_ch2 = QLabel("Ch2:")
        self.LCD_label_ch3 = QLabel("Ch3:")
        self.LCD_label_ch4 = QLabel("Ch4:")
        self.LCD_display1 = QLCDNumber()
        self.LCD_display1.setFixedHeight(24)
        self.LCD_display1.setFixedWidth(120)
        self.LCD_display1.setDigitCount(8)
        self.LCD_display2 = QLCDNumber()
        self.LCD_display2.setFixedHeight(24)
        self.LCD_display2.setFixedWidth(120)
        self.LCD_display2.setDigitCount(8)
        self.LCD_display3 = QLCDNumber()
        self.LCD_display3.setFixedHeight(24)
        self.LCD_display3.setFixedWidth(120)
        self.LCD_display3.setDigitCount(8)
        self.LCD_display4 = QLCDNumber()
        self.LCD_display4.setFixedHeight(24)
        self.LCD_display4.setFixedWidth(120)
        self.LCD_display4.setDigitCount(8)
        self.LCD_sublayout2.addWidget(self.LCD_label_ch1)
        self.LCD_sublayout2.addWidget(self.LCD_display1)
        self.LCD_sublayout2.addWidget(self.LCD_label_ch2)
        self.LCD_sublayout2.addWidget(self.LCD_display2)
        self.LCD_sublayout3.addWidget(self.LCD_label_ch3)
        self.LCD_sublayout3.addWidget(self.LCD_display3)
        self.LCD_sublayout3.addWidget(self.LCD_label_ch4)
        self.LCD_sublayout3.addWidget(self.LCD_display4)
        self.LCD_layout.addWidget(self.LCD_label)
        self.LCD_layout.addLayout(self.LCD_sublayout2)
        self.LCD_layout.addLayout(self.LCD_sublayout3)

        # user label and input field
        self.user_input_layout.addWidget(QLabel("User ID"))
        self.user_input = QLineEdit()
        self.user_input.setFixedWidth(200)
        self.user_input_layout.addWidget(self.user_input)
        self.user_input.textChanged.connect(self.check_condition)

        # experiment label and input field
        self.exp_layout.addWidget(QLabel("Experiment Name"))
        self.exp_input = QLineEdit()
        self.exp_input.setFixedWidth(200)
        self.exp_layout.addWidget(self.exp_input)
        self.exp_input.textChanged.connect(self.check_condition)

        # sensor label and input field
        self.sensor_layout.addWidget(QLabel("Sensor ID"))
        self.sensor_input = QLineEdit()
        self.sensor_input.setFixedWidth(200)
        self.sensor_layout.addWidget(self.sensor_input)
        self.sensor_input.textChanged.connect(self.check_condition)

        # instrument label and input field
        self.instrument_layout.addWidget(QLabel("Instrument ID"))
        self.instrument_input = QLineEdit()
        self.instrument_input.setFixedWidth(200)
        self.instrument_layout.addWidget(self.instrument_input)
        self.instrument_input.textChanged.connect(self.check_condition)

        # protocol label and input field
        self.protocol_input_layout.addWidget(QLabel("Protocol"))
        self.protocol_input = QLineEdit()
        self.protocol_input.setFixedWidth(200)
        self.protocol_input_layout.addWidget(self.protocol_input)

        # sample label and input field
        self.sample_layout.addWidget(QLabel("Cartridge"))
        self.sample_input = QLineEdit()
        self.sample_input.setFixedWidth(200)
        self.sample_layout.addWidget(self.sample_input)
        self.sample_input.textChanged.connect(self.check_condition)

        # notes label and input
        self.notes_layout.addWidget(QLabel("Notes"))
        self.notes_input = QTextEdit()
        self.notes_input.setFixedWidth(200)
        self.notes_input.setFixedHeight(100)
        self.notes_input.setLineWrapMode(QTextEdit.WidgetWidth)
        self.notes_layout.addWidget(self.notes_input)

        # created COM label and dropdown field and add to layout
        self.com_port_combo = QComboBox()
        self.COM_layout.addWidget(QLabel("Select COM Port"))
        self.COM_layout.addWidget(self.com_port_combo)

        # create connect and export buttons and add to layout
        self.connect_button = QPushButton("Connect")
        self.buttons_layout.addWidget(self.connect_button)
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(self.toggle_connect)

        self.export_button = QPushButton("Export")
        self.buttons_layout.addWidget(self.export_button)
        self.export_button.clicked.connect(self.export_helper)

        # add to main layout
        self.main_layout.addWidget(self.left_panel)                                                  
        self.main_layout.addWidget(self.right_panel) 

        # set main window layout
        self.window.setLayout(self.main_layout)
        self.setCentralWidget(self.window) 

        # create connect button for establishing serial communication
        self.status_label = QLabel("")                                                              # reporting on successful connection/disconnection
        self.left_layout.addWidget(self.status_label)

        # database entry confirmation message
        self.db_message = QLabel("")
        self.top_container.addWidget(self.db_message)

        # create a message box for clearing current data display
        self.clear_data_display = QMessageBox()
        self.clear_data_display.setWindowTitle("Choose Option")
        self.clear_data_display.setText("Would you like to reset the viewer and clear the data?")
        self.clear_data_display.setIcon(QMessageBox.Question)
        self.clear_data_display.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        # create instance of serial monitor
        self.serial_monitor = SerialPortMonitor()
        self.serial_monitor.port_changed.connect(self.update_com_port_combo)
        self.update_com_port_combo()
        
        # initialize and configure a QSerialPort object for serial communication
        self.serial_port = QSerialPort()
        self.serial_port.setBaudRate(115200)
        self.serial_port.readyRead.connect(self.receive_data)

        # initilise sensor
        self.add_sensor("Ch1", "r")
        self.add_sensor("Ch2", "g")
        self.add_sensor("Ch3", "b")
        self.add_sensor("Ch4", "y")
    
    # function for checking if all condition for establishing connection are met
    def check_condition(self):
        exp_name = self.exp_input.text()
        comport_index = self.com_port_combo.currentText()
        user_name = self.user_input.text()
        instrument_id = self.instrument_input.text()
        sensor_type = self.sensor_input.text()
        cartridge = self.sample_input.text()

        if all(len(x.strip()) > 0 for x in [cartridge, exp_name, comport_index, sensor_type, user_name, instrument_id]):
            self.connect_button.setEnabled(True)
            self.connect_action.setEnabled(True)
        else:
            self.connect_button.setEnabled(False)
            self.connect_action.setEnabled(False)

    def update_com_port_combo(self):
        current_port = self.com_port_combo.currentText()
        self.com_port_combo.clear()
        for port_name in self.serial_monitor.current_ports:
            self.com_port_combo.addItem(port_name)
        if current_port in self.serial_monitor.current_ports:
            self.com_port_combo.setCurrentText(current_port)  

    def add_sensor(self, name, color):
        self.sensor_data[name] = {
            'buffer': CircularBuffer(self.buffer_size),
            'plot_data': self.plot_widget.plot(pen=pgt.mkPen(color, width=2), name=name),
        }   

    def change_com_port(self):
        self.serial_port.setPortName(self.com_port_combo.currentText())

    # define toggle function for switching between connect and pause states
    def toggle_connect(self):
        if self.connect_button.text() == "Connect" or self.connect_button.text() == "Resume":
            port_name = self.com_port_combo.currentText()
            self.serial_port.setPortName(port_name)
            if not self.serial_port.isOpen():  # Check if the port is not already open
                if self.serial_port.open(QSerialPort.ReadOnly):
                    self.port_connect()
                    self.connect_button.setText("Pause")
                    self.status_label.setText("Connected to " + port_name)
                    self.connect_action.setEnabled(False)
                    self.update_clear_action_state()
                else:
                    self.status_label.setText("Failed to connect to COM port")
            else:
                self.status_label.setText("Port already open")
        else:
            self.port_pause()
            self.serial_port.close()  # Close the port when pausing
            self.connect_button.setText("Resume")

    # function for establishing serial communication 
    def port_connect(self):
        self.is_paused = False
        self.is_connected = True
        # if the pause button was clicked we are going to use the previously recorded time
        if hasattr(self, 'pause_time'):
            if self.data_records == {}:
                self.start_time = time.time()
            else:
                self.start_time += time.time() - self.pause_time 
            del self.pause_time   # Reset pause_time after resuming
        # Start from scratch if it's the first time connecting    
        else:  
            self.start_time = time.time()
    
    # function for pausing data stream and plotting
    def port_pause(self):
        self.is_paused = True
        self.is_connected = True
        # Record the time when the pause happens
        self.pause_time = time.time()

    def receive_data(self):
        self.serial_port.flush()
        while self.serial_port.canReadLine():
            try:
                values = [float(x) for x in self.serial_port.readLine().data().decode("utf-8", errors="ignore").strip().split(",")]
                formatted_values = ["{:.2f}".format(v) for v in values]
                if self.is_connected and not self.is_paused:
                    timestamp = format(float(time.time() - self.start_time), ".2f")
                    for channel, value in zip(["Ch1", "Ch2", "Ch3", "Ch4"], formatted_values):
                        buf = self.sensor_data[channel]['buffer']                                                                   # Get the buffer directly from self.sensor_data
                        plot = self.sensor_data[channel]['plot_data']
                        buf.push((timestamp, value))                                                                                # Update buffer

                        # down sample data for plotting
                        x_data, y_data = buf.get_data_for_plot()
                        downsampled_x = x_data[::4]
                        downsampled_y = y_data[::4]
                        #plot.setData(x_data, y_data)                                                                                # Update plot
                        plot.setData(x=downsampled_x, y=downsampled_y)
                        if channel not in self.data_records:
                            self.data_records[channel] = []
                        self.data_records[channel].append([timestamp, value])
                    
                self.LCD_display1.display(formatted_values[0])
                self.LCD_display2.display(formatted_values[1])
                self.LCD_display3.display(formatted_values[2])
                self.LCD_display4.display(formatted_values[3])
            except(UnicodeDecodeError, IndexError, ValueError):
                pass


    # define a helper function for exporting data and saving it into database
    def export_helper(self):
        if len(self.data_records) > 0:
            measurements = self.data_records
            experiment_name = self.exp_input.text()
            cartridge_number = self.sample_input.text()
            user_id = self.user_input.text()
            instrument_id = self.instrument_input.text()
            notes = self.notes_input.toPlainText()
            test_duration = measurements["Ch4"][-1][0]
            sensor_type = self.sensor_input.text()
            protocol = self.protocol_input.text()
            
            message = db.store_temp_measurements(user_id, sensor_type, experiment_name, instrument_id, protocol, cartridge_number, test_duration, measurements, notes)
            self.db_message.setText(message)
            self.export_data()
            reply = self.clear_data_display.exec_()
            if reply == QMessageBox.Yes:
                self.clear_data()
                self.update_clear_action_state()
            elif reply == QMessageBox.No:
                self.update_clear_action_state()
                QMessageBox.warning(self, "Current session", "Current session was not cleared. All data will be concatenated and submitted as a new entry. Rest plotter if you wish to avoid it.")
        else:
            QMessageBox.warning(self, "Export error", "No data to export.")


    def export_data(self):
        if len(self.data_records) > 0:
            filename, _ = QFileDialog.getSaveFileName(self, "Export Data", "", "CSV Files (*.csv)")
            if filename:
                try:
                    with open(filename, "w", newline="") as file:
                        writer = csv.writer(file)
                        channels = list(self.data_records.keys())             # Get all channel names
                        writer.writerow(["Time"] + channels)

                        for i in range(len(self.data_records[channels[0]])):  # Iterate over timestamps in any channel
                            timestamp = self.data_records[channels[0]][i][0]  # Extract timestamp directly
                            row = [timestamp]

                            for channel in channels:
                                value = self.data_records[channel][i][1]      # Extract value directly
                                row.append(value)                             # Append value for each channel for a given timestamp
                            writer.writerow(row)                             # Write the row data into csv (timestamp and 4 channels data) per each timestamp iteration
                    QMessageBox.information(self, "Success", "Data successfully exported to " + filename)
                except Exception as e:
                    QMessageBox.warning(self, "Error", "Failed to export data: " + str(e))
            else:
                QMessageBox.warning(self, "Export error", "Invalid file name.")
        else:
            QMessageBox.warning(self, "Export error", "No data to export.")
    
    # function for clearing data and viewer output
    def clear_data(self):
        self.data_records = {}
        for lcd in [self.LCD_display1, self.LCD_display2, self.LCD_display3, self.LCD_display4]:
            lcd.display(0)
        [self.plot_widget.removeItem(data["plot_data"]) for data in self.sensor_data.values()]
        for channel in self.sensor_data:
            self.sensor_data[channel]['buffer'] = CircularBuffer(self.buffer_size)
        
        self.add_sensor("Ch1", "r")
        self.add_sensor("Ch2", "g")
        self.add_sensor("Ch3", "b")
        self.add_sensor("Ch4", "y")
        self.start_time = time.time()
        self.connect_button.setText("Connect")
        self.status_label.setText("")
        self.update_clear_action_state()
        
    

    # overide closeEvent function
    def closeEvent(self, event):
        self.exit_application()

    # handles window closures (needed for dealing with hanging references)
    def exit_application(self):
        if hasattr(self.window_main, "temperature_window"):
            delattr(self.window_main, "temperature_window")
        self.window_main.temp_button.setEnabled(True)
        self.close() 

    # function for checking if data was collected
    def update_clear_action_state(self):
        if self.data_records or self.sensor_data: 
            self.clear_action.setEnabled(True)   
        else:
            self.clear_action.setEnabled(False) 
    
    def resource_path(self, relative_path):
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS2
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)
