import sys
import numpy as np
import pyqtgraph as pgt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QFileDialog, QMainWindow, QWidget, QPushButton, QComboBox, QMessageBox
from PyQt5.QtSerialPort import QSerialPort
import csv


#define buffer - using circular approach
class CircularBuffer:
    # constructor for circular buffer
    def __init__(self, max_size):
        self.max_size = max_size
        self.buffer = np.zeros(max_size)
        self.index = 0
        self.full = False

    # get function for fetching data from the buffer
    def get_data(self):
        if self.full:
            return np.concatenate((self.buffer[self.index:], self.buffer[:self.index]))
        else:
            return self.buffer[:self.index]

    # push function for adding data to the buffer
    def push(self, value):
        self.buffer[self.index] = value                                                             # assigns pushed value to the current index element in the numpy list
        self.index = (self.index + 1) % self.max_size                                               # increment index and checks if buffer was filled 
        if self.index == 0:
            self.full = True   

class SerialDynamicPlotter(QMainWindow):
    def __init__(self):
        super().__init__()                                                                          # inherit from superclass (QMainWindow)

        # initialize variables
        self.sensor_data = {}                                                                       # dictionary for storing the data


        # define GUI window dimentions characteristics
        self.setWindowTitle("Serial Dynamic Viewer")
        self.setGeometry(100, 100, 1024, 768)

        # define plot widget characteristics
        self.plot_widget = pgt.PlotWidget()
        self.plot_widget.setBackground("#000000")
        self.plot_widget.setLabel("left", "Value")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(True, True)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.setClipToView(True)

        # build the viewer widgets
        plot_widget_layout = QVBoxLayout()


if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication

    viewer_window = SerialDynamicPlotter()
    viewer_window.add_sensor("P", "r")

    if viewer_window.serial_port.open(QSerialPort.ReadOnly):
        viewer_window.show()
        sys.exit(application.exec_())


