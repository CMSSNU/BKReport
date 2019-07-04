##### encoding: utf-8 
import sys,os,optparse,re
import json,urllib2,requests
import fitz

parser=optparse.OptionParser()
parser.add_option("-q","--query",dest="query",help="inspirehep query ref. https://inspirehep.net/info/hep/search-tips")
parser.add_option("-p","--professor",dest="IsProfessor",action="store_true",default=False,help="run mode for professor")
parser.add_option("-o","--output",dest="output",default='out',help="output directory")
parser.add_option("-t","--test",dest="IsTest",action="store_true",default=False,help="test mode")
parser.add_option("-d","--debug",dest="DEBUG",action="store_true",default=False,help="debug mode")

(options, args)=parser.parse_args(sys.argv)

students={'김준호':{'CCID':'CCID-753048','INSPIRE_number':'INSPIRE-00430373','affiliation':'Seoul Natl. U.','full_name':'Kim, Junho','KRI':11337628,'paper_name':'J. Kim','alt_name':'Kim, J.'},
          '김재성':{'CCID':'CCID-760699','INSPIRE_number':'INSPIRE-00585799','affiliation':'Seoul Natl. U.','full_name':'Kim, Jae Sung','KRI':11337129,'paper_name':'J.S. Kim','alt_name':'Kim, J.S.'},
          '이한얼':{'CCID':'CCID-752808','INSPIRE_number':'INSPIRE-00549724','affiliation':'Seoul Natl. U.','full_name':'Lee, Haneol','KRI':11323419,'paper_name':'H. Lee','alt_name':'Lee, H.'},
          '오성빈':{'CCID':'CCID-752789','INSPIRE_number':'INSPIRE-00384981','affiliation':'Seoul Natl. U.','full_name':'Oh, Sung Bin','KRI':11323443,'paper_name':'S.B. Oh','alt_name':'Oh, S.B.'},
          }

def GetResponse(query):
    query=query.replace(' ','+')
    url='https://inspirehep.net/search?of=recjson&p='+query
    if options.DEBUG: print url
    return urllib2.urlopen(url)

def GetJsonWithDOI(doi):
    return json.load(GetResponse('doi:'+str(doi)))

def GetJsonWithRECID(recid):
    return json.load(GetResponse('recid:'+str(recid)))

def GetTitle(item):
    try: title=item['title']['title']
    except: title=item['title'][0]['title']
    return title

def GetJournal(item):
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
    elif journal=='Phys.Rev.' and volume[0]=='D': 
        return 'Physical Review D'
    elif journal=='Nucl.Instrum.Meth.' and volume[0]=='A': 
        return 'Nuclear Instruments and Methods in Physics Research Section A'
    else: 
        sys.exit('[Error] ['+__name__+'] wrong journal or volume '+journal+' '+volume)


def GetISSN(item):
    journal=GetJournal(item)
    if journal=='Journal of Instrumentation': 
        return '1748-0221'
    elif journal=='Journal of High Energy Physics': 
        return '1029-8479'
    elif journal=='Physical Review Letters': 
        return '0031-9007'
    elif journal=='European Physical Journal C': 
        return '1434-6052'
    elif journal=='IEEE Transactions on Nuclear Science': 
        return '0018-9499'
    elif journal=='Physics Letters B':
        return '0370-2693'
    elif journal=='Physical Review D':
        return '2470-0029'
    elif journal=='Nuclear Instruments and Methods in Physics Research Section A':
        return '0168-9002'
    else: 
        sys.exit('[Error] ['+__name__+'] wrong journal '+journal)

def GetVolume(item):
    return item['publication_info']['volume']

def GetPage(item):
    return item['publication_info']['pagination']

def GetDate(item):
    date=item['imprint']['date']
    if len(date)==10:
        return date[0:4]+date[5:2]
    else:
        sys.exit('[Error] ['+__name__+'] wrong date format '+date)

def GetNumberOfAuthors(item):
    return item['number_of_authors']

def CheckAuthor(a,b):
    if 'affiliation' in a:
        if a['affiliation']!=b['affiliation']: return False
    if a['full_name']!=b['full_name'] and a['full_name']!=b['alt_name']: return False
    return True

