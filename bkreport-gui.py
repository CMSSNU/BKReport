import sys, os, io
from bkreport import BKReport
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import threading, time

class BKReportThread(BKReport,QThread):
    print_signal=pyqtSignal(str)
    progress_signal=pyqtSignal(float)
    finish_signal=pyqtSignal()
    def __init__(self,options,parent=None):
        BKReport.__init__(self,options)
        QThread.__init__(self,parent)
        
    def Print(self,msg):
        self.print_signal.emit(msg+'\n')

    def Finish(self):
        self.finish_signal.emit()

    def Progress(self,prog):
        self.progress_signal.emit(prog)

class BKReportApp(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()
        self.initGUI()

    def initGUI(self):
        ######################
        self.setWindowTitle('BKReport')
        self.setGeometry(300,300,800,600)

        ##########LAYOUT###########
        self.query_check=QRadioButton("Query",self)
        self.query_check.clicked.connect(self.SelectInput)
        self.query_check.setChecked(True)
        self.query_edit=QLineEdit(self)
        self.info_check=QRadioButton("Info file",self)
        self.info_check.clicked.connect(self.SelectInput)
        self.info_check.setFixedWidth(100)
        self.info_path=QLabel("no file selected ...",self)
        self.info_path.hide()
        self.info_path.setAlignment(Qt.AlignCenter)
        self.info_button=QPushButton("select file",self)
        self.info_button.setFixedWidth(150)
        self.info_button.clicked.connect(self.SelectInfoFile)
        self.info_button.setEnabled(False)
        input_layout=QGridLayout()
        input_layout.addWidget(self.query_check,0,0)
        input_layout.addWidget(self.query_edit,0,1,1,4)
        input_layout.addWidget(self.info_check,1,0)
        input_layout.addWidget(self.info_path,1,1,1,3)
        input_layout.addWidget(self.info_button,1,4)
        input_box=QGroupBox("Input Method",self)
        input_box.setLayout(input_layout)

        self.people_path=QLabel(os.path.abspath('people.json'),self)
        self.people_path.setAlignment(Qt.AlignCenter)
        self.people_button=QPushButton("Select file",self)
        self.people_button.setFixedWidth(150)
        self.people_button.clicked.connect(self.SelectPeopleFile)
        people_layout=QHBoxLayout()
        people_layout.addWidget(self.people_path)
        people_layout.addWidget(self.people_button)
        people_box=QGroupBox("People Directory",self)
        people_box.setLayout(people_layout)

        self.output_path=QLabel("AUTO",self)
        self.output_path.setAlignment(Qt.AlignCenter)
        self.output_button=QPushButton("Select directory",self)
        self.output_button.setFixedWidth(150)
        output_layout=QHBoxLayout()
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)
        output_box=QGroupBox("Output Directory",self)
        output_box.setLayout(output_layout)
        
        self.debug_check=QCheckBox("Debug Mode",self)
        self.test_check=QCheckBox("Test Mode",self)
        self.start_button=QPushButton('Start',self)
        self.start_button.setFixedWidth(150)
        self.progressbar=QProgressBar(self)
        self.start_button.clicked.connect(self.Start)

        self.log=QTextEdit(self)
        log_layout=QVBoxLayout()
        log_layout.addWidget(self.log)
        log_box=QGroupBox("Log",self)
        log_box.setLayout(log_layout)
                
        layout=QGridLayout()
        layout.addWidget(input_box,0,0,1,3)
        layout.addWidget(people_box,1,0,1,3) 
        layout.addWidget(output_box,2,0,1,3) 
        layout.addWidget(self.test_check,3,0)
        layout.addWidget(self.debug_check,3,1)
        layout.addWidget(self.progressbar,4,0,1,2)
        layout.addWidget(self.start_button,4,2)
        layout.addWidget(log_box,5,0,1,3)

        self.setLayout(layout)
        self.show()


        ##########STDOUT###########
        #printOccur=pyqtSignal(str)
        self.stream=io.TextIOBase()
        self.stream.write=self.write
        sys.stdout=self.stream
        print("Welcome")
        
    def Start(self):
        self.start_button.setEnabled(False)
        options=[]
        if self.query_check.isChecked() and not self.test_check.isChecked():
            options+=['--query',self.query_edit.text()]
        elif self.info_check.isChecked():
            options+=['--input',self.info_path.text()]
        if self.test_check.isChecked():
            options+=['--test']
        if self.debug_check.isChecked():
            options+=['--debug']
        options+=['--people',self.people_path.text()]
        self.bk=BKReportThread(options,self)
        self.bk.print_signal.connect(self.write)
        self.bk.progress_signal.connect(self.Progress)
        self.bk.finish_signal.connect(self.Finish)
        self.bk.start()

    def SelectInput(self):
        if self.query_check.isChecked():
            self.query_edit.setEnabled(True)
            self.info_path.hide()
            self.info_button.setEnabled(False)
        elif self.info_check.isChecked():
            self.query_edit.setEnabled(False)
            self.info_path.show()
            self.info_button.setEnabled(True)

    def SelectInfoFile(self):
        fname = QFileDialog.getOpenFileName(self)
        self.info_path.setText(fname[0])

    def SelectPeopleFile(self):
        fname = QFileDialog.getOpenFileName(self)
        self.people_path.setText(fname[0])

    def write(self,msg):
        self.log.moveCursor(QTextCursor.End)
        self.log.insertPlainText(msg)

    def Finish(self):
        self.start_button.setEnabled(True)

    def Progress(self,prog):
        self.progressbar.setValue(prog)
        
app=QApplication(sys.argv)
bk=BKReportApp()
sys.exit(app.exec_())
