#!/bin/python
# -*- coding: utf-8 -*-
import sys,os,optparse,re
import json
import requests
import fitz
import chardet
from io import open

summary=[]
DEBUG=False
##################################################
############### Get functions#####################
##################################################
def GetQueryURL(query):
    query=query.replace(' ','+')
    return 'https://inspirehep.net/search?of=recjson&p='+query

def GetRecordURL(recid):
    return 'https://inspirehep.net/record/'+str(recid)+'?of=recjson'

def GetTitle(item):
    try: title=item['title']['title']
    except:
        try: title=item['title'][0]['title']
        except:
            try: title=item['title_additional'][0]['title']
            except:
                print('Cannot find title')
                print(json.dumps(item,indent=2))
    return title

def GetJournal(item):
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
        sys.exit('  [Error] [GetJournal] wrong journal or volume "'+journal+'" "'+volume+'"')


def GetISSN(item):
    journal=GetJournal(item)
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
        sys.exit('  [Error] [GetISSN] wrong journal '+journal)

def GetVolume(item):
    if type(item['publication_info']) is list:
        return item['publication_info'][-1]['volume']
    else:
        return item['publication_info']['volume']

def GetPage(item):
    if type(item['publication_info']) is list:
        return item['publication_info'][-1]['pagination']
    else:
        return item['publication_info']['pagination']

def GetDate(item):
    global summary
    journal=GetJournal(item)
    if 'imprint' in item.keys():
        date=item['imprint']['date']
    elif journal=='Journal of High Energy Physics':
        r=requests.get('http://doi.org/'+GetDOI(item))
        rr=re.search(r'First Online: </span><span class="article-dates__first-online"><time datetime="([0-9]{4}-[0-9]{2}-[0-9]{2})">',r.content.decode('utf-8'))
        if not rr: rr=re.search(r'Published<span class="u-hide">: </span><span class="u-clearfix c-bibliographic-information__value"><time datetime="([0-9]{4}-[0-9]{2}-[0-9]{2})">',r.content.decode('utf-8'))
        if rr:
            date=rr.group(1)
        else:
            print(r.content)
            print('http://doi.org/'+GetDOI(item))
    else:
        errorline='  [Error] [GetDate] Cannot find date'
        summary+=[errorline]
        date='0000-00-00'

    if len(date)==10:
        return date[0:4]+date[5:7]
    else:
        sys.exit('  [Error] [GetDate] wrong date format '+date)

def GetNumberOfAuthors(item):
    return item['number_of_authors']

def CheckAuthor(a,b):
    if 'affiliation' in a:
        if not b['affiliation'] in a['affiliation']: return False
    if not a['full_name'] in b['full_names']: return False
    return True

def GetPeopleInItem(item,people):
    this_people={}
    for a in item['authors']:
        for key,p in people.items():
            if CheckAuthor(a,p):
                this_people[key]=p
    return this_people

def GetPeopleNamesInItem(item,people):
    this_people=GetPeopleInItem(item,people)
    names=[]
    for key in this_people:
        names+=[key]
    return ','.join(names)

def GetPeopleKRIsInItem(item,people):
    this_people=GetPeopleInItem(item,people)
    kris=[]
    for p in this_people.values():
        kris+=[str(p['KRI'])]
    return ','.join(kris)
    
def GetNumberOfPeopleInItem(item,people):
    return len(GetPeopleInItem(item,people))

def GetDOI(item):
    if type(item['doi']) is not list:
        return item['doi']
    elif type(item['doi'][0]) is not list:
        return item['doi'][0]
    else:
        sys.exit('  [Error] [GetDOI] wrong doi format')
        
def SavePaperAlt(item):
    global summary
    count=0
    for f in item['files']:
        if f['type']!='arXiv' and f['superformat']=='.pdf' and re.search(r"[a-zA-Z]",f['name']) and not re.search("arXiv",f['name']):
           count+=1
           url=f['url']

    if count>1: 
        errorline='  [Warning] [SavePaperAlt] not uniqe matching file '+str(count)+'. Getting last one.'
        print(errorline)
        summary+=[errorline]
    elif count==0:
        errorline='  [Warning] [SavePaperAlt] no matching file '+str(count)+'. SavePaperAlt failed.'
        print(errorline)
        summary+=[errorline]
        global DEBUG
        if DEBUG:
            print(json.dumps(item['files'],indent=2))
        return False
        
    r=requests.get(url)
    if r:
        with open(os.path.join('tmp',str(item['recid'])+'.pdf'),'wb') as rawpdf:
            rawpdf.write(r.content)
        return True
    else:
        summary+=['  [Error] [SavePaperAlt] url error '+url+' Try later']
        return False

