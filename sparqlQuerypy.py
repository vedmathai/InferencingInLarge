"""
The purpose of this file is to accept sparql queries run them against the online datasets and return a resultset.
The dependancies are SPARQLWrapper and JSON classes. Which in turn are dependent on rdflib for python.
"""

from SPARQLWrapper import SPARQLWrapper, JSON
endpoint = SPARQLWrapper("http://dbpedia.org/sparql")
query1="""
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbp: <http://dbpedia.org/property/>

"""
query2="""
SELECT DISTINCT ?c ?b ?a WHERE {
?s ?p ?o.
?s dct:subject ?c.
?c skos:broader ?b.
?b skos:broader ?a.
{{?s rdfs:label ?l. ?l bif:contains "'%(name)s'" . FILTER regex(?l,"^%(name)s$" ,"i"). FILTER
(langMatches(lang(?l), "en"))} UNION
{?s dbp:name ?l1. ?l1 bif:contains "'%(name)s'". FILTER regex(?l1,"^%(name)s$" ,"i"). FILTER
(langMatches(lang(?l1), "en"))}}
}

"""




query3="""  
SELECT DISTINCT ?d WHERE{

?s rdfs:label ?l. ?l bif:contains "'^%(name)s$'". FILTER regex(?l,"^%(name)s$" ,"i") . FILTER (langMatches(lang(?l), "en")).
?s a ?d
}

"""

query4="""
 SELECT DISTINCT ?p ?r ?d WHERE {
?s ?p ?o.
{?s a ?r}.
OPTIONAL{?p rdfs:domain ?d}.
{{?s rdfs:label ?l. ?l bif:contains '"%(name1)s"' . FILTER regex(?l,'^%(name1)s$' ,"i"). FILTER (langMatches(lang(?l), "en"))} UNION
{?s dbp:name ?n. ?n bif:contains '"%(name1)s"' . FILTER regex(?n,'^%(name1)s$' ,"i"). FILTER (langMatches(lang(?n), "en"))}} .
{{?o rdfs:label ?l1. ?l1 bif:contains '"%(name2)s"' . FILTER regex(?l1,'^%(name2)s$' ,"i"). FILTER (langMatches(lang(?l1), "en"))} UNION
{?o dbp:name ?n1. ?n1 bif:contains '"%(name2)s"' . FILTER regex(?n1,'^%(name2)s$' ,"i"). FILTER (langMatches(lang(?n1), "en"))}}.

}
"""

query5="""
SELECT DISTINCT ?d ?p ?r WHERE{
?p rdfs:label ?l. ?l bif:contains "'%(name1)s'" . FILTER regex(?l,"^%(name1)s$" ,"i") . FILTER
(langMatches(lang(?l), "en")).
?s ?p ?o.
OPTIONAL{?p rdfs:domain ?d}.
OPTIONAL{?p rdfs:range ?r}
}
"""
query6="""
SELECT DISTINCT ?s ?d ?r WHERE{
?s <%(name1)s> ?o.
FILTER (?r in %(buildString)s).
?s rdf:type ?d. 
?o rdf:type ?r
}
"""

query7="""
 select distinct ?s where {

{{?s a ?p}. FILTER(?p IN (owl:DatatypeProperty, owl:ObjectProperty, rdf:Property)).

{{?s rdfs:comment ?l. ?l bif:contains "%(name1)s". FILTER regex(?l , "\\b%(name1)s\\b" , "i")} UNION {?s rdfs:label ?l. ?l bif:contains "%(name1)s". FILTER regex(?l , "\\b%(name1)s\\b" , "i")}}.

FILTER regex(?s ,"number", "i")}
"""

query8="""
select distinct ?r where {
<%(name)s> a ?r
}
"""
query9="""
select distinct ?r where {
<%(name)s> rdfs:range ?r
}
"""

query10="""
select distinct ?t where {
?s <%(name)s> ?o.
?o a ?t
}
"""
query11="""
select distinct ?d where {
<%(name)s> rdfs:domain ?d
}
"""
query12="""
select distinct ?t where {
?s <%(name)s> ?o.
?s a ?t
}
"""

def findClass(name):
    query=query1+query2%{'name':name}
    return runSparql(query,{'c':'value','b':'value','a':'value'})

def findBottomUp(name):
    query=query1+query3%{'name':name}
    return runSparql(query,{'s':'value','l':'value','d':'value'})

def findProperty(name1, name2):
    query=query1+query4%{'name1':name1, 'name2':name2}
    return runSparql(query,{'s':'value','p':'value','o':'value','d':'value','r':'value'})

def findProperty2(name1, name2):
    query=query1+query4%{'name1':name1, 'name2':name2}
    return runSparql2(query,{'s':'value','p':'value','o':'value','d':'value','r':'value'})


def findPropertyClassesFirst(name1):
    query=query1+query5%{'name1':name1}
    return runSparql2(query,{'p':'value','d':'value','r':'value'})

def findPropertyClassesSecond(name1,buildString):
    query=query1+query6%{'name1':name1, 'buildString':buildString}
    return runSparql2(query,{'s':'value','p':'value','o':'value','d':'value','r':'value'})

def findPropertyClassesThird(name1):
    query=query1+query7%{'name1':name1}
    return runSparql2(query,{'s':'value'})

def findType(name):
    query=query1+query8%{'name':name}
    return runSparql2(query,{'r':'value'})

def findRange(name):
    query=query1+query9%{'name':name}
    return runSparql2(query,{'r':'value'})

def findDomain(name):
    query=query1+query11%{'name':name}
    return runSparql2(query,{'d':'value'})

def findTypeOfObject(name):
    query=query1+query10%{'name':name}
    return runSparql2(query,{'t':'value'})
    
def findTypeOfSubject(name):
    query=query1+query12%{'name':name}
    return runSparql2(query,{'t':'value'})


def runSparql(queryAppend,dictionary):
    queryAppend=query1+queryAppend #Add the select statements and etc. from the calling program
    endpoint.setQuery(queryAppend)
    endpoint.setReturnFormat(JSON)
    results=endpoint.query().convert()
    rlist=[]
    for res in results["results"]["bindings"] :
        row=[]
        for k in dictionary.keys():
            if k in res.keys():
	        row.append(res[k][dictionary[k]])
        rlist.append(row)
    return rlist

def runSparql2(queryAppend,dictionary):
    queryAppend=query1+queryAppend #Add the select statements and etc. from the calling program
    endpoint.setQuery(queryAppend)
    endpoint.setReturnFormat(JSON)
    results=endpoint.query().convert()
    return results["results"]["bindings"]



if __name__=='__main__':
    rlist=findProperty2('book','page')
    for r in rlist:
        if u'r' in r.keys():
            print r
