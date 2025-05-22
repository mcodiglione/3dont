SELECT_ALL_QUERY = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?p ?x ?y ?z 
       (COALESCE(?r, 0) AS ?r) 
       (COALESCE(?g, 0) AS ?g) 
       (COALESCE(?b, 0) AS ?b)
FROM <{graph}>
WHERE {{
    ?p base:X ?x;
        base:Y ?y;
        base:Z ?z.
    OPTIONAL {{
        ?p base:R ?r.
        ?p base:G ?g.
        ?p base:B ?b.
    }}
}}
"""

PREDICATE_QUERY = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?s ?x
FROM <{graph}>
WHERE {{
    ?s {predicate} ?x.
}}
"""

# get all the predicates and objects of a point, given its id
GET_NODE_DETAILS = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p ?o
FROM <{graph}>
WHERE {{
{point} ?p ?o.
FILTER (?p != base:Is_constituted_by)
}}
ORDER BY ?o
"""

SELECT_ALL_WITH_PREDICATE = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT ?p
FROM <{graph}>
WHERE {{
    ?p {predicate} {object}.
}}
"""

# insert a triple with subject, predicate and object
ANNOTATE_NODE = """
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
INSERT DATA
{{
    GRAPH <{graph}> {{
        {subject} {predicate} {object}.
    }}
}}
"""

# sample scalar
"""
PREFIX base:<{namespace}>
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
PREFIX base:<{namespace}>
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

# sample table (avg x, avg y, avg z)
"""
PREFIX base:<{namespace}>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT (AVG(?x) AS ?avg_x) (AVG(?y) AS ?avg_y) (AVG(?z) AS ?avg_z)
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
