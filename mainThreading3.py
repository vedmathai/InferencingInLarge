import CSVRead
import sparqlQuerypy
import Neo4jDrive
import random
from threading import Thread, Lock
import datetime

log=open("log.log",'a')
log.write("\n--------------------------------------\n")
log.write(str(datetime.datetime.now()))
log.write("\n")

hypothesisSet=set()
stype=[]
sample=5
data=[]
csvitems=[]
def main():
    csvitems=[]
    data=[]
    tables=["StatesandCapitals.csv","RiversandSourceState.csv"]
    size=[]

    for nameOfFile in tables:
        Neo4jDrive.insertNode(nameOfFile)
        node=Neo4jDrive.findNodeByName(nameOfFile)
        node.properties['type']='table'
        node.push()
        csvitems+=[CSVRead.readCSV(nameOfFile,firstRow=False, choice=[0,1])[1:]]
        size+=[len(csvitems)]
        random.shuffle(csvitems[-1])
    i=k=0          
    while len(csvitems)>0:
        
        for l,item in enumerate(csvitems):
            
            end=k+sample
            s=sample
            if k+sample>len(item):
                s=sample-(end-len(item))
                end=len(item)
            data[i:i+s]=[[it,l] for it in item[k:end]]
            i+=s
            if k+sample>len(item):
               csvitems.remove(item)
        k+=sample
    run(data,tables,size)


def run(data,tables,size):
    support=[[]]
    columnNames=[]
    for i,nameOfFile in enumerate(tables):
        print i
        columnNames+=[CSVRead.readCSV(nameOfFile,firstRow=True, choice=[0,1])]
        columnNames[i]=[c.strip() for c in columnNames[i]]
        print 'this is',columnNames[i]
        for j,name in enumerate(columnNames[i]):
            z=Neo4jDrive.insertNodeAndRelationship(nameOfFile,"Column",name)[0]
            z.properties['type']="Column"
            z.push()
            print len(support),i
            support[i]+=[CSVRead.getSupport(nameOfFile,j)]
        support+=[[]]
    support=support[:-1]
   
    totalNumberOfValues=[[CSVRead.numberOfItems(s) for s in ss] for ss in support]
   
    
    hyplock=Lock()
    stypelock=Lock()
    
    for itemPiece in data:
        indexOfFile=itemPiece[1]
        item=itemPiece[0]
        for column in range(len(columnNames[indexOfFile])):
        #support=CSVRead.getSupport(nameOfFile,column)
        #totalNumberOfValues=CSVRead.numberOfItems(support)
        
            k=ccThread(item[column],columnNames[indexOfFile],column,support[indexOfFile],size)
            #k.start()
            #k.join()
    for itemPiece in data:
        indexOfFile=itemPiece[1]
        item=itemPiece[0]
        for column in range(len(columnNames[indexOfFile])):
           #support=CSVRead.getSupport(nameOfFile,column)
           #totalNumberOfValues=CSVRead.numberOfItems(support)

            for perm_column in range(len(columnNames[indexOfFile])):
                if perm_column!=column:
                    k=dmsThread(item[column],item[perm_column],size[indexOfFile],columnNames[indexOfFile],column,perm_column)
                    k.start()
                    k.join()
        
        
    allCC=set(Neo4jDrive.findAllCCNodes())
    for c in columnNames:
        for column in c:
            k=topDownThread(column,hyplock,stypelock,allCC)
            k.start()
            k.join()
       
                
    
class ccThread(Thread):
    def __init__(self,item,columnNames,column,support,totalNumberOfValues):
        Thread.__init__(self)
        self.item=item
        self.columnNames=columnNames
        self.column=column
        self.support=support
        self.totalNumberOfValues=totalNumberOfValues


    def run(self):
        support=self.support
        totalNumberOfValues=self.totalNumberOfValues*1.0

        column=self.column
        columnNames=self.columnNames
        item=self.item
        rlist=sparqlQuerypy.findBottomUp(item.strip())

        print 'number of nodes for', item.strip(), " is ", len(rlist)
        log.write('number of nodes for'+str( item.strip())+ " is "+ str(len(rlist))+'\n')
        for r in rlist:
            rel_data=Neo4jDrive.insertNodeAndRelationship(columnNames[column],"cc",r[2])       
            node=Neo4jDrive.findNodeByName(r[2])
            if node.properties['incoming']==None:
                node.properties['incoming']=1
                node.properties['ccs']=1/totalNumberOfValues
            else:
                node.properties['incoming']+=1
                node.properties['ccs']=node.properties['incoming']/totalNumberOfValues
            node.properties['type']='cc'
            node.push()
            
            
            rel_data=rel_data[0]
            rel_data.properties['rel_class'] = 'cc'
            #rel_data.properties['ccs']=node.proper/(totalNumberOfValues*1.0)
            rel_data.push()

