SELECT_ALL_QUERY = """
PREFIX base:<${namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?p ?x ?y ?z 
       (COALESCE(?r, 0) AS ?r) 
       (COALESCE(?g, 0) AS ?g) 
       (COALESCE(?b, 0) AS ?b)
FROM <${graph}>
WHERE {
    ?p base:X ?x;
        base:Y ?y;
        base:Z ?z.
    OPTIONAL {
        ?p base:R ?r.
        ?p base:G ?g.
        ?p base:B ?b.
    }
}
OFFSET ${offset} LIMIT ${limit}
"""

PREDICATE_QUERY = """
PREFIX base:<${namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?x
FROM <${graph}>
WHERE {
    ?s <${predicate}> ?x.
}
OFFSET ${offset} LIMIT ${limit}
"""

# get all the predicates and objects of a point, given its id
GET_NODE_DETAILS = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p ?o
FROM <{graph}>
WHERE {{
<{point}> ?p ?o.
}}
ORDER BY ?o
"""

# sample scalar
"""
PREFIX base:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?x 
FROM <http://localhost:8890/Nettuno>
WHERE {
    ?s base:Constitutes ?part.
    ?part base:Has_Y_Max ?x.
}
"""

# sample select
"""
PREFIX base:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p
FROM <http://localhost:8890/Nettuno>
WHERE {
?p 	base:X ?x;
	base:Y ?y;
	base:Z ?z.
	?p base:Constitutes ?part.
    ?part base:Is_part_of ?obj.
    ?obj a base:Type_Building.
}
"""
