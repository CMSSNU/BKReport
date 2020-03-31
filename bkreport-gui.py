import sys, os, io, subprocess, json
from io import open
from six import text_type
from bkreport import BKReport
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

def open_file(filename):
    if sys.platform == "win32":
        os.startfile(filename)
    else:
        opener ="open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, filename])

class BKReportThread(BKReport,QThread):
    print_signal=pyqtSignal(str)
    progress_signal=pyqtSignal(float)
    finish_signal=pyqtSignal(str)
    exception_signal=pyqtSignal(int)
    def __init__(self,options=[],parent=None):
        BKReport.__init__(self,options)
        QThread.__init__(self,parent)
        
    def Print(self,msg):
        self.print_signal.emit(msg+'\n')

    def Finish(self,msg):
        self.finish_signal.emit(msg)

    def Progress(self,prog):
        self.progress_signal.emit(prog)

    def Exit(self,code=0,msg=""):
        self.Print(msg)
        self.exception_signal.emit(code)
        self.exit()
        
class OutputWindow(QWidget):
    def __init__(self,outputdir,parent=None):
        QWidget.__init__(self,parent=parent)
        self.setWindowTitle("Output")
        self.setGeometry(500,500,300,100)

        self.path_label=QLabel(outputdir,self)
        self.dir_button=QPushButton("Open Directory",self)
        self.dir_button.clicked.connect(self.OpenDir)
        self.txt_button=QPushButton("Open txt",self)
        self.txt_button.clicked.connect(self.OpenTXT)
        self.excel_button=QPushButton("Open Excel",self)
        self.excel_button.clicked.connect(self.OpenExcel)

        layout=QGridLayout()
        layout.addWidget(self.path_label,0,0,1,3)
        layout.addWidget(self.dir_button,1,0)
        layout.addWidget(self.txt_button,1,1)
        layout.addWidget(self.excel_button,1,2)
        self.setLayout(layout)
            
        self.show()
    def OpenDir(self):
        open_file(self.path_label.text())
    def OpenTXT(self):
        open_file(os.path.join(self.path_label.text(),"out.txt"))
    def OpenExcel(self):
        open_file(os.path.join(self.path_label.text(),"out.xlsx"))

