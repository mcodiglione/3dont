from SPARQLWrapper import SPARQLWrapper, JSON, TURTLE
from urllib.parse import urlparse
import numpy as np
import re
from time import time

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

VARIABLE_REGEX = re.compile(r"res:binding\s*\[\s*res:variable\s*\"([a-z]+)\"\s*;\s*res:value\s*(\S+)\s*\]")
def parse_turtle_select(turtle):
    results = {}
    parsed = VARIABLE_REGEX.findall(turtle)
    for var, value in parsed:
        if var not in results:
            results[var] = []
        results[var].append(value)

    return results

class SparqlEndpoint:
    def __init__(self, url):
        self.graph = url
        parsed = urlparse(url)
        # TODO generalize outside of virtuoso
        self.endpoint= parsed.scheme + "://" + parsed.netloc + "/sparql"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(TURTLE)
        self.iri_to_id = {}
        self.id_to_iri = []
        self.colors = None

    def get_all(self):
        query = SELECT_ALL_QUERY.format(graph=self.graph)
        self.sparql.setQuery(query)
        start = time()
        results = self.sparql.queryAndConvert().decode()
        print("Time to query: ", time() - start)
        start = time()
        results = parse_turtle_select(results)
        print("Time to parse query result: ", time() - start)
        start = time()

        coords = np.array((results['x'], results['y'], results['z'])).T.astype(np.float32)
        colors = np.array((results['r'], results['g'], results['b'])).T.astype(np.float32)
        self.iri_to_id = {p: i for i, p in enumerate(results['p'])}
        self.id_to_iri = results['p']

        colors = colors / (1<<16)
        self.colors = colors
        print("Time to process query result: ", time() - start)
        return coords, colors

    # returns the colors with highlighted points
    def execute_select_query(self, where_clause):
        query = FILTER_QUERY.format(graph=self.graph, filter=where_clause)
        self.sparql.setQuery(query)
        try:
            results = self.sparql.queryAndConvert().decode()
        except Exception as e:
            print("Error executing query: ", e)
            return self.colors
        results = parse_turtle_select(results)
        colors = np.copy(self.colors)
        for p in results['p']:
            try:
                i = self.iri_to_id[p]
            except KeyError:
                print("Point not found: ", p)
                # This happens every time, it's a mistery for me why, probably virtuoso is misconfigured or something
                continue
            colors[i] = [1.0, 0.0, 0.0]

        return colors

if __name__ == "__main__":
    sparql = SparqlEndpoint("http://localhost:8890/Nettuno")
    sparql.sparql.setReturnFormat(TURTLE)
    coords, colors = sparql.get_all()
    print(len(coords))
    # print(coords)