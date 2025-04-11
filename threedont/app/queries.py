SELECT_ALL_QUERY = """
PREFIX urban:<http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p ?x ?y ?z ?r ?g ?b
FROM <{graph}>
WHERE {{
?p 	urban:X ?x;
	urban:Y ?y;
	urban:Z ?z;
	urban:R ?r;
	urban:G ?g;
	urban:B ?b.
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
	urban:Z ?z;
	urban:R ?r;
	urban:G ?g;
	urban:B ?b.
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