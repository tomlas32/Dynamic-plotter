import sys
from PyQt5.QtWidgets import QApplication
from gui_main import GuiMain

if __name__ == "__main__":
    application = QApplication(sys.argv)                                                            # creates instance of QApplication
    viewer_window = GuiMain()
    viewer_window.show()
    sys.exit(application.exec_())