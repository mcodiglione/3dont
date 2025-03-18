from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.parse import urlparse
import numpy as np

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
	urban:Z ?z.
	{filter}
}}
"""

class SparqlEndpoint:
    def __init__(self, url):
        self.graph = url
        parsed = urlparse(url)
        # TODO generalize outside of virtuoso
        self.endpoint= parsed.scheme + "://" + parsed.netloc + "/sparql"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(JSON)
        self.iri_to_id = {}
        self.id_to_iri = []
        self.colors = None

    def get_all(self):
        query = SELECT_ALL_QUERY.format(graph=self.graph)
        self.sparql.setQuery(query)
        results = self.sparql.queryAndConvert()
        results = results['results']['bindings']
        self.iri_to_id = {}
        self.id_to_iri = [0] * len(results)
        colors = np.empty((len(results), 3), dtype=np.float32)
        coords = np.empty((len(results), 3), dtype=np.float32)
        for i, result in enumerate(results):
            self.iri_to_id[result['p']['value']] = i
            self.id_to_iri[i] = result['p']['value']
            coords[i] = [float(result['x']['value']), float(result['y']['value']), float(result['z']['value'])]
            colors[i] = [float(result['r']['value']), float(result['g']['value']), float(result['b']['value'])]

        colors = colors / (1<<16)
        self.colors = colors
        return coords, colors

    # returns the colors with highlighted points
    def execute_select_query(self, where_clause):
        query = FILTER_QUERY.format(graph=self.graph, filter=where_clause)
        self.sparql.setQuery(query)
        try:
            results = self.sparql.queryAndConvert()
        except Exception as e:
            print("Error executing query: ", e)
            return self.colors
        results = results['results']['bindings']
        colors = np.copy(self.colors)
        for result in results:
            try:
                i = self.iri_to_id[result['p']['value']]
            except KeyError:
                print("Point not found: ", result['p']['value'])
                continue
            colors[i] = [1.0, 0.0, 0.0]

        return colors

if __name__ == "__main__":
    sparql = SparqlEndpoint("http://localhost:8890/Nettuno")
    coords, colors = sparql.get_all()
    print(coords)