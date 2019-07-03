# -*- coding: utf-8 -*- 
import json
import urllib2
import sys

DEBUG=True
students={'김준호':{'CCID':'CCID-753048','INSPIRE_number':'INSPIRE-00430373','affiliation':'Seoul Natl. U.','full_name':'Kim, Junho','KRI':11337628},                                                     
          '김재성':{'CCID':'CCID-760699','INSPIRE_number':'INSPIRE-00585799','affiliation':'Seoul Natl. U.','full_name':'Kim, Jae Sung','KRI':11337129},                                                  
          '이한얼':{'CCID':'CCID-752808','INSPIRE_number':'INSPIRE-00549724','affiliation':'Seoul Natl. U.','full_name':'Lee, Haneol','KRI':11323419},                                                    
          '오성빈':{'CCID':'CCID-752789','INSPIRE_number':'INSPIRE-00384981','affiliation':'Seoul Natl. U.','full_name':'Oh, Sung Bin','KRI':11323443},                                                       
          }

def GetResponse(query):
    query=query.replace(' ','+')
    url='https://inspirehep.net/search?of=recjson&p='+query
    if DEBUG: print url
    return urllib2.urlopen(url)

def GetJsonWithDOI(doi):
    return json.load(GetResponse('doi:'+doi))

def GetJsonWithRECID(recid):
    return json.load(GetResponse('recid:'+recid))

def PrintLine(recid):
    data=GetJsonWithRECID(recid)
    if len(data)!=1:
        sys.exit('[ERROR] ['+__name__+'] len(json) != 1')
        
    title=data[0]['title']['title']
    journal=data[0]['publication_info']['title']
    #issn
    volume=data[0]['publication_info']['volume']
    #issue
    page=data[0]['publication_info']['pagination']
    date=data[0]['imprint']['date']
    nauthor=data[0]['number_of_authors']
    this_students={}
    this_students_name=[]
    this_students_kri=[]
    for a in data[0]['authors']:
        for key,s in students.iteritems():
            if a['full_name']==s['full_name']:
                this_students[key]=s
                this_students_name+=[s['full_name']]
                this_students_kri+=[str(s['KRI'])]

    if DEBUG: 
        print this_students_name
        print this_students_kri

    print '\t'.join([title,journal,volume,page,date,str(nauthor),','.join(this_students_name),','.join(this_students_kri),str(len(this_students))])
    return

def test():
    print "PRL example"
    PrintLine('1620905')
    print "JHEP example"
    PrintLine('1620050')
    print "PRD example"
    PrintLine('1616497')
    print "PLB example"
    PrintLine('1616207')
    print "PRC example"
    PrintLine('1614482')
    return


          
          