class PeopleWindow(QWidget):
    def __init__(self,filepath,parent=None):
        QWidget.__init__(self,parent=parent)
        self.setWindowTitle("People")
        self.setGeometry(500,500,400,500)

        self.filepath=filepath
        self.people=BKReport.LoadJson(self.filepath)
        self.tree=QTreeWidget(self)
        self.tree.setColumnCount(2)
        self.tree.setColumnWidth(0,150)
        self.tree.setHeaderLabels(["key","value"])
        for name in self.people:
            self.AddPerson(name,self.people[name])
        self.add_button=QPushButton("Add",self)
        self.add_button.clicked.connect(self.Add)
        self.delete_button=QPushButton("Delete",self)
        self.delete_button.clicked.connect(self.Delete)
        self.save_button=QPushButton("Save",self)
        self.save_button.clicked.connect(self.Save)

        layout=QGridLayout()
        layout.addWidget(self.tree,0,0,1,3)
        layout.addWidget(self.add_button,1,0)
        layout.addWidget(self.delete_button,1,1)
        layout.addWidget(self.save_button,1,2)
        self.setLayout(layout)        
        self.show()

    def Add(self):
        self.AddItem(self.tree.currentItem())

    def AddItem(self,item):
        if item is None:
            self.AddPerson("",{"affiliation":"","full_names":[""],"KRI":"","paper_names":[""]})
        elif item.parent() is None:
            self.AddPerson("",{"affiliation":"","full_names":[""],"KRI":"","paper_names":[""]})
        elif item.text(0) == "affiliation":
            return
        elif item.text(0) == "KRI":
            return
        elif item.text(0) == "full_names":
            empty=QTreeWidgetItem(item)
            self.tree.openPersistentEditor(empty,1)
            self.tree.setCurrentItem(empty,1)
        elif item.text(0) == "paper_names":
            empty=QTreeWidgetItem(item)
            self.tree.openPersistentEditor(empty,1)
            self.tree.setCurrentItem(empty,1)
        else:
            self.AddItem(item.parent())
        
    def AddPerson(self,name,data):
        person=QTreeWidgetItem(self.tree.invisibleRootItem())
        person.setText(0,name)
        self.tree.openPersistentEditor(person,0)
        affiliation=QTreeWidgetItem(person)
        affiliation.setText(0,"affiliation")
        affiliation.setText(1,data["affiliation"])
        self.tree.openPersistentEditor(affiliation,1)
        kri=QTreeWidgetItem(person)
        kri.setText(0,"KRI")
        kri.setText(1,text_type(data["KRI"]))
        self.tree.openPersistentEditor(kri,1)
        full_names=QTreeWidgetItem(person)
        full_names.setText(0,"full_names")
        for n in data["full_names"]:
            name=QTreeWidgetItem(full_names)
            name.setText(1,n)
            self.tree.openPersistentEditor(name,1)
        paper_names=QTreeWidgetItem(person)
        paper_names.setText(0,"paper_names")
        for n in data["paper_names"]:
            name=QTreeWidgetItem(paper_names)
            name.setText(1,n)
            self.tree.openPersistentEditor(name,1)
        self.tree.setCurrentItem(person)
                
    def Delete(self):
        item=self.tree.currentItem()
        if item.parent() is None:
            self.tree.invisibleRootItem().removeChild(item)
        elif item.parent().text(0) == "full_names":
            item.parent().removeChild(item)
        elif item.parent().text(0) == "paper_names":
            item.parent().removeChild(item)
        
    def Save(self):
        root=self.tree.invisibleRootItem()
        people={}
        for i in range(root.childCount()):
            c=root.child(i)
            kor_name=c.text(0)
            affiliation=u""
            kri=u""
            full_names=[]
            paper_names=[]
            for j in range(c.childCount()):
                c2=c.child(j)
                key=c2.text(0)
                if key == "affiliation":
                    affilliation=c2.text(1)
                elif key == "KRI":
                    kri=c2.text(1)
                elif key == "full_names":
                    for k in range(c2.childCount()):
                        full_names+=[c2.child(k).text(1)]
                elif key == "paper_names":
                    for k in range(c2.childCount()):
                        paper_names+=[c2.child(k).text(1)]
            try:
                people[kor_name]={"affiliation":affilliation,"full_names":full_names,"KRI":int(kri),"paper_names":paper_names}
            except:
                QMessageBox.warning(self,"Invalid format","Cannot save the file")
        if BKReport.CheckPeople(people):
            with open(self.filepath,"w",encoding='utf-8') as f:
                f.write(text_type(json.dumps(people,indent=2,ensure_ascii=False)))
                self.close()
        else:
            QMessageBox.warning(self,"Invalid format","Cannot save the file")
                    
    
class FormatWindow(QWidget):
    def __init__(self,filepath,parent=None):
        QWidget.__init__(self,parent=parent)
        self.setWindowTitle("Format")
        self.setGeometry(500,500,500,100)

        self.filepath=filepath
        self.form=BKReport.LoadJson(self.filepath)
        self.table=QTableWidget(self)
        self.table.setRowCount(1)
        self.table.setColumnCount(len(self.form))
        for i in range(len(self.form)):
            wdg=QWidget(self)
            combo=QComboBox(wdg)
            combo.setObjectName("combo")
            combo.addItems(BKReport.avail_format)
            j=combo.findText(self.form[i])
            if j != -1: combo.setCurrentIndex(j)
            else:
                print("[Error] Invalid format "+self.form[i])

            layout=QHBoxLayout(wdg)
            layout.setContentsMargins(0,0,20,0)
            layout.addWidget(combo)
            wdg.setLayout(layout)
            self.table.setCellWidget(0,i,wdg)
                
        self.add_button=QPushButton("Add",self)
        self.add_button.clicked.connect(self.Add)
        self.delete_button=QPushButton("Delete",self)
        self.delete_button.clicked.connect(self.Delete)
        self.save_button=QPushButton("Save",self)
        self.save_button.clicked.connect(self.Save)

        layout=QGridLayout()
        layout.addWidget(self.table,0,0,1,3)
        layout.addWidget(self.add_button,1,0)
        layout.addWidget(self.delete_button,1,1)
        layout.addWidget(self.save_button,1,2)
        self.setLayout(layout)
            
        self.show()
    def Add(self):
        self.table.insertColumn(self.table.currentColumn()+1)
        self.table.setCurrentCell(0,self.table.currentColumn()+1)
        wdg=QWidget(self)
        combo=QComboBox(self)
        combo.setObjectName("combo")
        combo.addItems(BKReport.avail_format)
        layout=QHBoxLayout(wdg)
        layout.setContentsMargins(0,0,20,0)
        layout.addWidget(combo)
        wdg.setLayout(layout)
        self.table.setCellWidget(0,self.table.currentColumn(),wdg)
            
    def Delete(self):
        self.table.removeColumn(self.table.currentColumn())

    def Save(self):
        self.form=[]
        for i in range(self.table.columnCount()):
            self.form+=[self.table.cellWidget(0,i).findChild(QComboBox,"combo").currentText()]
        with open(self.filepath,"w",encoding='utf-8') as f:
            f.write(text_type(json.dumps(self.form,indent=2,ensure_ascii=False)))
        self.close()
        
        
