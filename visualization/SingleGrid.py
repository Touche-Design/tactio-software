from PyQt5 import QtWidgets, QtCore, Qt, QtGui
from pyqtgraph import PlotWidget, plot
import sys  # We need sys so that we can pass argv to QApplication
import os


class GridPoint(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        #self.palette.setColor(QtGui.QPalette.Window, Qt.red)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(100, 100, 100))
        self.setPalette(p)

    def setColor(color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio 1")
        self.gridWidgets = [GridPoint(), GridPoint(), GridPoint()]
        self.setCentralWidget(self.gridWidgets[0])
       

if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
