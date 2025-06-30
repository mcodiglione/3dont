from time import time
from urllib.parse import urlparse

import numpy as np
from SPARQLWrapper import TURTLE

from .queries import *
from .turtle_parse import SPARQLWrapperWithTurtle as SPARQLWrapper

TEST_FAST = False  # remove true before commit
CHUNK_SIZE = 1000000 if not TEST_FAST else 1000
HIGHLIGHT_COLOR = [1.0, 0.0, 0.0]  # TODO make this a parameter


class WrongResultFormatException(Exception):
    def __init__(self, expected, got):
        message = f"Expected {expected}, but got {got}"
        super().__init__(message)


class EmptyResultSetException(Exception):
    def __init__(self, query):
        message = f"Empty result set for query: {query}"
        super().__init__(message)


class SparqlEndpoint:
    def __init__(self, graph_uri, db_url, namespace):
        self.graph = graph_uri
        if namespace.endswith('#'):
            self.namespace = namespace
        else:
            self.namespace = namespace + "#"
        # TODO generalize outside of virtuoso
        self.endpoint = db_url + "/sparql"
        self.sparql = SPARQLWrapper(self.endpoint)
        self.sparql.setReturnFormat(
            TURTLE)  # works with virtuoso even if the header sent is accept */* (RuntimeWarning)
        self.iri_to_id = {}
        self.coords_to_id = {}
        self.id_to_iri = []
        self.colors = None

    def _execute_chunked_query(self, query):
        offset = 0
        all_results = {}
        while True:
            chunked_query = query + " OFFSET " + str(offset) + " LIMIT " + str(CHUNK_SIZE)
            self.sparql.setQuery(chunked_query)
            results = self.sparql.queryAndConvert()
            for key in results.keys():
                if key not in all_results:
                    all_results[key] = []
                all_results[key].extend(results[key])

            if len(results) == 0:
                print(results)
                raise EmptyResultSetException(query)

            any_key = next(iter(results.keys()))
            if len(results[any_key]) < CHUNK_SIZE:
                break
            if TEST_FAST:
                break
            offset += CHUNK_SIZE
        return all_results

    def get_all(self):
        query = SELECT_ALL_QUERY.format(graph=self.graph, namespace=self.namespace)
        start = time()
        results = self._execute_chunked_query(query)
        print("Time to query: ", time() - start)
        start = time()

        # fix values in form '"2.48e-05"^^xsd:decimal'
        for k, v in results.items():
            for i, x in enumerate(v):
                if x.endswith('^^xsd:decimal'):
                    v[i] = x.split('"')[1]

        coords = np.array((results['x'], results['y'], results['z'])).T.astype(np.float32)
        colors = np.array((results['r'], results['g'], results['b'])).T.astype(np.float32)
        self.iri_to_id = {p: i for i, p in enumerate(results['p'])}
        self.coords_to_id = {tuple(c): i for i, c in enumerate(coords)}
        self.id_to_iri = results['p']

        if colors.max() > 255:
            colors = colors / (1 << 16)  # 16 bit color
        else:
            colors = colors / (1 << 8)  # 8 bit color
        self.colors = colors
        print("Time to process query result: ", time() - start)
        return coords, colors

    # returns the colors with highlighted points
    def execute_select_query(self, query):
        results = self._execute_chunked_query(query)

        colors = np.copy(self.colors)
        if not 'p' in results:
            raise WrongResultFormatException(['p'], list(results.keys()))

        for p in results['p']:
            try:
                i = self.iri_to_id[p]
            except KeyError:
                continue  # not all the results of a select are points
            colors[i] = HIGHLIGHT_COLOR

        return colors

    def execute_scalar_query(self, query):
        results = self._execute_chunked_query(query)
        if not 's' in results or not 'x' in results:
            raise WrongResultFormatException(['s', 'x'], list(results.keys()))

        minimum = float(min(results['x']))
        maximum = float(max(results['x']))
        # print(minimum, maximum)
        default = minimum - (maximum - minimum) / 10
        # scalars = np.empty(len(self.colors), dtype=np.float32)
        scalars = np.full(len(self.colors), default, dtype=np.float32)
        for subject, scalar in zip(results['s'], results['x']):
            i = self.iri_to_id[subject]
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

    def execute_predicate_query(self, predicate):
        query = PREDICATE_QUERY.format(graph=self.graph, predicate=predicate, namespace=self.namespace)
        return self.execute_scalar_query(query)

    def annotate_node(self, subject, predicate, object):
        query = ANNOTATE_NODE.format(graph=self.graph, subject=subject, predicate=predicate, object=object,
                                     namespace=self.namespace)
        self.sparql.setQuery(query)
        self.sparql.query()

    def select_all_subjects(self, predicate, object):
        query = SELECT_ALL_WITH_PREDICATE.format(graph=self.graph, predicate=predicate, object=object,
                                                 namespace=self.namespace)
        iris = self._execute_chunked_query(query)['p']
        colors = np.copy(self.colors)
        for p in iris:
            try:
                i = self.iri_to_id[p]
            except KeyError:
                continue  # not all the results of a select are points
            colors[i] = [1.0, 0.0, 0.0]
        return colors

    def raw_query(self, query):
        return self._execute_chunked_query(query)

    def autodetect_query_nl(self, query):
        # TODO refactor
        result = self._execute_chunked_query(query)
        columns = list(result.keys())
        if 'x1' in columns and 'y1' in columns and 'z1' in columns:
            # select query
            colors = np.copy(self.colors)
            coords = np.array((result['x1'], result['y1'], result['z1'])).T.astype(np.float32)
            for coord in coords :
                try:
                    i = self.coords_to_id[tuple(coord)]
                except KeyError:
                    continue  # not all the results of a select are points
                colors[i] = [1.0, 0.0, 0.0]
                return colors, "select"

        if 'x1' in columns and 'y1' in columns and 'z1' in columns:
            minimum = float(min(result['x1']))
            maximum = float(max(result['x1']))
            default = minimum - (maximum - minimum) / 10
            scalars = np.full(len(self.colors), default, dtype=np.float32)
            coords = np.array((result['x1'], result['y1'], result['z1'])).T.astype(np.float32)
            for coord, scalar in zip(coords, result['x1']):
                i = self.coords_to_id[tuple(coord)]
                scalars[i] = scalar
            return scalars, "scalar"

        return result, "tabular"