def GetStudentNames(item):
    student_names=[]
    for a in item['authors']:
        for key,s in students.iteritems():
            if CheckAuthor(a,s):
                student_names+=[key]
    return ','.join(student_names).decode('utf-8')

def GetStudentKRIs(item):
    student_kris=[]
    for a in item['authors']:
        for key,s in students.iteritems():
            if CheckAuthor(a,s):
                student_kris+=[str(s['KRI'])]
    return ','.join(student_kris)
    
def GetNumberOfStudents(item):
    n=0
    for a in item['authors']:
        for key,s in students.iteritems():
            if CheckAuthor(a,s):
                n+=1
    return n

def GetDOI(item):
    if type(item['doi']) is not list:
        return item['doi']
    elif type(item['doi'][0]) is not list:
        return item['doi'][0]
    else:
        sys.exit('[Error] ['+__name__+'] wrong doi format')
        
def SavePaperAlt(item):
    count=0
    for f in item['files']:
        if f['type']!='arXiv' and f['superformat']=='.pdf' and re.search(r"[a-zA-Z]",f['name']):
           count+=1
           url=f['url']

    if count!=1: sys.exit('[Error] ['+__name__+'] not uniqe matching file '+str(count))
    r=requests.get(url)
    if r:
        with open('tmp/'+str(item['recid'])+'.pdf','wb') as rawpdf:
            rawpdf.write(r.content)
    else:
        print '[Error] ['+__name__+'] url error '+url
        print '  Try later'
    return

def SavePaper(item):
    journal=GetJournal(item)
    doi=GetDOI(item)
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
        r=r[r.rfind('/')+1:]
        url='https://www.sciencedirect.com/science/article/pii/'+r+'/pdfft'
    elif journal=='Physical Review D':
        url='https://journals.aps.org/prd/pdf/'+doi
    else: 
        sys.exit('[Error] ['+__name__+'] wrong journal '+journal)

    r=requests.get(url)
    if r:
        with open('tmp/'+str(item['recid'])+'.pdf','wb') as rawpdf:
            rawpdf.write(r.content)
    else:
        print '[Warning] ['+__name__+'] url error '+url
        print '  Trying alternative method'
        SavePaperAlt(item)
    return

if options.IsTest:
    options.query='find author u. yang and i. park and tc p and d >= 2018-03'
    options.DEBUG=True

print options

os.system('mkdir -p '+options.output)
os.system('mkdir -p tmp')

items=json.load(GetResponse(options.query))
for index,item in enumerate(items):
    title=GetTitle(item)
    journal=GetJournal(item)
    issn=GetISSN(item)
    volume=GetVolume(item)
    page=GetPage(item)
    date=GetDate(item)
    nauthor=GetNumberOfAuthors(item)
    student_names=GetStudentNames(item)
    student_kris=GetStudentKRIs(item)
    nstudent=GetNumberOfStudents(item)
    line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+student_names+'\t'+student_kris+'\t'+str(nstudent)
    print line 

    if options.DEBUG: print item['recid'], GetDOI(item)

    pdfname='tmp/'+str(item['recid'])+'.pdf'
    if not os.path.exists(pdfname):
        SavePaper(item)
    
    doc=fitz.open(pdfname)
    for pagenumber in range(len(doc)):
        page=doc[pagenumber]
        if page.searchFor("abstract") or page.searchFor("Abstract") or page.searchFor("ABSTRACT"):
            doc.select([pagenumber])
            doc.save(options.output+'/'+str(index+1)+'-1.pdf')
            break;
    doc.close();
    
    doc=fitz.open(pdfname)
    last=0
    for pagenumber in range(len(doc)):
        page=doc[pagenumber]
        if page.searchFor("Tumasyan"):last=pagenumber
        
    doc.select(range(last,len(doc)))
    count=0
    for student in students.itervalues():
        for page in doc:
            text_instances=page.searchFor(' '+student['paper_name'])
            for inst in text_instances:
                print(inst,type(inst))
                highlight=page.addHighlightAnnot(inst)
                count+=1
    if count!=nstudent:
        sys.exit('[Error] ['+__name__+'] inconsistent number of students '+str(nstudent)+' '+str(count))

    doc.save(options.output+'/'+str(index+1)+'-2.pdf')
    doc.close();
