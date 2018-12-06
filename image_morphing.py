#!/usr/local/bin/python3

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, \
    QPushButton, QGroupBox, QAction, QFileDialog, qApp
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import cv2

SUCCESS = 0
ERROR = 1

class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()

        self.title = 'Image Morphing'

        # Booelans to trach if input, target and result images are loaded
        self.inputLoaded = False
        self.targetLoaded = False
        self.resultLoaded = False

        self.triangled = False
        self.morphed = False

        # Fix the size so boxes cannot expand
        self.setFixedSize(self.geometry().width(), self.geometry().height())

        self.initUI()

    def addImageToGroupBox(self, image, groupBox, labelString):
        # Get the height, width information
        height, width, channel = image.shape
        bytesPerLine = 3 * width # 3 Channels

        # Swap the channels from BGR to RGB
        qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()

        pix = QPixmap(qImg)

        # Add image  to the widget
        label = QLabel(labelString)
        label.setPixmap(pix)
        label.setAlignment(Qt.AlignCenter)
        groupBox.layout().addWidget(label)

    def getPointsFromFile(self, fileName, image):
        points = []

        textFile = open(fileName)

        for line in textFile:
            x, y = line.split(",")
            points.append((int(x), int(y)))

        height, width, _ = image.shape

        points.append((int(2), int(2)))
        points.append((int(width/2),int(2)))
        points.append((int(width-3), int(2)))
        points.append((int(2),int(height/2)))
        points.append((int(2), int(height-3)))
        points.append((int(width-3),int(height/2)))
        points.append((int(width/2),int(height-3)))
        points.append((int(width-3), int(height-3)))

        return points

    def convertImagePathToPointsPath(self, fileName):
        return fileName[0:-3] + "txt"

    def openInputImage(self):
        # This function is called when the user clicks File->Input Image.

        fName = QFileDialog.getOpenFileName(self, 'Open input file', './', 'Image files (*.png *.jpg)')

        # File open dialog has been cancelled or file could not be found
        if fName[0] is '':
            return

        # If there is an input or a result image loaded, remove them
        if self.inputLoaded:
            self.deleteItemsFromWidget(self.inputGroupBox.layout())
            self.triangled = False

        if self.resultLoaded:
            self.deleteItemsFromWidget(self.resultGroupBox.layout())
            self.resultLoaded = False
            self.morphed = False

        self.inputImage = cv2.imread(fName[0]) # Read the image
        self.inputLoaded = True

        self.resultImage = self.inputImage.copy()
        self.resultLoaded = True

        self.inputPoints = self.getPointsFromFile(self.convertImagePathToPointsPath(fName[0]), self.inputImage)

        self.addImageToGroupBox(self.inputImage, self.inputGroupBox, 'Input image')
        self.addImageToGroupBox(self.resultImage, self.resultGroupBox, 'Result image')

    def openTargetImage(self):
        # This function is called when the user clicks File->Target Image.
        fName = QFileDialog.getOpenFileName(self, 'Open target file', './', 'Image files (*.png *.jpg)')

        # File open dialog has been cancelled or file could not be found
        if fName[0] is '':
            return

        # If there is an target or a result image loaded, remove them
        if self.targetLoaded:
            self.deleteItemsFromWidget(self.targetGroupBox.layout())
            self.triangled = False
            if self.resultLoaded and self.morphed:
                self.deleteItemsFromWidget(self.resultGroupBox.layout())
                self.resultLoaded = True
                self.addImageToGroupBox(self.resultImage, self.resultGroupBox, 'Result image')
                self.morphed = False

        self.targetImage = cv2.imread(fName[0]) # Read the image
        self.targetLoaded = True

        self.targetPoints = self.getPointsFromFile(self.convertImagePathToPointsPath(fName[0]), self.targetImage)

        self.addImageToGroupBox(self.targetImage, self.targetGroupBox, 'Target image')

    def initUI(self):
        # Add menu bar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('File')
        
        # Create action buttons of the menu bar
        inputAct = QAction('Open input', self)
        inputAct.triggered.connect(self.openInputImage)

        targetAct = QAction('Open target', self) 
        targetAct.triggered.connect(self.openTargetImage)

        exitAct = QAction('Exit', self)        
        exitAct.triggered.connect(qApp.quit) # Quit the app

        # Add action buttons to the menu bar
        fileMenu.addAction(inputAct)
        fileMenu.addAction(targetAct)
        fileMenu.addAction(exitAct)

        # Create create triangulation button for toolbar
        createTriangAct = QAction('Create Triangulation', self) 
        createTriangAct.triggered.connect(self.createTriangulationButtonClicked)

        # Create morph button for toolbar
        morphAct = QAction('Morph', self) 
        morphAct.triggered.connect(self.morphButtonClicked)
        
        # Create toolbar
        toolbar = self.addToolBar('Image Morphing')
        toolbar.addAction(createTriangAct)
        toolbar.addAction(morphAct)

        # Create empty group boxes 
        self.createEmptyInputGroupBox()
        self.createEmptyTargetGroupBox()
        self.createEmptyResultGroupBox()

        # Since QMainWindows layout has already been set, create central widget
        # to manipulate layout of main window
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Initialize input, target, result boxes
        windowLayout = QGridLayout()
        windowLayout.addWidget(self.inputGroupBox, 0, 0)
        windowLayout.addWidget(self.targetGroupBox, 0, 1)
        windowLayout.addWidget(self.resultGroupBox, 0, 2)
        wid.setLayout(windowLayout)

        self.setWindowTitle(self.title) 
        self.showMaximized()
        self.show()

    def createEmptyInputGroupBox(self):
        self.inputGroupBox = QGroupBox('Input')
        layout = QVBoxLayout()

        self.inputGroupBox.setLayout(layout)

    def createEmptyTargetGroupBox(self):
        self.targetGroupBox = QGroupBox('Target')
        layout = QVBoxLayout()

        self.targetGroupBox.setLayout(layout)

    def createEmptyResultGroupBox(self):
        self.resultGroupBox = QGroupBox('Result')
        layout = QVBoxLayout()

        self.resultGroupBox.setLayout(layout)

    def checkMissingLoadedImages(self):
        if not self.inputLoaded and not self.targetLoaded:
            # Error: "First load input and target images" in MessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Input and target images are missing.")
            msg.setText('First load input and target images!')
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec()
            return ERROR
        elif not self.inputLoaded:
            # Error: "Load input image" in MessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Input image is missing.")
            msg.setText('Load input image!')
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec()
            return ERROR
        elif not self.targetLoaded:
            # Error: "Load target image" in MessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Target image is missing.")
            msg.setText('Load target image!')
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec()
            return ERROR

        return SUCCESS

    def createTriangulationButtonClicked(self):
        if self.checkMissingLoadedImages():
            return

        iT, triangledInputImage = self.createTriangulatedImage(self.inputImage, self.inputPoints)
        tT, triangledTargetImage = self.createTriangulatedImage(self.targetImage, self.targetPoints)

        self.inputTriangles = iT
        self.targetTriangles = tT

        self.deleteItemsFromWidget(self.inputGroupBox.layout())
        self.addImageToGroupBox(triangledInputImage, self.inputGroupBox, 'Input image')

        self.deleteItemsFromWidget(self.targetGroupBox.layout())
        self.addImageToGroupBox(triangledTargetImage, self.targetGroupBox, 'Target image')

        self.triangled = True

    def createTriangulatedImage(self, image, points):
        height, width, _ = image.shape

        rectangle = (0, 0, width, height)
        sd = cv2.Subdiv2D(rectangle)

        imageCopy = image.copy()

        for p in points:
            cv2.circle(imageCopy, p, 2, (255,255,255), cv2.FILLED, cv2.LINE_AA, 0)
            sd.insert(p)

        triangles = sd.getTriangleList()

        for t in triangles:
            p1 = (t[0], t[1]) # Point 1
            p2 = (t[2], t[3]) # Point 2
            p3 = (t[4], t[5]) # Point 3

            if self.isInRectangle(rectangle, [p1, p2, p3]):
                cv2.line(imageCopy, p1, p2, (255,255,255), 1, cv2.LINE_AA, 0)
                cv2.line(imageCopy, p2, p3, (255,255,255), 1, cv2.LINE_AA, 0)
                cv2.line(imageCopy, p3, p1, (255,255,255), 1, cv2.LINE_AA, 0)

        return (triangles, imageCopy)

    def isInRectangle(self, r, points):
        for p in points:
            if p[0] < r[0] or p[1] < r[1] or p[0] > r[2] or p[1] > r[3]:
                return False
        return True

    def morphButtonClicked(self):
        if self.checkMissingLoadedImages():
            return
        elif not self.triangled:
            # Error: "First triangulate the images" in MessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Images are not triangulated.")
            msg.setText('First triangulate the images!')
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec()
            return

        

        return NotImplemented

    def deleteItemsFromWidget(self, layout):
        # Deletes items in the given layout
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    deleteItemsFromWidget(item.layout())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())