class BKReportApp(QWidget):
    def __init__(self):
        super(QWidget,self).__init__()
        self.initGUI()

    def initGUI(self):
        ######################
        self.setWindowTitle('BKReport')
        self.setGeometry(300,300,1000,600)

        ##########LAYOUT###########
        self.query_check=QRadioButton("Query",self)
        self.query_check.clicked.connect(self.SelectInput)
        self.query_edit=QLineEdit(self)
        self.info_check=QRadioButton("Info file",self)
        self.info_check.clicked.connect(self.SelectInput)
        self.info_check.setFixedWidth(100)
        self.info_path=QLabel("no file selected ...",self)
        self.info_path.setAlignment(Qt.AlignCenter)
        self.info_button=QPushButton("Select",self)
        self.info_button.setFixedWidth(100)
        self.info_button.clicked.connect(self.SelectInfoFile)
        self.info_button.setEnabled(False)
        self.test_check=QRadioButton("Test Query",self)
        self.test_check.clicked.connect(self.SelectInput)
        self.test_label=QLabel(BKReport.test_query,self)
        self.test_label.setAlignment(Qt.AlignCenter)
        input_layout=QGridLayout()
        input_layout.addWidget(self.query_check,0,0)
        input_layout.addWidget(self.query_edit,0,1,1,2)
        input_layout.addWidget(self.info_check,1,0)
        input_layout.addWidget(self.info_path,1,1)
        input_layout.addWidget(self.info_button,1,2)
        input_layout.addWidget(self.test_check,2,0)
        input_layout.addWidget(self.test_label,2,1)
        input_box=QGroupBox("Input Method",self)
        input_box.setLayout(input_layout)

        self.people_path=QLabel(self)
        self.people_path.setAlignment(Qt.AlignCenter)
        self.people_preview=QLabel(self)
        self.people_preview.setAlignment(Qt.AlignCenter)
        self.people_button=QPushButton("Select",self)
        self.people_button.setFixedWidth(100)
        self.people_button.clicked.connect(self.SelectPeopleFile)
        self.people_edit_button=QPushButton("View/Edit",self)
        self.people_edit_button.setFixedWidth(100)
        self.people_edit_button.clicked.connect(self.EditPeopleFile)
        people_layout=QGridLayout()
        people_layout.addWidget(self.people_path,0,0)
        people_layout.addWidget(self.people_button,0,1)
        people_layout.addWidget(self.people_preview,1,0)
        people_layout.addWidget(self.people_edit_button,1,1)
        people_box=QGroupBox("People File",self)
        people_box.setLayout(people_layout)

        self.format_path=QLabel(self)
        self.format_path.setAlignment(Qt.AlignCenter)
        self.format_preview=QLabel(self)
        self.format_preview.setAlignment(Qt.AlignCenter)
        self.format_button=QPushButton("Select",self)
        self.format_button.setFixedWidth(100)
        self.format_button.clicked.connect(self.SelectFormatFile)
        self.format_edit_button=QPushButton("View/Edit",self)
        self.format_edit_button.setFixedWidth(100)
        self.format_edit_button.clicked.connect(self.EditFormatFile)
        format_layout=QGridLayout()
        format_layout.addWidget(self.format_path,0,0)
        format_layout.addWidget(self.format_button,0,1)
        format_layout.addWidget(self.format_preview,1,0)
        format_layout.addWidget(self.format_edit_button,1,1)
        format_box=QGroupBox("Format File",self)
        format_box.setLayout(format_layout)

        self.date_check=QCheckBox("date",self)
        self.date_check.clicked.connect(self.SetDateFilter)
        self.date_start_label=QLabel("from",self)
        self.date_start_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.date_start=QDateEdit(self)
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_end_label=QLabel("to",self)
        self.date_end_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.date_end=QDateEdit(self)
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        filter_layout=QGridLayout()
        filter_layout.addWidget(self.date_check,0,0)
        filter_layout.addWidget(self.date_start_label,0,1)
        filter_layout.addWidget(self.date_start,0,2)
        filter_layout.addWidget(self.date_end_label,0,3)
        filter_layout.addWidget(self.date_end,0,4)
        filter_box=QGroupBox("Filter",self)
        filter_box.setLayout(filter_layout)
        
        self.output_check=QCheckBox("Auto",self)
        self.output_check.setFixedWidth(100)
        self.output_check.clicked.connect(self.SetAutoOutputDir)
        self.output_path=QLabel("No directory selected ...",self)
        self.output_path.setAlignment(Qt.AlignCenter)
        self.output_button=QPushButton("Select",self)
        self.output_button.setFixedWidth(100)
        self.output_button.clicked.connect(self.SelectOutputDir)
        output_layout=QGridLayout()
        output_layout.addWidget(self.output_check,0,0)
        output_layout.addWidget(self.output_path,0,1)
        output_layout.addWidget(self.output_button,0,2)
        output_box=QGroupBox("Output Directory",self)
        output_box.setLayout(output_layout)
        
        self.debug_check=QCheckBox("Debug",self)
        self.debug_check.setFixedWidth(80)
        self.start_button=QPushButton('Start',self)
        self.start_button.setFixedWidth(100)
        self.progressbar=QProgressBar(self)
        self.start_button.clicked.connect(self.Start)

        self.log=QTextEdit(self)
        self.log.setReadOnly(True)
        log_layout=QVBoxLayout()
        log_layout.addWidget(self.log)
        log_box=QGroupBox("Log",self)
        log_box.setLayout(log_layout)
                
        layout=QGridLayout()
        layout.addWidget(input_box,0,0,1,4)
        layout.addWidget(people_box,1,0,1,2) 
        layout.addWidget(format_box,1,2,1,2)
        layout.addWidget(filter_box,2,0,1,2)
        layout.addWidget(output_box,2,2) 
        layout.addWidget(self.debug_check,2,3)
        layout.addWidget(self.progressbar,3,0,1,3)
        layout.addWidget(self.start_button,3,3)
        layout.addWidget(log_box,4,0,1,4)

        self.setLayout(layout)
        self.show()

        self.SetPeopleFile(os.path.abspath("people.json"))
        self.SetFormatFile(os.path.abspath("format.json"))
        self.query_check.setChecked(True)
        self.query_check.clicked.emit()
        self.date_check.setChecked(False)
        self.date_check.clicked.emit()
        self.output_check.setChecked(True)
        self.output_check.clicked.emit()

        ##########STDOUT###########
        #printOccur=pyqtSignal(str)
        self.stream=io.TextIOBase()
        self.stream.write=self.write
        sys.stdout=self.stream
        print("Welcome")
        
    def Start(self):
        self.start_button.setEnabled(False)
        options=[]
        if self.query_check.isChecked() and self.query_edit.text() != '':
            options+=['--query',self.query_edit.text()]
        elif self.info_check.isChecked():
            options+=['--input',self.info_path.text()]
        elif self.test_check.isChecked():
            options+=['--test']
        if self.debug_check.isChecked():
            options+=['--debug']
        if not self.output_check.isChecked():
            options+=['--output',self.output_path.text()]
        if self.date_check.isChecked():
            options+=['--select','date['+self.date_start.date().toString("yyyyMMdd")+','+self.date_end.date().toString("yyyyMMdd")+']']
        options+=['--people',self.people_path.text()]
        options+=['--format',self.format_path.text()]
        print(options)
        self.bk=BKReportThread(options=options,parent=self)
        self.bk.print_signal.connect(self.write)
        self.bk.progress_signal.connect(self.Progress)
        self.bk.finish_signal.connect(self.Finish)
        self.bk.exception_signal.connect(self.OnException)
        self.bk.start()

    def SelectInput(self):
        if self.query_check.isChecked():
            self.query_edit.setEnabled(True)
            self.info_path.setEnabled(False)
            self.info_button.setEnabled(False)
            self.test_label.setEnabled(False)
        elif self.info_check.isChecked():
            self.query_edit.setEnabled(False)
            self.info_path.setEnabled(True)
            self.info_button.setEnabled(True)
            self.test_label.setEnabled(False)
        elif self.test_check.isChecked():
            self.query_edit.setEnabled(False)
            self.info_path.setEnabled(False)
            self.info_button.setEnabled(False)
            self.test_label.setEnabled(True)

    def SelectInfoFile(self):
        fname = QFileDialog.getOpenFileName(self)[0]
        if fname != "":
            self.info_path.setText(fname)

    def SelectPeopleFile(self):
        fname=QFileDialog.getSaveFileName(options=QFileDialog.DontConfirmOverwrite)[0]
        if fname != "":
            self.SetPeopleFile(fname)
        
    def SetPeopleFile(self,path):
        self.people_path.setText(path)
        people=BKReport.LoadJson(path)
        if people is None:
            self.people_preview.setText("NEW")
            self.people_edit_button.setEnabled(True)
        elif people is False:
            self.people_preview.setText("INVALID")
            self.people_edit_button.setEnabled(False)
        elif BKReport.CheckPeople(people):
            self.people_preview.setText(",".join(people.keys()))
            self.people_edit_button.setEnabled(True)
        else:
            self.people_preview.setText("INVALID")
            self.people_edit_button.setEnabled(False)

    def EditPeopleFile(self):
        self.peoplewindow=PeopleWindow(self.people_path.text())

    def SelectFormatFile(self):
        fname=QFileDialog.getSaveFileName(options=QFileDialog.DontConfirmOverwrite)[0]
        if fname != "":
            self.SetFormatFile(fname)

    def SetFormatFile(self,path):
        self.format_path.setText(path)
        form=BKReport.LoadJson(path)
        if form is None:
            self.format_preview.setText("NEW")
            self.format_edit_button.setEnabled(True)
        elif form is False:
            self.format_preview.setText("INVALID")
            self.format_edit_button.setEnabled(False)
        elif BKReport.CheckFormat(form):
            self.format_preview.setText("VALID")
            self.format_edit_button.setEnabled(True)
        else:
            self.format_preview.setText("INVALID")
            self.format_edit_button.setEnabled(False)

    def EditFormatFile(self):
        self.formatwindow=FormatWindow(self.format_path.text())

    def SetDateFilter(self):
        if self.date_check.isChecked():
            self.date_start_label.setEnabled(True)
            self.date_start.setEnabled(True)
            self.date_end_label.setEnabled(True)
            self.date_end.setEnabled(True)
        else:
            self.date_start_label.setEnabled(False)
            self.date_start.setEnabled(False)
            self.date_end_label.setEnabled(False)
            self.date_end.setEnabled(False)

    def SetAutoOutputDir(self):
        if self.output_check.isChecked():
            self.output_path.setEnabled(False)
            self.output_button.setEnabled(False)
        else:
            self.output_path.setEnabled(True)
            self.output_button.setEnabled(True)
        
    def SelectOutputDir(self):
        fname = QFileDialog.getExistingDirectory(self)
        if fname != "":
            self.output_path.setText(fname)

    def write(self,msg):
        self.log.moveCursor(QTextCursor.End)
        self.log.insertPlainText(msg)

    def Finish(self,outputdir):
        self.outputwindow=OutputWindow(outputdir)
        self.start_button.setEnabled(True)

    def OnException(self,code):
        self.start_button.setEnabled(True)
        self.progressbar.setValue(0)

    def Progress(self,prog):
        self.progressbar.setValue(prog)
        
app=QApplication(sys.argv)
bk=BKReportApp()
sys.exit(app.exec_())
