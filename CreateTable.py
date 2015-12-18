import Neo4jDrive
import CSVWrite
from py2neo import Graph
import csv
import math
graph = Graph("http://neo4j:vedmathai@localhost:7474/db/data/")

i=5
number=6
with open('../csv/eggs%s.csv'%number,'wb') as csvfile:
    writer=csv.writer(csvfile, delimiter=',',quotechar='{')
    writer.writerow(['Domain Class','CCS Score','DCS Score', 'Table','Overall Score'])

    for record in graph.cypher.execute("MATCH (n) where n.hyp='yes' return n.name, n.ccs, n.DCS"):
        ccs=record[1]
        dms=record[2]
        if ccs!=None and dms!=None and ccs!=0 and dms!=0:
            r=[]
            domain=record[0]
            csv=math.sqrt((ccs*ccs)+(dms*dms))
            table=Neo4jDrive.tableMembership(domain)
            entropy=-(ccs)/(ccs+dms)*math.log(ccs/(ccs+dms))-(dms)/(ccs+dms)*math.log(dms/(ccs+dms))
            overall=csv*entropy*table
            r.append(domain)    
            r.append(ccs)
            r.append(dms)
            r.append(table) 
            r.append(overall)
            writer.writerow(r)
        
        


    #CSVWrite.csvWrite(record)
        """
        m=[]
        if record[0] !=u'Broader':
            m.append(record[0])
            print record[1]
            m.append(record[1].properties["name"])
            m.append(record[2].properties["name"])
            m.append(record[2].properties["count"])
            writer.writerow(m)
       """


