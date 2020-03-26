import sys, os
from bkreport import BKReport
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton

class BKReportApp(QMainWindow):
    def __init__(self):
        super(QMainWindow,self).__init__()
        self.initGUI()

    def initGUI(self):
        self.setWindowTitle('BKReport')
        self.setGeometry(300,300,600,400)

        self.query_label=QLabel(self)
        self.query_label.move(20,20)
        self.query_label.setText("Query")

        self.query_edit=QLineEdit(self)
        self.query_edit.move(70,20)
        self.query_edit.resize(500,30)

        self.start_button=QPushButton('Start',self)
        self.start_button.move(400,300)
        self.start_button.clicked.connect(self.Start)

        self.show()

    def Start(self):
        args=['--query',self.query_edit.text()]
        bk=BKReport(args)
        bk.Run()
        
app=QApplication(sys.argv)
bk=BKReportApp()
sys.exit(app.exec_())