class dmsThread(Thread):
    def __init__(self,label1,label2,size,columnNames,column,perm_column):
        Thread.__init__(self)
        self.label1=label1.strip()
        self.label2=label2.strip()
        self.size=size
        self.columnNames=columnNames
        self.column=column
	self.perm_column=perm_column

    def run(self):
        rlist=sparqlQuerypy.findProperty2(self.label1,self.label2)
        print '------------------'
        log.write('----------------\n')
        log.write(str(datetime.datetime.now())+'\n')
        log.write(self.label1+self.label2)
        print self.label1,self.label2#,rlist
        
        cache=[]
        propertyUsage=[1]
        for r in rlist:
            if u'd' in r.keys():
                self.addProperty(r['p']['value'])
                rel_data=Neo4jDrive.insertNodeAndRelationship(self.columnNames[self.column],"property",r['d']['value'])[0]
                rel_data['name']='property'
                rel_data.push()
            else:
                ccClasses=Neo4jDrive.findCCNodes(self.columnNames[self.perm_column])
                buildString="("
                for i in ccClasses:
                    buildString+='<'+i+'>,'
                buildString=buildString[:-1]
                buildString+=")"
                if r['p']['value'] not in cache:
                    propertyUsage=sparqlQuerypy.findPropertyClassesSecond(r['p']['value'],buildString)
                    cache+=[r['p']['value']]
                
                    print len(propertyUsage),r['p']['value']
                    if len(propertyUsage)<15000:
                        for item in (set([k['r']['value'] for k in propertyUsage]) & set(ccClasses)):
                             self.addProperty(r['p']['value'])
                             rel_data=Neo4jDrive.insertNodeAndRelationship(self.columnNames[self.column],"domain",item)[0]
                             rel_data['name']="domain"
                             rel_data.push()
                             self.incrementDms(item)

    
    def incrementDms(self,name):
        node=Neo4jDrive.findNodeByName(name)
        if node.properties['DCSinc']==None:
            node.properties['DCSinc']=1
            node.properties['DCS']=1.0/self.size
                
        else:
            node.properties['DCSinc']+=1
            node.properties['DCS']=node.properties['DCSinc']*1.0/self.size
        node.properties['hyp']='yes'
        node.properties['type']='cc'
        node.push()
    




    def addProperty(self,p):
        rel_data=Neo4jDrive.insertNodeAndRelationship(self.columnNames[self.column],"property",p)
        hypothesisSet.add(p)
        node=Neo4jDrive.findNodeByName(p)
        if node.properties['dcsincoming']==None:
            node.properties['dcsincoming']=1
            node.properties['dcs']=1/(self.size*1.0)
        else:
            node.properties['dcsincoming']+=1
            node.properties['dcs']=node.properties['dcsincoming']/(self.size*1.0)
        node.properties['type']='property'
        node.push()
        rel=Neo4jDrive.insertRelationship(self.columnNames[self.column], p, self.columnNames[self.perm_column])[0]
        if rel.properties['propCount']==None:    
            rel.properties['type']='property_rel'
            rel.properties['name']=p
            rel.properties['dms']=1
        else:
            rel.properties['dms']+=1
                
        rel.push()

class topDownThread(Thread):
    def __init__(self, item1, hyplock, stypelock, allCC):
        Thread.__init__(self)
        self.a=item1.strip()
        self.hyplock=hyplock
        self.stypelock=stypelock
        self.allCC=allCC
   
    def run(self):
        count=0
        objtypes=[]
        rlist=sparqlQuerypy.findPropertyClassesFirst(self.a)
        
        for r in rlist:
            if u'r' not in r.keys():
                ccClasses=Neo4jDrive.findCCNodes(self.a)
                buildString="("
                for i in ccClasses:
                    buildString+='<'+i+'>,'
                buildString=buildString[:-1]
                buildString+=")"
                propertyUsage=sparqlQuerypy.findPropertyClassesSecond(r['p']['value'],buildString)
                for item in (set([k['d']['value'] for k in propertyUsage]) & hypothesisSet):
                    print count
                    count+=1
                    rel=Neo4jDrive.insertNodeAndRelationship(self.a ,'p', r['p']['value'])
                    self.hyplock.acquire()
                    hypothesisSet.add(r['p']['value'])
                    self.hyplock.release()
                    temp=Neo4jDrive.findNodeByName(r['p']['value'])
                    temp.properties['hyp']='yes'
                    temp.push()
                    rel=Neo4jDrive.insertNodeAndRelationship(r['p']['value'], 'd', item)
                for item in (set([k['d']['value'] for k in propertyUsage]) & set(self.allCC)):
                    rel=Neo4jDrive.insertNodeAndRelationship(self.a, 'p', r['p']['value'])
                    self.hyplock.acquire()
                    hypothesisSet.add(r['p']['value'])
                    self.hyplock.release()
                    temp=Neo4jDrive.findNodeByName(r['p']['value'])
                    temp.properties['hyp']='yes'
                    temp.push()
                    rel=Neo4jDrive.insertNodeAndRelationship(r['p']['value'], 'd', item)
                        
                        

    def levenshtein(s1, s2):
        if len(s1) < len(s2):
            return levenshtein(s2, s1)

    # len(s1) >= len(s2)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
                deletions = current_row[j] + 1       # than s2
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
    
        return previous_row[-1]

                

    def addProperty(self,p):
        rel_data=Neo4jDrive.insertNodeAndRelationship(self.columnNames[self.column],"property",p)
        hypothesisSet.add(p)
        node=Neo4jDrive.findNodeByName(p)
        if node.properties['incoming']==None:
            node.properties['incoming']=1
            node.properties['dms']=1/(self.size*1.0)
        else:
            node.properties['incoming']+=1
            node.properties['dms']=node.properties['incoming']/(self.size*1.0)
        node.properties['type']='property'
        node.properties['hyp']='yes'
        node.push()
        rel=Neo4jDrive.insertRelationship(self.columnNames[self.column], p, self.columnNames[self.perm_column])[0]
            
        rel.properties['type']='property_rel'
        rel.properties['lms']=levenshtein(p,self.columnNames[self.column])
        rel.properties['name']=p
        rel.push()


        

if __name__=='__main__':
    

    main()


