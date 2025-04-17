from SPARQLWrapper import TURTLE
from urllib.parse import urlparse
import numpy as np
from time import time

from .turtle_parse import SPARQLWrapperWithTurtle as SPARQLWrapper
from .queries import *

class SparqlEndpoint:
    def __init__(self, url, namespace):
        self.graph = url
        if namespace.endswith('#'):
            self.namespace = namespace
        else:
            self.namespace = namespace + "#"
        parsed = urlparse(url)
        # TODO generalize outside of virtuoso
        self.endpoint= parsed.scheme + "://" + parsed.netloc + "/sparql"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(TURTLE)
        self.iri_to_id = {}
        self.id_to_iri = []
        self.colors = None

    def get_all(self):
        query = SELECT_ALL_QUERY.format(graph=self.graph, namespace=self.namespace)
        self.sparql.setQuery(query)
        start = time()
        results = self.sparql.queryAndConvert()
        print("Time to query: ", time() - start)
        start = time()

        coords = np.array((results['x'], results['y'], results['z'])).T.astype(np.float32)
        colors = np.array((results['r'], results['g'], results['b'])).T.astype(np.float32)
        self.iri_to_id = {p: i for i, p in enumerate(results['p'])}
        self.id_to_iri = results['p']

        if colors.max() > 255:
            colors = colors / (1<<16) # 16 bit color
        else:
            colors = colors / (1<<8) # 8 bit color
        self.colors = colors
        print("Time to process query result: ", time() - start)
        return coords, colors

    # returns the colors with highlighted points
    def execute_select_query(self, where_clause):
        query = FILTER_QUERY.format(graph=self.graph, filter=where_clause, namespace=self.namespace)
        self.sparql.setQuery(query)
        try:
            results = self.sparql.queryAndConvert()
        except Exception as e:
            print("Error executing query: ", e)
            return self.colors

        colors = np.copy(self.colors)
        for p in results['p']:
            try:
                i = self.iri_to_id[p]
            except KeyError:
                print("Point not found: ", p)
                # This happens every time, it's a mistery for me why, probably virtuoso is misconfigured or something
                continue
            colors[i] = [1.0, 0.0, 0.0] # TODO make this a parameter

        return colors

    def execute_scalar_query(self, query):
        self.sparql.setQuery(query)
        results = self.sparql.queryAndConvert()
        if 's' not in results:
            # assume empty result
            return None

        scalars = np.empty(len(self.colors), dtype=np.float32)
        for subject, scalar in zip(results['s'], results['x']):
            try:
                i = self.iri_to_id[subject]
            except KeyError:
                print("Point not found: ", subject)
                # This happens every time, it's a mistery for me why, probably virtuoso is misconfigured or something
                continue
            scalars[i] = scalar

        return scalars


    def get_point_iri(self, point_id):
        return self.id_to_iri[point_id]

    def get_node_details(self, iri):
        query = GET_NODE_DETAILS.format(graph=self.graph, point=iri, namespace=self.namespace)
        self.sparql.setQuery(query)
        results = self.sparql.queryAndConvert()

        if 'p' not in results or 'o' not in results:
            # assume empty result
            return []

        out = list(zip(results['p'], results['o']))

        return out


if __name__ == "__main__":
    sparql = SparqlEndpoint("http://localhost:8890/Nettuno")
    sparql.sparql.setReturnFormat(TURTLE)
    sparql.get_all()
    details = sparql.get_point_details(0)
    print(details)
    # coords, colors = sparql.get_all()
    # print(len(coords))
    # print(coords)