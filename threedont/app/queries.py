SELECT_ALL_QUERY = """
PREFIX urban:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?p ?x ?y ?z 
       (COALESCE(?r, 0) AS ?r) 
       (COALESCE(?g, 0) AS ?g) 
       (COALESCE(?b, 0) AS ?b)
FROM <{graph}>
WHERE {{
    ?p urban:X ?x;
        urban:Y ?y;
        urban:Z ?z.
    OPTIONAL {{
        ?p urban:R ?r.
        ?p urban:G ?g.
        ?p urban:B ?b.
    }}
}}
"""

FILTER_QUERY = """
PREFIX urban:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p
FROM <{graph}>
WHERE {{
?p 	urban:X ?x;
	urban:Y ?y;
	urban:Z ?z.
	{filter}
}}
"""

# get all the predicates and objects of a point, given its id
GET_NODE_DETAILS = """
PREFIX urban:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p ?o
FROM <{graph}>
WHERE {{
<{point}> ?p ?o.
}}
ORDER BY ?o
"""