def SavePaper(item):
    journal=GetJournal(item)
    doi=GetDOI(item)
    headers={'User-Agent':'Mozilla/5.0'}
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
        sys.exit('  [Error] [SavePaper] wrong journal '+journal)

    r=requests.get(url,headers=headers)
    if r:
        with open(os.path.join('tmp',str(item['recid'])+'.pdf'),'wb') as rawpdf:
            rawpdf.write(r.content)
    else:
        print('[Info] [SavePaper] cannot access '+url+' Trying alternative method')
        rr=SavePaperAlt(item)
        if not SavePaperAlt(item):
            while not os.path.exists(os.path.join('tmp',str(item['recid']))+'.pdf'):
                raw_input('[Info] [SavePaper] Failed to get '+GetDOI(item)+'\n please save it as \''+os.path.join(os.path.getcwd(),'tmp',+str(item['recid'])+'.pdf')+'\' mannually and press Enter key.')
    return

def FindPersonMatches(doc,person):
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

def FindPersonMatchesTight(doc,person):
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

##################################################
############### Class ############################
##################################################
class MyParser(optparse.OptionParser):
    def format_epilog(self, formatter):
        return self.expand_prog_name(self.epilog)

class BKReport:
    def __init__(self,args):
        parser=MyParser(usage='%prog {--query QEURY|--input INFILE} [--output OUTFILE] [--select SELECTIONEXP]',version='1.0',description='Listing papers using INSPIREHEP and finding authors in PDF file',epilog='''EXAMPLES: 
  ## find papars with "author = u. yang && i. park" and "typecode=Published" and "JournalYear=2019" from inspirehep.
  ## And select papers published in 2019Jan<=date<=2019June
    bekreport --query "find author u. yang and i. park and tc p and jy 2019" --selection "date[201901,201906]"
  ## Start from INFO file in output directory of other run.
  bekreport --input out/info.txt --selection "date[201903,201903]"

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
        #parser.add_option('-v','--verbose',dest='VERBOS',action='store_true',default=False,help='verbose mode')
        (self.options, args_dummpy)=parser.parse_args(args)
        self.options.people={}
        global DEBUG
        DEBUG=self.options.DEBUG
        

    def Run(self):
        options=self.options
        if options.IsTest:
            options.query='find author u. yang and i. park and tc p and jy 2020'

        with open(options.PeopleFile,"rb") as people_file:
            content=people_file.read()
            encoding=chardet.detect(content)['encoding']
            options.people=json.loads(content.decode(encoding))
    
        date_select=re.search(r'date([\(\[0-9]*),([0-9\]\)]*)',options.select)
        date_begin=None
        date_end=None
        if date_select:
            date_begin=date_select.group(1)
            if date_begin[0] == '[' : date_begin=int(date_begin[1:])-1
            elif date_begin[0] == '(' : date_begin=int(date_begin[1:])
            else:
                print('[Error] Wrong selection expression')
                exit(1)
            date_end=date_select.group(2)
            if date_end[-1] == ']' : date_end=int(date_end[:-1])+1
            elif date_end[-1] == ')' : date_end=int(date_end[:-1])
            else:
                print('[Error] Wrong selection expression')
                exit(1)

        if options.DEBUG:
            print("--------------Options------------------")
            print(options)
            print("--------------People-------------------")
            print(json.dumps(options.people,indent=2))
            print("---------------------------------------")

        if not options.info == "":
            print("> INFO file: "+options.info)
        else:
            print("> QUERY: "+options.query)
            print("> URL: "+GetQueryURL(options.query))
            
        print("> SELECTION:")
        if date_begin : print("    date > "+str(date_begin))
        if date_end : print("    date < "+str(date_end))

        if os.path.exists(options.output):
            suffix_index=0
            while os.path.exists(options.output+"_"+str(suffix_index)):
                suffix_index+=1
            options.output+='_'+str(suffix_index)
            
        print("> OUT: "+options.output)
        if not os.path.exists(options.output):
            os.mkdir(options.output)
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        summaries=[]

        nitem=0
        infofilelines=[]
        if not options.info == "":
            infofilelines= [line.rstrip('\n') for line in open(options.info)]
            nitem=len(infofilelines)
        else:
            request_for_num=requests.get(GetQueryURL(options.query).replace("recjson","xm")+'&rg=1&ot=001')
            request_for_num_search=re.search(r"Search-Engine-Total-Number-Of-Results: ([0-9]+)",request_for_num.text)
            if request_for_num_search: nitem=int(request_for_num_search.group(1))

        if nitem < 1:
            print('[Error] no item')
            exit(1)
    
        print("> Total number of Items before selection: "+str(nitem))

        print("> Get Json from INSPIREHEP")
        items=[]
        if not options.info =="":
            for i in range(len(infofilelines)):
                line=infofilelines[i]
                recid=int(line.split()[1])
                items+=requests.get(GetRecordURL(recid)).json()
                if (i+1)%10==0: print(str(i+1)+'/'+str(nitem))
        else:
            for ichunk in range(int(nitem/25+1)):
                print(str(ichunk*25)+'/'+str(nitem))
                items+=requests.get(GetQueryURL(options.query+'&jrec='+str(25*ichunk+1))).json()
            print(str(len(items))+'/'+str(nitem))
    

        print("> Selecting")
        items_selected=[]
        for index,item in enumerate(items):
            date=int(GetDate(item))
            if date_begin:
                if date <= date_begin: continue
            if date_end:
                if date >= date_end: continue
            items_selected+=[item]
        items=items_selected
        print("> Total number of Items after selection: "+str(len(items)))

        if options.info =="":
            print("> Sorting by date")
            for i in range(len(items)-1):
                for j in range(i+1,len(items)):
                    if int(GetDate(items[i])) > int(GetDate(items[j])):
                        items[i], items[j] = items[j], items[i]
    

        outputfile=open(os.path.join(options.output,'out.txt'),'w',encoding='utf-8')
        infofile=open(os.path.join(options.output,'info.txt'),'w')
        for index,item in enumerate(items):
            global summary
            summary=[]

            title=GetTitle(item)
            journal=GetJournal(item)
            issn=GetISSN(item)
            doi=GetDOI(item)
            volume=GetVolume(item)
            page=GetPage(item)
            date=GetDate(item)
            nauthor=GetNumberOfAuthors(item)
            people_names=GetPeopleNamesInItem(item,self.options.people)
            people_kris=GetPeopleKRIsInItem(item,self.options.people)
            npeople=GetNumberOfPeopleInItem(item,self.options.people)
            recid=item['recid']

            #line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+people_names+'\t'+people_kris+'\t'+str(npeople)
            line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn.replace('-','')+'\t'+doi+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+people_names+'\t'+people_kris+'\t'+str(npeople)
            if options.DEBUG: print(line)
            outputfile.write((line+'\n'))
 
            infoline=u"{:3.3} {:9.9} {:32.32} {:10.10} {:30.30}".format(str(index+1),str(recid),GetDOI(item),GetDate(item),title)
            infofile.write(infoline+'\n')
            summary=[infoline]+summary
            for l in summary: print(l)

            #Download paper
            pdfname=os.path.join('tmp',str(recid)+'.pdf')
            if not os.path.exists(pdfname):
                SavePaper(item)
    
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
            for person in GetPeopleInItem(item,self.options.people).values():
            #step 1. simple search
                matches=FindPersonMatches(doc,person)
                if options.DEBUG: print(person['full_names'][0], matches)
                if len(matches)==1:
                    doc[matches[0][0]].addHighlightAnnot(matches[0][1])
                    highlights+=[matches[0]]

            #step 2. tight search
                elif len(matches)>1:
                    matches_tight=FindPersonMatchesTight(doc,person)
                    if options.DEBUG: print(person['full_names'][0], matches_tight)
                    if len(matches_tight)==1:
                        doc[matches_tight[0][0]].addHighlightAnnot(matches_tight[0][1])
                        highlights+=[matches_tight[0]]
                    else: 
                        ambiguous+=[matches]
    
            #step 3. select the closest to others
            page_y=doc[0].bound().y1
            for am in ambiguous:
                if options.DEBUG: print("ambiguous matches",am)
                closest=am[0]
                record=100000
                for match in am:
                    for highlight in highlights:
                        this_record=abs((match[0]*page_y+match[1].y0)-(highlight[0]*page_y+highlight[1].y0))
                        if this_record<record:
                            closest=match
                            record=this_record
                doc[closest[0]].addHighlightAnnot(closest[1])
                if options.DEBUG: print("closest match",record, match)
                highlights+=[closest]

            doc.save(os.path.join(options.output,str(index+1)+'-2.pdf'))
            doc.close();
            

            if len(highlights)!=npeople:
                errorline='  [Error] inconsistent number of people and highlight. people:'+str(npeople)+' highlights:'+str(len(highlights))
                print(errorline)
                summary+=[errorline]
    
            if len(summary)>1: summaries+=summary
    
        outputfile.close()

        print("\n############ Summary ###########")
        for l in summaries: print(l)

        
if __name__ == "__main__":
    bk=BKReport(sys.argv)
    bk.Run()
