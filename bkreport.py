#!/bin/python
# -*- coding: utf-8 -*-
import sys,os,optparse,re
import json
import requests
import fitz
import chardet
import openpyxl
from six import text_type
from io import open

##################################################
############### Class ############################
##################################################
class MyParser(optparse.OptionParser):
    def format_epilog(self, formatter):
        return self.expand_prog_name(self.epilog)

class BKReport:
    avail_format=["empty","index","title","journal","issn","doi","volume","page","date","date(yyyymm)","date(yymm)","nauthor","names","kris","npeople"]
    test_query="author u. yang and type-code p and journal-year 2020"
    def __init__(self,options=[]):
        if len(options):
            self.Init(options)
        
    def Init(self,options=[]):
        parser=MyParser(usage='%prog {--query QEURY|--input INFILE} [--output OUTFILE] [--select SELECTIONEXP]',version='1.0',description='Listing papers using INSPIREHEP and finding authors in PDF file',epilog='''EXAMPLES: 
  ## find papars with "author = u. yang && i. park" and "typecode=Published" and "JournalYear=2019" from inspirehep.
  ## And select papers published in 2019Jan<=date<=2019June
       bekreport --query "find author u. yang and i. park and tc p and jy 2019" --selection "date[20190101,20190630]"
  ## Start from INFO file in output directory of other run.
       bekreport --input out/info.txt --selection "date[20190301,20190331]"

NOTE:
  "date" query in inspirehep is not reliable.
  So, use "journalyear(jy)" and --select argument.
''')
        parser.add_option('-q','--query',dest='query',type='str',help='query string to be used for inspirehep. Refernce: https://inspirehep.net/info/hep/search-tips')
        parser.add_option('-i','--input',dest='info',default='',help='using info file instead of query')
        parser.add_option('-o','--output',dest='output',default='out',type='str',help='output directory')
        parser.add_option('-p','--people',dest='PeopleFile',default='people.json',help='json file with information of people to investigate')
        parser.add_option('-t','--test',dest='IsTest',action='store_true',default=False,help='test mode')
        parser.add_option('-d','--debug',dest='DEBUG',action='store_true',default=False,help='debug mode')
        parser.add_option('-s','--select',dest='select',type='str',default='',help='selection expressions. "date[201708,201801]"->201708<=date<=201801. "date(201708,201801)"->201708<date<201801')
        parser.add_option('-f','--format',dest='FormatFile',type='str',default='format.json',help='format file path')
        #parser.add_option('-v','--verbose',dest='VERBOS',action='store_true',default=False,help='verbose mode')
        (self.options, args_dummpy)=parser.parse_args(options)
        self.options.people={}
        self.options.form=[]
        self.summary=[]
        
    def Print(self,msg):
        print(msg)

    def Finish(self,msg):
        pass

    def Progress(self,prog):
        pass

    def Exit(self,code=0,msg=""):
        if msg!="": self.Print(msg)
        exit(code)
    
    def GetQueryURL(self,query):
        query=query.replace(' ','+')
        return 'https://inspirehep.net/search?of=recjson&p='+query
    		
    def GetRecordURL(self,recid):
        return 'https://inspirehep.net/record/'+str(recid)+'?of=recjson'
    
    def GetTitle(self,item):
        try: title=item['title']['title']
        except:
            try: title=item['title'][0]['title']
            except:
                try: title=item['title_additional'][0]['title']
                except:
                    self.Print('Cannot find title')
                    self.Print(json.dumps(item,indent=2,ensure_ascii=False))
        return title
    
    def GetJournal(self,item):
        if type(item['publication_info']) is list:
            journal=item['publication_info'][-1]['title']
            volume=item['publication_info'][-1]['volume']
        else:
            journal=item['publication_info']['title']
            volume=item['publication_info']['volume']
    
        if journal=='JINST': 
            return 'Journal of Instrumentation'
        elif journal=='JHEP': 
            return 'Journal of High Energy Physics'
        elif journal=='Phys.Rev.Lett.': 
            return 'Physical Review Letters'
        elif journal=='Eur.Phys.J.' and volume[0]=='C': 
            return 'European Physical Journal C'
        elif journal=='IEEE Trans.Nucl.Sci.': 
            return 'IEEE Transactions on Nuclear Science'
        elif journal=='Phys.Lett.' and volume[0]=='B': 
            return 'Physics Letters B'
        elif journal=='Phys.Rev.' and volume[0]=='C': 
            return 'Physical Review C'
        elif journal=='Phys.Rev.' and volume[0]=='D': 
            return 'Physical Review D'
        elif journal=='Nucl.Instrum.Meth.' and volume[0]=='A': 
            return 'Nuclear Instruments and Methods in Physics Research Section A'
        else: 
            self.Exit(1,'  [Error] [GetJournal] wrong journal or volume "'+journal+'" "'+volume+'"')
    
    
    def GetISSN(self,item):
        journal=self.GetJournal(item)
        if journal=='Journal of Instrumentation': 
            return '1748-0221'
        elif journal=='Journal of High Energy Physics': 
            return '1029-8479'
        elif journal=='Physical Review Letters': 
            return '0031-9007'
        elif journal=='European Physical Journal C': 
            return '1434-6044'
        elif journal=='IEEE Transactions on Nuclear Science': 
            return '0018-9499'
        elif journal=='Physics Letters B':
            return '0370-2693'
        elif journal=='Physical Review C':
            return '2469-9985'
        elif journal=='Physical Review D':
            return '2470-0029'
        elif journal=='Nuclear Instruments and Methods in Physics Research Section A':
            return '0168-9002'
        else: 
            self.Exit(1,'  [Error] [GetISSN] wrong journal '+journal)
    
    def GetVolume(self,item):
        if type(item['publication_info']) is list:
            return item['publication_info'][-1]['volume']
        else:
            return item['publication_info']['volume']
    
    def GetPage(self,item):
        if type(item['publication_info']) is list:
            return item['publication_info'][-1]['pagination']
        else:
            return item['publication_info']['pagination']
    
    def GetDate(self,item):
        journal=self.GetJournal(item)
        if 'imprint' in item.keys():
            date=item['imprint']['date']
        elif journal=='Journal of High Energy Physics':
            r=requests.get('http://doi.org/'+self.GetDOI(item))
            rr=re.search(r'First Online: </span><span class="article-dates__first-online"><time datetime="([0-9]{4}-[0-9]{2}-[0-9]{2})">',r.content.decode('utf-8'))
            if not rr: rr=re.search(r'Published<span class="u-hide">: </span><span class="u-clearfix c-bibliographic-information__value"><time datetime="([0-9]{4}-[0-9]{2}-[0-9]{2})">',r.content.decode('utf-8'))
            if rr:
                date=rr.group(1)
            else:
                self.Print(r.content)
                self.Print('http://doi.org/'+self.GetDOI(item))
        else:
            errorline='  [Error] [GetDate] Cannot find date'
            self.summary+=[errorline]
            date='0000-00-00'
    
        if len(date)==10:
            return date[0:4]+date[5:7]+date[8:10]
        else:
            self.Exit(1,'  [Error] [GetDate] wrong date format '+date)
    
    def GetNumberOfAuthors(self,item):
        return item['number_of_authors']
    
    def CheckAuthor(self,a,b):
        if 'affiliation' in a:
            if not b['affiliation'] in a['affiliation']: return False
        if not a['full_name'] in b['full_names']: return False
        return True
    
    def GetPeopleInItem(self,item):
        this_people={}
        for a in item['authors']:
            for key,p in self.options.people.items():
                if self.CheckAuthor(a,p):
                    this_people[key]=p
        return this_people
    
    def GetPeopleNames(self):
        names=[]
        for key in self.options.people:
            names+=[key]
        return ','.join(names)

    def GetPeopleNamesInItem(self,item):
        this_people=self.GetPeopleInItem(item)
        names=[]
        for key in this_people:
            names+=[key]
        return ','.join(names)
    
    def GetPeopleKRIsInItem(self,item):
        this_people=self.GetPeopleInItem(item)
        kris=[]
        for p in this_people.values():
            kris+=[str(p['KRI'])]
        return ','.join(kris)
        
    def GetNumberOfPeopleInItem(self,item):
        return len(self.GetPeopleInItem(item))
    
    def GetDOI(self,item):
        if type(item['doi']) is not list:
            return item['doi']
        elif type(item['doi'][0]) is not list:
            return item['doi'][0]
        else:
            self.Exit(1,'  [Error] [GetDOI] wrong doi format')
            
    def SavePaperAlt(self,item):
        count=0
        for f in item['files']:
            if f['type']!='arXiv' and f['superformat']=='.pdf' and re.search(r"[a-zA-Z]",f['name']) and not re.search("arXiv",f['name']):
               count+=1
               url=f['url']
    
        if count>1: 
            errorline='  [Warning] [SavePaperAlt] not uniqe matching file '+str(count)+'. Getting last one.'
            self.Print(errorline)
            self.summary+=[errorline]
        elif count==0:
            errorline='  [Warning] [SavePaperAlt] no matching file '+str(count)+'. SavePaperAlt failed.'
            self.Print(errorline)
            self.summary+=[errorline]
            if self.options.DEBUG:
                self.Print(json.dumps(item['files'],indent=2,ensure_ascii=False))
            return False
            
        r=requests.get(url)
        if r:
            with open(os.path.join('tmp',str(item['recid'])+'.pdf'),'wb') as rawpdf:
                rawpdf.write(r.content)
            return True
        else:
            self.summary+=['  [Error] [SavePaperAlt] url error '+url+' Try later']
            return False
    
    def SavePaper(self,item):
        journal=self.GetJournal(item)
        doi=self.GetDOI(item)
        headers={'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0'}
        if journal=='Journal of Instrumentation': 
            url='https://iopscience.iop.org/article/'+doi+'/pdf'
        elif journal=='Journal of High Energy Physics': 
            url='https://link.springer.com/content/pdf/'+doi
        elif journal=='Physical Review Letters': 
            url='https://journals.aps.org/prl/pdf/'+doi
        elif journal=='European Physical Journal C': 
            url='https://link.springer.com/content/pdf/'+doi
        elif journal=='IEEE Transactions on Nuclear Science': 
            return
        elif journal=='Physics Letters B' or journal=='Nuclear Instruments and Methods in Physics Research Section A':
            r=requests.get('https://www.doi.org/'+doi).url
            id=r[r.rfind('/')+1:]
            url='https://www.sciencedirect.com/science/article/pii/'+id+'/pdfft?download=true'
            r=requests.get(url,headers=headers)
            url=re.search(r'a href="([^"]*pdf[^"]*)',r.content.decode('utf-8')).group(1)
        elif journal=='Physical Review C':
            url='https://journals.aps.org/prc/pdf/'+doi
        elif journal=='Physical Review D':
            url='https://journals.aps.org/prd/pdf/'+doi
        else: 
            self.Exit(1,'  [Error] [SavePaper] wrong journal '+journal)
    
        if headers: r=requests.get(url,headers=headers)
        else: r=requests.get(url)
            
        if r:
            with open(os.path.join('tmp',str(item['recid'])+'.pdf'),'wb') as rawpdf:
                rawpdf.write(r.content)
        else:
            self.Print('[Info] [SavePaper] cannot access '+url+' Trying alternative method')
            rr=self.SavePaperAlt(item)
            if not self.SavePaperAlt(item):
                while not os.path.exists(os.path.join('tmp',str(item['recid']))+'.pdf'):
                    raw_input('[Info] [SavePaper] Failed to get '+self.GetDOI(item)+'\n please save it as \''+os.path.join(os.path.getcwd(),'tmp',+str(item['recid'])+'.pdf')+'\' mannually and press Enter key.')
        return
    
    def FindPersonMatches(self,doc,person):
        matches=[]
        for paper_name in person['paper_names']:
            for i in range(len(doc)):
                for inst in doc[i].searchFor(paper_name):
                    unique=True
                    for match in matches:
                        if match[0]==i and match[1].intersects(inst):
                            unique=False
                    if unique: matches+=[(i,inst)]
        return matches
    
    def FindPersonMatchesTight(self,doc,person):
        matches=[]
        for paper_name in person['paper_names']:
            for i in range(len(doc)):
                for inst in doc[i].searchFor(', '+paper_name):
                    unique=True
                    for match in matches:
                        if match[0]==i and match[1].intersects(inst):
                            unique=False
                    if unique: matches+=[(i,inst)]
        return matches
    
    @staticmethod
    def LoadJson(filepath):
        if not os.path.exists(filepath):
            return None
        with open(filepath,"rb") as f:
            content=f.read()
            encoding=chardet.detect(content)['encoding']
            if encoding is None:
                return False
            else:
                try:
                    return json.loads(content.decode(encoding))
                except:
                    return False

    @staticmethod
    def CheckPeople(people):
        if not type(people) is dict:
            return False
        for name in people:
            if not "affiliation" in people[name]:
                return False
            if not "full_names" in  people[name]:
                return False
            if not type(people[name]["full_names"]) is list:
                return False
            if not "KRI" in  people[name]:
                return False
            if not type(people[name]["KRI"]) is int:
                return False
            if not "paper_names" in  people[name]:
                return False
            if not type(people[name]["paper_names"]) is list:
                return False
        return True

    @staticmethod
    def CheckFormat(form):
        if not type(form) is list:
            return False
        for data in form:
            if not data in BKReport.avail_format:
                return False
        return True
    
    def GetData(self,item,datastr):
        if datastr == "empty":
            return text_type('')
        elif datastr == "title":
            return text_type(self.GetTitle(item))
        elif datastr == "journal":
            return text_type(self.GetJournal(item))
        elif datastr == "issn":
            return text_type(self.GetISSN(item))
        elif datastr == "doi":
            return text_type(self.GetDOI(item))
        elif datastr == "volume":
            return text_type(self.GetVolume(item))
        elif datastr == "page":
            return text_type(self.GetPage(item))
        elif datastr == "date":
            return text_type(self.GetDate(item))
        elif datastr == "date(yymm)":
            return text_type(self.GetDate(item)[2:6])
        elif datastr == "date(yyyymm)":
            return text_type(self.GetDate(item)[0:6])
        elif datastr == "nauthor":
            return text_type(self.GetNumberOfAuthors(item))
        elif datastr == "names":
            return text_type(self.GetPeopleNamesInItem(item))
        elif datastr == "kris":
            return text_type(self.GetPeopleKRIsInItem(item))
        elif datastr == "npeople":
            return text_type(self.GetNumberOfPeopleInItem(item))
        else:
            self.Exit(1,"[Error] [GetData] No data with name "+datastr)

    def run(self):
        options=self.options
        self.Progress(1)
        if options.IsTest:
            options.query=BKReport.test_query
        if options.query is None and options.info == "":
            self.Exit(1,"[Error] no input")
            return
            
        options.people=self.LoadJson(options.PeopleFile)
        if not BKReport.CheckPeople(options.people):
            self.Exit(1,"[Error] Invalid people file")
            return
        
        options.form=self.LoadJson(options.FormatFile)
        if not BKReport.CheckFormat(options.form):
            self.Exit(1,"[Error] Invalid format file")
            return
    
        date_select=re.search(r'date([\(\[0-9]*),([0-9\]\)]*)',options.select)
        date_begin=None
        date_end=None
        if date_select:
            date_begin=date_select.group(1)
            if date_begin[0] == '[' : date_begin=int(date_begin[1:])-1
            elif date_begin[0] == '(' : date_begin=int(date_begin[1:])
            else:
                self.Exit(1,'[Error] Wrong selection expression')
                return
            date_end=date_select.group(2)
            if date_end[-1] == ']' : date_end=int(date_end[:-1])+1
            elif date_end[-1] == ')' : date_end=int(date_end[:-1])
            else:
                self.Exit(1,'[Error] Wrong selection expression')
                return

        if options.DEBUG:
            self.Print("--------------Options------------------")
            self.Print(json.dumps(vars(options),indent=2,ensure_ascii=False))
            self.Print("---------------------------------------")

        if not options.info == "":
            self.Print("> INFO file: "+options.info)
        else:
            self.Print("> QUERY: "+options.query)
            self.Print("> URL: "+self.GetQueryURL(options.query))

        
        self.Print("> PEOPLE: "+self.GetPeopleNames())
        self.Print("> SELECTION:")
        if date_begin : self.Print("    date > "+str(date_begin))
        if date_end : self.Print("    date < "+str(date_end))

        if os.path.exists(options.output) and os.listdir(options.output):
            suffix_index=0
            while os.path.exists(options.output+"_"+str(suffix_index)) and os.listdir(options.output+"_"+str(suffix_index)):
                suffix_index+=1
            options.output+='_'+str(suffix_index)
            
        self.Print("> OUT: "+options.output)
        if not os.path.exists(options.output):
            os.mkdir(options.output)
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        summaries=[]

        nitem=0
        recids=[]
        if not options.info == "":
            infofilelines= [line.rstrip('\n') for line in open(options.info)]
            nitem=len(infofilelines)
            for line in infofilelines:
                recids+=[int(line.split()[0])]
        else:
            request_for_num=requests.get(self.GetQueryURL(options.query).replace("recjson","xm")+'&rg=1&ot=001')
            request_for_num_search=re.search(r"Search-Engine-Total-Number-Of-Results: ([0-9]+)",request_for_num.text)
            if request_for_num_search: nitem=int(request_for_num_search.group(1))
            else:
                self.Exit(1,"[Error] no response from INSPIREHEP")
                return
            rg=250
            for ichunk in range(int(nitem/rg+1)):
                short_items=requests.get(self.GetQueryURL(options.query)+'&ot=recid&rg='+str(rg)+'&jrec='+str(rg*ichunk+1)).json()
                for item in short_items:
                    recids+=[item['recid']]

        if nitem < 1:
            self.Exit(1,'[Error] no item')
            return

        if nitem != len(recids) :
            self.Exit(1,'[Error] nitem != len(recids)')
            return

        self.Print("> Total number of Items before selection: "+str(nitem))
        self.Progress(2)
        
        self.Print("> Get Json from INSPIREHEP or cache")
        items=[]
        for i in range(nitem):
            self.Progress(5+40.*i/nitem)
            recid=recids[i]
            json_path=os.path.join('tmp',str(recid)+'.json')
            if os.path.exists(json_path):
                if options.DEBUG : self.Print("[DEBUG] "+str(i)+" "+str(recid)+" Get from "+json_path)
                with open(json_path,"rb") as f:
                    content=f.read()
                    encoding=chardet.detect(content)['encoding']
                    items+=[json.loads(content.decode(encoding))]
            else:
                if options.DEBUG : self.Print("[DEBUG] "+str(i)+" "+str(recid)+" Get from "+self.GetRecordURL(recid))
                item=requests.get(self.GetRecordURL(recid)).json()[0]
                items+=[item]
                with open(json_path,'w',encoding='utf-8') as f:
                    f.write(text_type(json.dumps(item,indent=2,ensure_ascii=False)))
            if (i+1)%10==0:
                self.Print('  '+str(i+1)+'/'+str(nitem))
        self.Print('  done')
    
        self.Print("> Selecting")
        items_selected=[]
        for index,item in enumerate(items):
            date=int(self.GetDate(item))
            if date_begin:
                if date <= date_begin: continue
            if date_end:
                if date >= date_end: continue
            items_selected+=[item]
        items=items_selected
        self.Print("> Total number of Items after selection: "+str(len(items)))

        if options.info =="":
            self.Print("> Sorting by date")
            for i in range(len(items)-1):
                for j in range(i+1,len(items)):
                    if int(self.GetDate(items[i])) > int(self.GetDate(items[j])):
                        items[i], items[j] = items[j], items[i]
    

        infofile=open(os.path.join(options.output,'info.txt'),'w',encoding='utf-8')
        result=[]
        result+=[options.form]
        for index,item in enumerate(items):
            self.Progress(50+40.*index/nitem)
            self.summary=[]

            title=self.GetTitle(item)
            journal=self.GetJournal(item)
            issn=self.GetISSN(item)
            doi=self.GetDOI(item)
            volume=self.GetVolume(item)
            page=self.GetPage(item)
            date=self.GetDate(item)
            nauthor=self.GetNumberOfAuthors(item)
            people_names=self.GetPeopleNamesInItem(item)
            people_kris=self.GetPeopleKRIsInItem(item)
            npeople=self.GetNumberOfPeopleInItem(item)
            recid=item['recid']

            #line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+people_names+'\t'+people_kris+'\t'+str(npeople)
            #line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn.replace('-','')+'\t'+doi+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+people_names+'\t'+people_kris+'\t'+str(npeople)

            this_result=[]
            for form in options.form:
                if form == "index":
                    this_result+=[text_type(index+1)]
                else:
                    this_result+=[self.GetData(item,form)]
            if options.DEBUG: self.Print('[DEBUG] '+u'\t'.join(this_result))
            result+=[this_result]
 
            infoline=u"{:9.9} {:3.3} {:32.32} {:10.10} {:30.30}".format(text_type(recid),text_type(index+1),doi,date,title)
            infofile.write(infoline+'\n')
            self.summary=[infoline]+self.summary
            for l in self.summary: self.Print(l)

            #Download paper
            pdfname=os.path.join('tmp',str(recid)+'.pdf')
            if not os.path.exists(pdfname):
                self.SavePaper(item)
    
            #Make abstract pdf
            doc=fitz.open(pdfname)
            abspagenumber=0
            for pagenumber in range(len(doc)):
                page=doc[pagenumber]
                if page.searchFor("abstract") or page.searchFor("Abstract") or page.searchFor("ABSTRACT") or page.searchFor("A B S T R A C T"):
                    abspagenumber=pagenumber
                    break;

            doc.select(range(abspagenumber+1))
            doc.save(os.path.join(options.output,str(index+1)+'-1.pdf'))
            doc.close();
    
            #Make authors pdf
            doc=fitz.open(pdfname)
            start=0
            for pagenumber in range(len(doc)):
                page=doc[pagenumber]
                if page.searchFor("Tumasyan"):start=pagenumber
            if start>abspagenumber:
                end=len(doc)-1
            else:
                end=max(abspagenumber-1,0)
            doc.select(range(start,end+1))
 
            ambiguous=[]
            highlights=[]
            for person in self.GetPeopleInItem(item).values():
            #step 1. simple search
                matches=self.FindPersonMatches(doc,person)
                if options.DEBUG:
                    self.Print(person['full_names'][0])
                    for match in matches:
                        self.Print("P"+str(match[0])+" X"+str(match[1].x0)+" Y"+str(match[1].y0))
                if len(matches)==1:
                    doc[matches[0][0]].addHighlightAnnot(matches[0][1])
                    highlights+=[matches[0]]

            #step 2. tight search
                elif len(matches)>1:
                    matches_tight=self.FindPersonMatchesTight(doc,person)
                    if options.DEBUG:
                        self.Print(person['full_names'][0])
                        for match in matches_tight:
                            self.Print("P"+str(match[0])+" X"+str(match[1].x0)+" Y"+str(match[1].y0))
                    if len(matches_tight)==1:
                        doc[matches_tight[0][0]].addHighlightAnnot(matches_tight[0][1])
                        highlights+=[matches_tight[0]]
                    else: 
                        ambiguous+=[matches]
    
            #step 3. select the closest to others
            page_y=doc[0].bound().y1
            for am in ambiguous:
                if options.DEBUG:
                    self.Print("ambiguous matches")
                    for match in am:
                        self.Print("P"+str(match[0])+" X"+str(match[1].x0)+" Y"+str(match[1].y0))

                closest=am[0]
                record=100000
                for match in am:
                    for highlight in highlights:
                        this_record=abs((match[0]*page_y+match[1].y0)-(highlight[0]*page_y+highlight[1].y0))
                        if this_record<record:
                            closest=match
                            record=this_record
                doc[closest[0]].addHighlightAnnot(closest[1])
                if options.DEBUG:
                    self.Print("closest match "+str(record)+", P"+str(match[0])+" X"+str(match[1].x0)+" Y"+str(match[1].y0))
                highlights+=[closest]

            doc.save(os.path.join(options.output,str(index+1)+'-2.pdf'))
            doc.close();
            

            if len(highlights)!=npeople:
                errorline='  [Error] inconsistent number of people and highlight. people:'+str(npeople)+' highlights:'+str(len(highlights))
                self.Print(errorline)
                self.summary+=[errorline]
    
            if len(self.summary)>1: summaries+=self.summary
    
        outputfile=open(os.path.join(options.output,'out.txt'),'w',encoding='utf-8')
        outputxl=openpyxl.Workbook()
        sheet=outputxl.active
        for i in range(len(result)):                
            outputfile.write(u'\t'.join(result[i])+u'\n')
            for j in range(len(result[i])):
                sheet.cell(i+1,j+1).value=result[i][j]
        outputfile.close()
        outputxl.save(os.path.join(options.output,'out.xlsx'))

        self.Print("\n========== Summary =============")
        for l in summaries: self.Print(l)
        self.Print("============ Done ==============")
        self.Progress(100)
        self.Finish(os.path.abspath(options.output))
        
        
if __name__ == "__main__":
    bk=BKReport(sys.argv)
    bk.run()
