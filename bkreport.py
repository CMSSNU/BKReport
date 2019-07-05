#!/bin/python
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

students={'김준호':{'affiliation':'Seoul Natl. U.','full_names':['Kim, Junho','Kim, J.'],'KRI':11337628,'paper_names':['J. Kim']},
          '김재성':{'affiliation':'Seoul Natl. U.','full_names':['Kim, Jae Sung','Kim, J.S.'],'KRI':11337129,'paper_names':['J.S. Kim','J. S. Kim']},
          '이한얼':{'affiliation':'Seoul Natl. U.','full_names':['Lee, Haneol','Lee, H.'],'KRI':11323419,'paper_names':['H. Lee']},
          '오성빈':{'affiliation':'Seoul Natl. U.','full_names':['Oh, Sung Bin','Oh, S.B.'],'KRI':11323443,'paper_names':['S.B. Oh','S. B. Oh']},
          '변지환':{'affiliation':'Seoul Natl. U.','full_names':['Bhyun, Ji Hwan','Bhyun, J.H.'],'KRI':11456491,'paper_names':['J.H. Bhyun','J. H. Bhyun']},
          '전시현':{'affiliation':'Seoul Natl. U.','full_names':['Jeon, Sihyun','Jeon, S.'],'KRI':11571169,'paper_names':['S. Jeon']},
      }

professors={'양운기':{'affiliation':'Seoul Natl. U.','full_names':['Yang, Unki'],'KRI':00000000,'paper_names':['U. Yang']},}

people={}

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
    if not a['full_name'] in b['full_names']: return False
    return True

def GetPeople(item):
    this_people={}
    for a in item['authors']:
        for key,p in people.iteritems():
            if CheckAuthor(a,p):
                this_people[key]=p
    return this_people

def GetPeopleNames(item):
    this_people=GetPeople(item)
    names=[]
    for key in this_people.iterkeys():
        names+=[key]
    return ','.join(names).decode('utf-8')

def GetPeopleKRIs(item):
    this_people=GetPeople(item)
    kris=[]
    for p in this_people.itervalues():
        kris+=[str(p['KRI'])]
    return ','.join(kris)
    
def GetNumberOfPeople(item):
    return len(GetPeople(item))

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

if options.IsTest:
    options.query='find author u. yang and i. park and tc p and d >= 2018-03'
    options.DEBUG=True

if options.IsProfessor:
    people=professors
else:
    people=students

print options
print people

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
    people_names=GetPeopleNames(item)
    people_kris=GetPeopleKRIs(item)
    npeople=GetNumberOfPeople(item)
    line=str(index+1)+'\t'+title+'\t'+journal+'\t'+issn+'\t'+volume+'\t'+page+'\t'+date+'\t'+str(nauthor)+'\t'+people_names+'\t'+people_kris+'\t'+str(npeople)

    if options.DEBUG: 
        print line 
        print item['recid'], GetDOI(item)

    #Download paper
    pdfname='tmp/'+str(item['recid'])+'.pdf'
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
    doc.save(options.output+'/'+str(index+1)+'-1.pdf')
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
    print start, end, len(doc), range(start,end+1)
    doc.select(range(start,end+1))
 
    ambiguous=[]
    highlights=[]
    for person in GetPeople(item).itervalues():
    #step 1. simple search
        matches=FindPersonMatches(doc,person)
        print person['full_names'][0], matches
        if len(matches)==1:
            doc[matches[0][0]].addHighlightAnnot(matches[0][1])
            highlights+=[matches[0]]

    #step 2. tight search
        elif len(matches)>1:
            matches_tight=FindPersonMatchesTight(doc,person)
            print person['full_names'][0], matches_tight
            if len(matches_tight)==1:
                doc[matches_tight[0][0]].addHighlightAnnot(matches_tight[0][1])
                highlights+=[matches_tight[0]]
            else: 
                ambiguous+=[matches]
    
    #step 3. select the closest to others
    page_y=doc[0].bound().y1
    for am in ambiguous:
        print "ambiguous matches",am
        closest=am[0]
        record=100000
        for match in am:
            for highlight in highlights:
                this_record=abs((match[0]*page_y+match[1].y0)-(highlight[0]*page_y+highlight[1].y0))
                if this_record<record:
                    closest=match
                    record=this_record
        doc[closest[0]].addHighlightAnnot(closest[1])
        print "closest match",record, match
        highlights+=[closest]

    doc.save(options.output+'/'+str(index+1)+'-2.pdf')
    doc.close();
            
    if len(highlights)!=npeople:
        sys.exit('[Error] ['+__name__+'] inconsistent number of people '+str(npeople)+' '+str(len(highlights)))

