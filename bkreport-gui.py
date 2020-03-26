import sys, os
from bkreport import BKReport
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

class BKReportApp(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()
        self.initGUI()

    def initGUI(self):
        self.setWindowTitle('BKReport')
        self.setGeometry(300,300,600,400)

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

        self.output_path=QLabel("AUTO",self)
        self.output_path.setAlignment(Qt.AlignCenter)
        self.output_button=QPushButton("select directory",self)
        self.output_button.setFixedWidth(150)
        output_layout=QHBoxLayout()
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)
        output_box=QGroupBox("Output Directory",self)
        output_box.setLayout(output_layout)
        
        self.debug_check=QCheckBox("Debug Mode",self)
        self.start_button=QPushButton('Start',self)
        self.start_button.clicked.connect(self.Start)

        self.log=QTextEdit(self)
        log_layout=QVBoxLayout()
        log_layout.addWidget(self.log)
        log_box=QGroupBox("Log",self)
        log_box.setLayout(log_layout)
        
        
        layout=QGridLayout()
        layout.addWidget(input_box,0,0,1,3)
        layout.addWidget(output_box,1,0,1,3)
        layout.addWidget(self.debug_check,2,1)
        layout.addWidget(self.start_button,2,2)
        layout.addWidget(log_box,3,0,1,3)

        self.setLayout(layout)
        self.show()

    def Start(self):
        args=['--query',self.query_edit.text()]
        bk=BKReport(args)
        bk.Run()

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

        
app=QApplication(sys.argv)
bk=BKReportApp()
sys.exit(app.exec_())
