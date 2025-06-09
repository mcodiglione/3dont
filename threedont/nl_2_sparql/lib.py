import owlready2 as owl2
import rdflib
import networkx as nx
import re
import openai
import itertools

def init_client():
    client = openai.OpenAI()
    return client


def parse_wordlist(ontology_schema):
    parsed_schema = parse_ontology_schema(ontology_schema)
    wordlist = ""
    type_dict = {
        "0": "noun",
        "1": "property",
        "2": "relationship",
        "3": "noun",
    }
    for index, list in enumerate(parsed_schema):
        for word in list:
            if any(x in word for x in ["_", " ", "-"]):
                ind = str(index)
                wordlist += f"{word}-{type_dict[ind]}, "

    return wordlist


def gpt_process_query_with_wordlist(query, client, annotated_words):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You will receive a natural language query by the user. you just have to parse it. do not say anything else. Also, i'll attach a list of words in a word-type format, delimited by XML tags. use this for two tasks: (1) in case of multi-word expressions in the input query, if you find them (or something very similar) in the list as unique words, then consider them as such in the parsing, if they are not on the list, then consider them as different expressions; (2) if you are unsure of the type - noun, property or relationship - of some words, check on the list. <LIST> "
                           + f"{annotated_words}"
                           + " </LIST>",
            },
            {"role": "user", "content": f"{query}"},
        ],
        model="ft:gpt-4o-mini-2024-07-18:3dont:nl-2-sparql:AsqpMGPB",
        max_tokens=1000,
        seed=42,
    )
    return response.choices[0].message.content


def gpt_process_query_no_wordlist(query, client):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You will receive a natural language query by the user. you just have to parse it. do not say anything else.",
            },
            {"role": "user", "content": f"{query}"},
        ],
        model="ft:gpt-4o-mini-2024-07-18:3dont:nl-2-sparql:AsqpMGPB",
        max_tokens=1000,
        seed=42,
    )
    return response.choices[0].message.content


########## here post LLM parsing ###########


def add_commas_and_quotes(parsed_query):
    parsed_query = parsed_query.replace("]\n[", "],\n[")
    parsed_query = parsed_query.replace("] \n[", "],\n[")
    pattern = r"(?<!\[Non)(?<!\sNon)([a-zA-Z0-9])(?=[,\]])"
    parsed_query = re.sub(pattern, r"\1'", parsed_query)
    return parsed_query


def remove_point_classes(ontology_schema, class_list):
    classes_to_be_removed = []
    for cl in class_list:
        if cl != ontology_schema.Points.name:
            if cl in [cl.name for cl in list(ontology_schema.Points.descendants())]:
                classes_to_be_removed.append(cl)
    for cl in classes_to_be_removed:
        class_list.remove(cl)
    return class_list


def parse_ontology_schema(
        ontology_schema,
):  # it expects an already loaded ontology object. it returns a list of lists containing the string names of the various resources of the ontology schema

    class_list = [x.name for x in ontology_schema.classes()]
    class_list = remove_point_classes(ontology_schema, class_list)
    data_prop_list = [x.name for x in ontology_schema.data_properties()]
    relationships_list = [x.name for x in ontology_schema.object_properties()]
    individuals_list = [x.name for x in ontology_schema.individuals()]

    return [class_list, data_prop_list, relationships_list, individuals_list]


"""parsed query L1 structure:
    [[root word,[closest neighborood]],
    [root word,[closest neighborood]],
    ...]
    """


def ask_user_for_confirmation(mapping_dict, parsed_ontology_schema, type_dict):
    window = tk.Toplevel()
    window.title("Mapping executed")
    subtitle = tk.Label(
        window,
        text="Check the mapping and adjust if needed, then press ok",
        font=("Arial", 14, "italic"),
    )
    subtitle.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    final_mapping_dict = {}
    dropdowns = {}

    # Iterate through the dictionary to create labels and dropdowns
    for index, (key, default_value) in enumerate(mapping_dict.items()):
        # Label for the key
        label = tk.Label(window, text=key)
        label.grid(row=index + 1, column=0, padx=10, pady=5)

        parsed_ontology_schema_merged = [
            item for sublist in parsed_ontology_schema for item in sublist
        ]

        # Dropdown menu for the value associated with the key
        dropdown = ttk.Combobox(window, values=parsed_ontology_schema_merged)
        dropdown.set(default_value[0])  # Set the default value
        dropdown.grid(row=index + 1, column=1, padx=10, pady=5)
        dropdowns[key] = dropdown

    def on_ok():
        for word, var in dropdowns.items():
            mapped_word = var.get()
            for index, l in enumerate(parsed_ontology_schema):
                if mapped_word in l and mapped_word != "":
                    final_mapping_dict[word] = [mapped_word, type_dict[str(index)]]
        window.destroy()  # Close the sub-window

    ok_button = tk.Button(window, text="OK", command=on_ok)
    ok_button.grid(
        row=index + 2,
        column=0,
        columnspan=2,
        pady=10,
    )
    window.wait_window()

    return final_mapping_dict


def ask_user_for_manual_mapping(unmapped_list, parsed_ontology_schema, type_dict):
    mapping_result = {}
    sub_window = tk.Toplevel()
    sub_window.title("Manual Mapping")

    # Configure the grid
    sub_window.grid_columnconfigure(0, weight=1)
    sub_window.grid_columnconfigure(1, weight=1)

    # Add headers
    tk.Label(sub_window, text="Unmapped Words", font=("Arial", 12, "bold")).grid(
        row=0, column=0, padx=10, pady=10
    )
    tk.Label(sub_window, text="Mapped To", font=("Arial", 12, "bold")).grid(
        row=0, column=1, padx=10, pady=10
    )

    # Create a dictionary to store the dropdown menus
    dropdown_vars = {}

    # Populate the sub-window with unmapped words and dropdown menus
    for idx, word in enumerate(unmapped_list):
        # Label for the unmapped word
        tk.Label(sub_window, text=word, font=("Arial", 10)).grid(
            row=idx + 1, column=0, padx=10, pady=5, sticky="w"
        )

        parsed_ontology_schema_merged = [
            item for sublist in parsed_ontology_schema for item in sublist
        ]

        # Dropdown menu for the mapped words
        var = tk.StringVar(value="")  # Default value is empty
        dropdown = ttk.Combobox(
            sub_window, textvariable=var, values=parsed_ontology_schema_merged
        )
        dropdown.grid(row=idx + 1, column=1, padx=10, pady=5, sticky="ew")
        dropdown_vars[word] = var  # Store the variable for later retrieval

    # OK button to finalize the mapping
    def on_ok():
        for word, var in dropdown_vars.items():
            mapped_word = var.get()
            for index, l in enumerate(parsed_ontology_schema):
                if mapped_word in l and mapped_word != "":
                    mapping_result[word] = [mapped_word, type_dict[str(index)]]
        sub_window.destroy()  # Close the sub-window

    ok_button = tk.Button(sub_window, text="OK", command=on_ok)
    ok_button.grid(row=len(unmapped_list) + 1, column=0, columnspan=2, pady=10)
    sub_window.wait_window()
    return mapping_result


def map_query(parsed_query, parsed_ontology_schema, base):  # base is a namespace object
    from nltk.corpus import wordnet as wn
    import editdistance as ed
    from jarowinkler import jarowinkler_similarity

    unmapped_list = []
    string_filters_dict = (
        {}
    )  # this will use the unmapped_root_word as key and the name of the property of which it is the string value filter as element
    mapping_dict = (
        {}
    )  # this will use the root_word as key to reach a list with the ont_word as first element and the word type as second
    type_dict = {
        "0": "class",
        "1": "data_property",
        "2": "relationship",
        "3": "individual",
    }
    # L1 mapping
    for word_row in parsed_query[0]:
        root_word = word_row[0]
        map_flag = False
        # exact match try
        index = 0
        for word_list in parsed_ontology_schema:
            if map_flag == False:
                for word in word_list:
                    if word.lower() == root_word.lower():
                        map_flag = True
                        mapping_dict[root_word] = [word, type_dict[str(index)]]
                        break
                index += 1
        # wordnet syn list generation
        if map_flag == False:
            synonyms = set()  # Using a set to avoid duplicate synonyms
            for syn in wn.synsets(root_word):
                for lemma in syn.lemmas():
                    synonyms.add(lemma.name())  # Add each synonym to the set
            synonyms = list(synonyms)

            # wordnet exact match try
            for syn in synonyms:
                index = 0
                for word_list in parsed_ontology_schema:
                    if map_flag == False:
                        for word in word_list:
                            if word.lower() == root_word.lower():
                                map_flag = True
                                mapping_dict[root_word] = [word, type_dict[str(index)]]
                                break
                    index += 1
                if map_flag == True:
                    break
            # root_word edit distance and jaro_winkler
            if map_flag == False:
                index = 0
                for word_list in parsed_ontology_schema:
                    for ont_word in word_list:
                        ed_score = ed.eval(root_word.lower(), ont_word.lower())
                        max_len = max(len(root_word), len(ont_word))
                        normalized_ed_score = 1 - (ed_score / max_len)
                        jw_score = jarowinkler_similarity(
                            root_word.lower(), ont_word.lower()
                        )
                        average_score = (normalized_ed_score + jw_score) / 2
                        threshold = 0.8
                        if average_score >= threshold:
                            map_flag = True
                            mapping_dict[root_word] = [ont_word, type_dict[str(index)]]
                            break
                    if map_flag == True:
                        break
                    index += 1
                if map_flag == False:
                    # syn edit distance and jaro_winkler
                    for syn in synonyms:
                        index = 0
                        for word_list in parsed_ontology_schema:
                            for ont_word in word_list:
                                ed_score = ed.eval(syn.lower(), ont_word.lower())
                                max_len = max(len(syn), len(ont_word))
                                normalized_ed_score = 1 - (ed_score / max_len)
                                jw_score = jarowinkler_similarity(
                                    syn.lower(), ont_word.lower()
                                )
                                average_score = (normalized_ed_score + jw_score) / 2
                                threshold = 0.85
                                if average_score >= threshold:
                                    map_flag = (True,)
                                    mapping_dict[root_word] = [
                                        ont_word,
                                        type_dict[str(index)],
                                    ]
                                    break
                            if map_flag == True:
                                break
                            index += 1
                        if map_flag == True:
                            break
                    if map_flag == False:
                        unmapped_list.append(root_word)
        """                     # gensim init
                        model = api.load("glove-wiki-gigaword-300")

                        # gensim try on root word
                        index = 0
                        for word_list in parsed_ontology_schema:
                            for ont_word in word_list:
                                if root_word in model and ont_word in model:
                                    gensim_score = model.similarity(
                                        root_word.lower(), ont_word.lower()
                                    )
                                    if gensim_score >= 0.85:
                                        map_flag = True
                                        mapping_dict[root_word] = [
                                            ont_word,
                                            type_dict[str(index)],
                                        ]
                                        break
                            if map_flag == True:
                                break
                            index += 1
                            if map_flag == False:
                                # gensim try on synonyms
                                for syn in synonyms:
                                    index = 0
                                    for word_list in parsed_ontology_schema:
                                        for ont_word in word_list:
                                            if syn in model and ont_word in model:
                                                gensim_score = model.similarity(
                                                    syn.lower(), ont_word.lower()
                                                )
                                                if gensim_score >= 0.85:
                                                    map_flag = True
                                                    mapping_dict[root_word] = [
                                                        ont_word,
                                                        type_dict[str(index)],
                                                    ]
                                                    break
                                        if map_flag == True:
                                            break
                                        index += 1
                                    if map_flag == True:
                                        break
                                # adding to unmapped_list
                                if map_flag == False:
                                    unmapped_list.append(root_word)
        """
    # here i have a mapping_dict and an unmapped_list
    if len(unmapped_list) != 0:
        for unmapped_word in unmapped_list:
            for word_row in parsed_query[0]:
                if unmapped_word == word_row[0]:
                    closest_neighborood = word_row[1]
                    for neighbor in closest_neighborood:
                        if neighbor in mapping_dict.keys():
                            neighbor_type = mapping_dict[neighbor][1]
                            if neighbor_type == "data_property":
                                prop = getattr(base, mapping_dict[neighbor][0])
                                if str in prop.range:
                                    string_filters_dict[unmapped_word] = prop.name
                                    unmapped_list.remove(unmapped_word)

    if len(unmapped_list) != 0:
        print(
            f"impossible to map the following words: {unmapped_list}, neither directly nor as string filter for data property which range over strings."
        )
        # request to the user for a manual mapping
        unmapped_mapping_dict = ask_user_for_manual_mapping(
            unmapped_list, parsed_ontology_schema, type_dict
        )
        mapping_dict = mapping_dict | unmapped_mapping_dict

    confirmed_mapping_dict = ask_user_for_confirmation(
        mapping_dict, parsed_ontology_schema, type_dict
    )

    # here i have a mapping_dict and a string_filters_dict (can be empty).
    # ML1 generation
    ml1 = []
    for root_word in confirmed_mapping_dict.keys():
        mapped_word = confirmed_mapping_dict[root_word][0]
        mapped_word_type = confirmed_mapping_dict[root_word][1]
        mapped_neighborood = []
        for word_row in parsed_query[0]:
            if root_word == word_row[0]:
                closest_neighborood = word_row[1]
                for neighbor in closest_neighborood:
                    if neighbor in confirmed_mapping_dict.keys():
                        mapped_neighborood.append(confirmed_mapping_dict[neighbor][0])
        ml1.append([mapped_word, mapped_neighborood, mapped_word_type])

    # ML2
    """L2 previous shape:
        [occurrence, relative_root_word, closest neighborood (occurrences), [subject, object](completely filled just for relationships while [subject, none] for properties)]
        """
    # ML2
    for row in parsed_query[1]:
        if row[1] in confirmed_mapping_dict.keys():
            row[1] = confirmed_mapping_dict[row[1]][0]
        for neighbor in row[2]:
            if (
                    neighbor in confirmed_mapping_dict.keys()
            ):  # se il neighbor è una root word e non un'occurrence
                row[2] = [
                    confirmed_mapping_dict[neighbor] if n == neighbor else n
                    for n in row[2]
                ]
    for row in parsed_query[1]:
        for roww in ml1:
            if roww[0] == row[1]:
                if (
                        roww[2] == "relationship"
                ):  # substituting root words to occurrences in the subject-object field of relationships if they are individuals occurrences
                    subject = row[3][0]
                    object = row[3][1]
                    for rowww in parsed_query[1]:
                        if rowww[0] == subject:
                            for rowwww in ml1:
                                if rowwww[0] == rowww[1]:
                                    if rowwww[2] == "individual":
                                        row[3][0] = rowwww[0]
                        if rowww[0] == object:
                            for rowwww in ml1:
                                if rowwww[0] == rowww[1]:
                                    if rowwww[2] == "individual":
                                        row[3][1] = rowwww[0]
        for index, neighbor in enumerate(row[2]):  # same but for all neighborhoods
            neighbor_flag = False
            for r in parsed_query[1]:
                if neighbor_flag == True:
                    break
                if r[0] == neighbor:
                    neighbor_flag = True
                    for ro in ml1:
                        if ro[0] == r[1]:
                            if ro[2] == "individual":
                                row[2][index] = r[1]
                            else:
                                break
    for roww in ml1:
        for row in parsed_query[1]:
            if roww[0] == row[1]:
                if roww[2] == "individual":  # same but for ML2 first column
                    row[0] = roww[0]
                    break

    # ML4
    # substituting individuals in ML4 in case of identity/difference filters
    for row in parsed_query[3]:
        if len(row[1]) == 2:
            for index, comparatum in enumerate(row[1]):
                if comparatum in confirmed_mapping_dict.keys():
                    comparatum = re.sub(r"\d+$", "", comparatum)
                    if confirmed_mapping_dict[comparatum][1] == "individual":
                        row[1][index] = confirmed_mapping_dict[comparatum][0]

    # here, in the case of string filters (like "day" for "temperature with a "day" tag")
    for key in string_filters_dict.keys():
        for row in parsed_query[1]:
            if row[1] == string_filters_dict[key]:
                for occ in row[2]:
                    if key == occ:
                        parsed_query[3].append([f"={key}", f"{occ}"])

    # ML3,5 are not updated, since they directly refer to the occurrences and are used in a pipeline stage in which the occurrences are already attributed to the relative root words in the subgraph

    return [
        ml1,
        parsed_query[1],
        parsed_query[2],
        parsed_query[3],
        parsed_query[4],
        string_filters_dict,
    ]


def get_local_name(uri):
    """Extract the local name from a URI."""
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]


def is_standard_namespace(uri):
    return (
            str(uri).startswith(str(rdflib.namespace.RDF))
            or str(uri).startswith(str(rdflib.namespace.RDFS))
            or str(uri).startswith(str(rdflib.namespace.OWL))
    )


def onto_to_graph(
        ont_schema_path,
):  # prende un file rdf e ne restituisce un grafo completo in cui le prop e gli individui sono nodi
    # Load the RDF file using rdflib
    g = rdflib.Graph()
    g.parse(ont_schema_path, format="application/rdf+xml")  # Adjust format as needed

    # Define namespaces (example with RDF and RDFS)
    RDF = rdflib.namespace.RDF
    RDFS = rdflib.namespace.RDFS

    # Define standard properties that should be treated as edges
    standard_properties = {
        RDF.type,
        RDFS.domain,
        RDFS.range,
        RDFS.subPropertyOf,
        RDFS.subClassOf,
    }

    # Initialize an empty NetworkX graph
    G = nx.DiGraph()

    # Iterate through RDF triples
    for subj, pred, obj in g:
        # Skip nodes and edges if they belong to RDF or RDFS namespaces
        if is_standard_namespace(subj) or is_standard_namespace(obj):
            subj_name = get_local_name(subj)
            pred_name = get_local_name(pred)
            obj_name = get_local_name(obj)
            print(f"discarded standard triple:{subj_name},{pred_name},{obj_name}")
            continue
        # Get local names for the subject, predicate, and object
        subj_name = get_local_name(subj)
        pred_name = get_local_name(pred)
        obj_name = get_local_name(obj)
        print(f"considering triple:{subj_name},{pred_name},{obj_name}")

        if pred in standard_properties:
            # Add nodes with local names and treat standard properties as edges
            if subj_name not in G:
                G.add_node(subj_name, label=subj_name)
            if obj_name not in G:
                G.add_node(obj_name, label=obj_name)
            G.add_edge(subj_name, obj_name, label=pred_name)
            print(f"added triple:{subj_name},{pred_name},{obj_name}")

        else:
            print(f"ignored triple:{subj_name},{pred_name},{obj_name}")

    """
    pos = nx.spring_layout(G)
    nx.draw(
        G, pos, with_labels=True, font_size=8, node_size=500, node_color="lightblue"
    )
    nx.draw_networkx_edge_labels(G, pos, edge_labels=nx.get_edge_attributes(G, "label"))
    plt.show()"""

    return G


def node_to_edges(path):
    edge_path = []
    for i in range(0, len(path) - 1):
        edge = (path[i], path[i + 1])
        edge_path.append(edge)
    return edge_path


def generate_query_subgraph(ML1, full_graph):
    nodes_set = set()
    undirected_G = full_graph.to_undirected()
    # for each root word, generate the shortest path from it to all its neighbors. this way should be semantically more reasonable. filtering to avoid paths with range-range or domain-domain nodes
    for row in ML1:
        if len(row[1]) == 0:
            nodes_set.add(row[0])
        for neighbor in row[1]:
            paths_list = list(
                itertools.islice(
                    nx.shortest_simple_paths(
                        undirected_G, source=row[0], target=neighbor
                    ),
                    10,  # DA TESTARE; MAGARI è TROPPO PICCOLO
                )
            )
            # filtering
            paths_to_be_removed = []
            paths_list = [node_to_edges(path) for path in paths_list]
            for path in paths_list:
                for index, (n1, n2) in enumerate(path):
                    if undirected_G.has_edge(n1, n2):
                        edge_label = undirected_G[n1][n2].get("label", "unknown")
                        if edge_label == "domain":
                            if len(path) >= index + 2:
                                new_couple = path[index + 1]
                                if undirected_G.has_edge(new_couple[0], new_couple[1]):
                                    new_edge_label = undirected_G[new_couple[0]][
                                        new_couple[1]
                                    ].get("label", "unknown")
                                    if new_edge_label == "domain":
                                        paths_to_be_removed.append(path)
                                        break
                        if edge_label == "range":
                            if len(path) >= index + 2:
                                new_couple = path[index + 1]
                                if undirected_G.has_edge(new_couple[0], new_couple[1]):
                                    new_edge_label = undirected_G[new_couple[0]][
                                        new_couple[1]
                                    ].get("label", "unknown")
                                    if new_edge_label == "range":
                                        paths_to_be_removed.append(path)
                                        break
            paths = []
            for path in paths_list:
                if path not in paths_to_be_removed:
                    paths.append(path)
            shortest_path = min(paths, key=len)
            for couple in shortest_path:
                nodes_set.add(couple[0])
                nodes_set.add(couple[1])

    query_subgraph = full_graph.subgraph(nodes_set).copy()
    if nx.is_weakly_connected(query_subgraph):
        """
        pos = nx.spring_layout(query_subgraph)
        nx.draw(
            query_subgraph,
            pos,
            with_labels=True,
            font_size=8,
            node_size=500,
            node_color="lightblue",
        )
        nx.draw_networkx_edge_labels(
            query_subgraph,
            pos,
            edge_labels=nx.get_edge_attributes(query_subgraph, "label"),
        )
        plt.ioff()
        plt.show()
        """
        return query_subgraph

    else:  # if subgraph is not connected, generate it again not conisdering neighbors but only root words and with just shortest path
        starting_nodes_list = []
        subgraph_node_set = set()
        for row in ML1:
            starting_nodes_list.append(row[0])
        for i in range(len(starting_nodes_list)):
            source_node = starting_nodes_list.pop(0)
            for other_node in starting_nodes_list:
                path_nodes_list = nx.shortest_path(
                    undirected_G, source=source_node, target=other_node
                )
                for node in path_nodes_list:
                    subgraph_node_set.add(node)
        query_subgraph = full_graph.subgraph(subgraph_node_set).copy()
        if nx.is_weakly_connected(query_subgraph):
            """
            pos = nx.spring_layout(query_subgraph)
            nx.draw(
                query_subgraph,
                pos,
                with_labels=True,
                font_size=8,
                node_size=500,
                node_color="lightblue",
            )
            nx.draw_networkx_edge_labels(
                query_subgraph,
                pos,
                edge_labels=nx.get_edge_attributes(query_subgraph, "label"),
            )
            plt.ioff()
            plt.show()
            """
            return query_subgraph
        else:
            print("no way to get a connected subgraph")
            return None


def class_occurrence_generation(query_subgraph, ML1, ML2):  # ML2 is parsed_query[1]
    for occurrence_row in ML2:
        root_word = occurrence_row[1]
        occurrence = occurrence_row[0]
        for root_row in ML1:
            if root_row[0] == root_word:
                if root_row[2] == "class":
                    query_subgraph.add_node(f"?{occurrence}", label=f"?{occurrence}")
                    query_subgraph.add_edge(f"?{occurrence}", root_word, label="type")
                    break
    """
    pos = nx.spring_layout(query_subgraph)
    nx.draw(
        query_subgraph,
        pos,
        with_labels=True,
        font_size=8,
        node_size=500,
        node_color="lightblue",
    )
    nx.draw_networkx_edge_labels(
        query_subgraph,
        pos,
        edge_labels=nx.get_edge_attributes(query_subgraph, "label"),
    )
    plt.ioff()
    plt.show()
    """
    return query_subgraph


def remove_path_with_dome_issues(
        directed_paths,
):  # IMPEDIRE <- -> per subclass of, ossia impedire path che prevedono “cupole” nel muoversi tra le classi.
    path_to_be_removed = []
    for path in directed_paths:
        for index, step in enumerate(path):
            if step[2] == "subClassOf":
                if step[3] == "<-":
                    next_step = path[index + 1]
                    if next_step[2] == "subClassOf":
                        if step[3] == "->":
                            path_to_be_removed.append(path)
                            break
    for path in path_to_be_removed:
        directed_paths.remove(path)
    return directed_paths


def single_paths_annotation(query_subgraph, ML1, ML2, base):
    ML2_temp = []
    triples_rdf_list = []
    path_borders_tuples = set()
    # starting from class occurrences
    for occurrence_row in ML2:
        root_word = occurrence_row[1]
        occurrence = occurrence_row[0]
        # controllo se la root word, nell'ontologia, è una sottoclasse di Points
        ont_obj = getattr(base, f"{root_word}")
        if ont_obj in base.Points.descendants() and all(
                coordinate_occurrence not in occurrence_row[2]
                for coordinate_occurrence in ["x1", "y1", "z1"]
        ):
            for row in ML1:
                if row[0] == "X" and row[1][0] == root_word:
                    occurrence_row[2].append("x1")
                elif row[0] == "Y" and row[1][0] == root_word:
                    occurrence_row[2].append("y1")
                elif row[0] == "Z" and row[1][0] == root_word:
                    occurrence_row[2].append("z1")
        for root_row in ML1:
            if root_row[0] == root_word:
                if root_row[2] == "class":
                    # simple triple for class variables type attribution
                    triples_rdf_list.append(
                        [
                            [f"?{occurrence} rdf:type base:{root_word}."],
                            occurrence,
                            root_word,
                        ]
                    )
                    # neighborood guided long paths
                    for neighbor in occurrence_row[2]:
                        # starting from relationship neighbors
                        for occ_row in ML2:
                            rt_word = occ_row[1]
                            occ = occ_row[0]
                            if neighbor == occ:
                                for rt_row in ML1:
                                    if rt_row[0] == rt_word:
                                        if rt_row[2] == "relationship":
                                            subject = occ_row[3][0]
                                            objectt = occ_row[3][1]
                                            if subject == occurrence:
                                                # generare undirected graph
                                                UG = query_subgraph.to_undirected()
                                                directed_paths = []
                                                # generare tutti i path comprensivi di edges che vanno dal soggetto alla relazione
                                                for (
                                                        edge_path
                                                ) in nx.all_simple_edge_paths(
                                                    UG,
                                                    source=f"?{subject}",
                                                    target=rt_word,
                                                ):
                                                    directed_path = []
                                                    for n1, n2 in edge_path:
                                                        if query_subgraph.has_edge(
                                                                n1, n2
                                                        ):  # if we are going down the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n1
                                                            ][n2].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                [
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "->",
                                                                ]
                                                            )
                                                        elif query_subgraph.has_edge(
                                                                n2, n1
                                                        ):  # if we are going up on the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n2
                                                            ][n1].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                [
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "<-",
                                                                ]
                                                            )
                                                    directed_paths.append(directed_path)
                                                    # EXAMPLE DIRECTED_PATH_SHAPE: Path with directed edges: [(1, 2, 'edge_1_2', '->'), (2, 3, 'edge_2_3', '->'), (3, 4, 'edge_3_4', '->'), (4, 5, 'edge_4_5', '->')]
                                                directed_paths = (
                                                    remove_path_with_dome_issues(
                                                        directed_paths
                                                    )
                                                )
                                                # prendere il più corto
                                                subj_rel_path = min(
                                                    directed_paths, key=len
                                                )
                                                # generare tutti i path comprensivi di edges che vanno dalla relazione all'oggetto
                                                directed_paths = []
                                                if UG.has_node(f"?{objectt}"):
                                                    object_to_look_for = f"?{objectt}"
                                                elif UG.has_node(f"{objectt}"):
                                                    object_to_look_for = objectt
                                                for (
                                                        edge_path
                                                ) in nx.all_simple_edge_paths(
                                                    UG,
                                                    source=rt_word,
                                                    target=object_to_look_for,
                                                ):
                                                    directed_path = []
                                                    for n1, n2 in edge_path:
                                                        if query_subgraph.has_edge(
                                                                n1, n2
                                                        ):  # if we are going down the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n1
                                                            ][n2].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                [
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "->",
                                                                ]
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                        elif query_subgraph.has_edge(
                                                                n2, n1
                                                        ):  # if we are going up on the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n2
                                                            ][n1].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                [
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "<-",
                                                                ]
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                        # EXAMPLE DIRECTED_PATH_SHAPE: Path with directed edges: [(1, 2, 'edge_1_2', '->'), (2, 3, 'edge_2_3', '->'), (3, 4, 'edge_3_4', '->'), (4, 5, 'edge_4_5', '->')]
                                                directed_paths = (
                                                    remove_path_with_dome_issues(
                                                        directed_paths
                                                    )
                                                )
                                                # prendere il più corto
                                                rel_obj_path = min(
                                                    directed_paths, key=len
                                                )
                                                # JUST FOR REFLEXIVE PROPERTIES (or for props which ranges and domain over the same class, to which belong both variables) combinarli facendo attenzione che se alla rel si arriva da domain se ne esce da range e viceversa (dico viceversa perchè il campo subj-obj della rel occurrence è generato prima del mapping, quindi non è detto che vada bene)
                                                last_tuple = subj_rel_path[-1]
                                                last_pred = last_tuple[2]
                                                first_tuple = rel_obj_path[0]
                                                first_pred = first_tuple[2]
                                                if (
                                                        last_pred == first_pred
                                                ):  # se, dunque, la prop è connessa al grafo da un solo edge
                                                    subj_rel_path[-1][2] = "domain"
                                                    rel_obj_path[0][2] = "range"

                                                subj_rel_obj_path = (
                                                        subj_rel_path + rel_obj_path
                                                )
                                                # scrivere triple per i path e aggiungerle come unica lista, tenendo di conto le frecce nel decidere chi è soggetto e chi è oggetto
                                                path_triple_list = []
                                                for path_tuple in subj_rel_obj_path:
                                                    if path_tuple[3] == "->":
                                                        subj = path_tuple[0]
                                                        if not subj[0] == "?":
                                                            subj = "base:" + subj
                                                        obj = path_tuple[1]
                                                        if not obj[0] == "?":
                                                            obj = "base:" + obj
                                                        predicate = path_tuple[2]
                                                    elif path_tuple[3] == "<-":
                                                        subj = path_tuple[1]
                                                        if not subj[0] == "?":
                                                            subj = "base:" + subj
                                                        obj = path_tuple[0]
                                                        if not obj[0] == "?":
                                                            obj = "base:" + obj
                                                        predicate = path_tuple[2]

                                                    if predicate in [
                                                        "subClassOf",
                                                        "domain",
                                                        "range",
                                                    ]:
                                                        prefix = "rdfs:"
                                                    elif predicate in ["type"]:
                                                        prefix = "rdf:"
                                                    else:
                                                        prefix = "base:"
                                                    path_triple_list.append(
                                                        f"{subj} {prefix}{predicate} {obj}."
                                                    )
                                                triples_rdf_list.append(
                                                    [
                                                        path_triple_list,
                                                        occurrence,
                                                        neighbor,  # qui neighbor è la relazione
                                                    ]
                                                )
                                                # eliminare la row della relationship occurrence da ML2 e dal neighborood dell'oggetto
                                                ML2.remove(occ_row)
                                                ML2_temp.append(occ_row)
                                                for row in ML2:
                                                    if row[0] == objectt:
                                                        try:
                                                            row[2].remove(neighbor)
                                                        except:
                                                            pass
                                                # aggiungere la tupla (sogg, ogg) alla lista path_borders_tuple. in questa maniera altre relazioni potrebbero appoggiarvisi, ma nessuna rel implicita tra le due sarà considerata.
                                                path_borders_tuples.add(
                                                    (subject, objectt)
                                                )
                                                path_borders_tuples.add(
                                                    (objectt, subject)
                                                )
                                        # path legati alle data prop
                                        elif rt_row[2] == "data_property":
                                            right_subject_flag = False
                                            property_instance = neighbor
                                            property_root = rt_row[0]
                                            if occ_row[3][0] != None:
                                                subject = occ_row[3][0]
                                                if subject == occurrence:
                                                    right_subject_flag = True
                                            else:
                                                subject = occurrence  # in caso in cui una prop non sia stata riconosciuta come tale si assegna di default il soggettoo in base al neighborood.
                                                right_subject_flag = True
                                            # scrivo il path fino alla data property
                                            # generare undirected graph
                                            if right_subject_flag == True:
                                                UG = query_subgraph.to_undirected()
                                                directed_paths = []
                                                # generare tutti i path comprensivi di edges che vanno dal soggetto alla relazione
                                                for (
                                                        edge_path
                                                ) in nx.all_simple_edge_paths(
                                                    UG,
                                                    source=f"?{subject}",
                                                    target=property_root,
                                                ):
                                                    directed_path = []
                                                    for n1, n2 in edge_path:
                                                        if query_subgraph.has_edge(
                                                                n1, n2
                                                        ):  # if we are going down the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n1
                                                            ][n2].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                (
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "->",
                                                                )
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                        elif query_subgraph.has_edge(
                                                                n2, n1
                                                        ):  # if we are going up on the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n2
                                                            ][n1].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                (
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "<-",
                                                                )
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                        # EXAMPLE DIRECTED_PATH_SHAPE: Path with directed edges: [(1, 2, 'edge_1_2', '->'), (2, 3, 'edge_2_3', '->'), (3, 4, 'edge_3_4', '->'), (4, 5, 'edge_4_5', '->')]
                                                directed_paths = (
                                                    remove_path_with_dome_issues(
                                                        directed_paths
                                                    )
                                                )
                                                # prendere il più corto
                                                subj_prop_root_path = min(
                                                    directed_paths, key=len
                                                )
                                                path_triple_list = []
                                                for path_tuple in subj_prop_root_path:
                                                    if path_tuple[3] == "->":
                                                        subj = path_tuple[0]
                                                        if not subj[0] == "?":
                                                            subj = "base:" + subj
                                                        obj = path_tuple[1]
                                                        if not obj[0] == "?":
                                                            obj = "base:" + obj
                                                        predicate = path_tuple[2]
                                                    elif path_tuple[3] == "<-":
                                                        subj = path_tuple[1]
                                                        if not subj[0] == "?":
                                                            subj = "base:" + subj
                                                        obj = path_tuple[0]
                                                        if not obj[0] == "?":
                                                            obj = "base:" + obj
                                                        predicate = path_tuple[2]

                                                    if predicate in [
                                                        "subClassOf",
                                                        "domain",
                                                        "range",
                                                    ]:
                                                        prefix = "rdfs:"
                                                    elif predicate in ["type"]:
                                                        prefix = "rdf:"
                                                    else:
                                                        prefix = "base:"
                                                    path_triple_list.append(
                                                        f"{subj} {prefix}{predicate} {obj}."
                                                    )
                                                # aggiungo al path due triple così formate ({property_root} rdfs:range values), (?{property_instance} rdf:type values). di per sè non ha senso, ma in fase di cleaning questo permetterà di attribuire la variabile relativa alla property occurrence come oggetto di una tripla subj prop_root prop_occ
                                                path_triple_list.append(
                                                    f"base:{property_root} rdfs:range values"
                                                )
                                                path_triple_list.append(
                                                    f"?{property_instance} rdf:type values"
                                                )
                                                triples_rdf_list.append(
                                                    [
                                                        path_triple_list,
                                                        occurrence,
                                                        neighbor,
                                                    ]
                                                )
                                        elif (
                                                rt_row[2] == "class"
                                                or rt_row[2] == "individual"
                                        ):
                                            ind_flag = False
                                            if rt_row[2] == "individual":
                                                ind_flag = True
                                            # qui da fare, path dall'uno all'altro. così gestisco anche implicit relationships
                                            # prima controllare che non esista nel vicinato una rel che punta a quell'ente come ad un oggetto e che ha la parola analizzata come soggetto
                                            rel_subjobj_flag = False
                                            for row in ML2:
                                                if len(row) >= 4:
                                                    if row[0] in occurrence_row[2]:
                                                        if (
                                                                row[3][0] == occurrence
                                                                and row[3][1] == neighbor
                                                        ) or (
                                                                row[3][0] == neighbor
                                                                and row[3][1] == occurrence
                                                        ):
                                                            rel_subjobj_flag = True
                                                            break
                                            if (
                                                    rel_subjobj_flag == False
                                                    and (occurrence, neighbor)
                                                    not in path_borders_tuples
                                                    and (neighbor, occurrence)
                                                    not in path_borders_tuples
                                            ):  # se quindi non vi sono relazioni esplicite da considerare fra i due:
                                                # generare undirected graph
                                                UG = query_subgraph.to_undirected()
                                                directed_paths = []
                                                if ind_flag == True:
                                                    neigh_to_look_for = neighbor
                                                else:
                                                    neigh_to_look_for = f"?{neighbor}"
                                                # generare tutti i path comprensivi di edges che vanno dal soggetto alla relazione
                                                for (
                                                        edge_path
                                                ) in nx.all_simple_edge_paths(
                                                    UG,
                                                    source=f"?{occurrence}",
                                                    target=neigh_to_look_for,
                                                ):
                                                    directed_path = []
                                                    for n1, n2 in edge_path:
                                                        if query_subgraph.has_edge(
                                                                n1, n2
                                                        ):  # if we are going down the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n1
                                                            ][n2].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                (
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "->",
                                                                )
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                        elif query_subgraph.has_edge(
                                                                n2, n1
                                                        ):  # if we are going up on the hyerarchical tree
                                                            edge_label = query_subgraph[
                                                                n2
                                                            ][n1].get(
                                                                "label", "unknown"
                                                            )
                                                            directed_path.append(
                                                                (
                                                                    n1,
                                                                    n2,
                                                                    edge_label,
                                                                    "<-",
                                                                )
                                                            )
                                                            directed_paths.append(
                                                                directed_path
                                                            )
                                                directed_paths = (
                                                    remove_path_with_dome_issues(
                                                        directed_paths
                                                    )
                                                )
                                                # qui filtrare di modo che si eliminino dai directed_paths quelli che non hanno alcuna relazione dentro
                                                non_trivial_flag = False
                                                paths_to_be_removed = []
                                                for directed_path in directed_paths:
                                                    for tuple in directed_path:
                                                        if (
                                                                "domain" in tuple[2]
                                                                or "range" in tuple[2]
                                                        ):
                                                            non_trivial_flag = True
                                                            break
                                                    if non_trivial_flag == False:
                                                        paths_to_be_removed.append(
                                                            directed_path
                                                        )
                                                for path in paths_to_be_removed:
                                                    if path in directed_paths:
                                                        directed_paths.remove(path)
                                                if len(directed_paths) > 0:
                                                    subj_neigh_path = min(
                                                        directed_paths, key=len
                                                    )
                                                    path_triple_list = []
                                                    for path_tuple in subj_neigh_path:

                                                        if path_tuple[3] == "->":
                                                            subj = path_tuple[0]
                                                            if not subj[0] == "?":
                                                                subj = "base:" + subj
                                                            obj = path_tuple[1]
                                                            if not obj[0] == "?":
                                                                obj = "base:" + obj
                                                            predicate = path_tuple[2]
                                                        elif path_tuple[3] == "<-":
                                                            subj = path_tuple[1]
                                                            if not subj[0] == "?":
                                                                subj = "base:" + subj
                                                            obj = path_tuple[0]
                                                            if not obj[0] == "?":
                                                                obj = "base:" + obj
                                                            predicate = path_tuple[2]

                                                        if predicate in [
                                                            "subClassOf",
                                                            "domain",
                                                            "range",
                                                        ]:
                                                            prefix = "rdfs:"
                                                        elif predicate in ["type"]:
                                                            prefix = "rdf:"
                                                        else:
                                                            prefix = "base:"
                                                        path_triple_list.append(
                                                            f"{subj} {prefix}{predicate} {obj}."
                                                        )

                                                    triples_rdf_list.append(
                                                        [
                                                            path_triple_list,
                                                            occurrence,
                                                            neighbor,
                                                        ]
                                                    )
                                                    path_borders_tuples.add(
                                                        (occurrence, neighbor)
                                                    )
                                                    path_borders_tuples.add(
                                                        (neighbor, occurrence)
                                                    )
    for row in ML2_temp:
        ML2.append(row)
    return triples_rdf_list


# clean si compone di due fasi: 1) cleaning per classi che devono diventare variabili e 2) cleaning per range e domain relationships
def clean_rdf_path(
        triples_rdf_list, parsed_ontology_schema
):  # si prendono in input liste contenenti una lista per ogni path. ogni tripla è una stringa separata all'interno della lista del proprio path

    for path_ID, rdf_path_with_metadata in enumerate(triples_rdf_list):
        rdf_path = rdf_path_with_metadata[0]
        if len(rdf_path) == 1:
            continue  # no cleaning needed
        else:
            # looking for classes to be substituted with variables (i am looking only for classes (or subclassof jointed groups of classes) who are domain of a certain prop or rel and range of another. let's call them "joints")
            interval_indexes = []
            interval_classes = []
            first_range_domain_flag = False
            second_range_domain_flag = False
            # also further cleaning for next intervals
            first_span_flag = True
            for index, triple in enumerate(rdf_path):
                predicate = triple.split()[1]
                if (
                        predicate in ["rdfs:domain", "rdfs:range"]
                        and first_range_domain_flag == False
                        and first_span_flag == True
                ):
                    first_range_domain_flag = True
                    first_span_flag = False
                    continue
                if (
                        predicate in ["rdfs:domain", "rdfs:range"]
                        and first_range_domain_flag == False
                        and first_span_flag == False
                ):
                    first_range_domain_flag = True
                    second_range_domain_flag = True
                    interval_start = index + 1
                    if triple.split()[2][5:-1] not in interval_classes:
                        interval_classes.append(triple.split()[2][5:-1])
                    continue
                if (
                        predicate in ["rdfs:domain", "rdfs:range"]
                        and first_range_domain_flag == True
                        and second_range_domain_flag == False
                ):
                    interval_start = index + 1
                    if triple.split()[2][5:-1] not in interval_classes:
                        interval_classes.append(triple.split()[2][5:-1])
                    second_range_domain_flag = True
                    continue
                if (
                        predicate in ["rdfs:subClassOf"]
                        and second_range_domain_flag == True
                ):
                    subj = triple.split()[0][5:]
                    obj = triple.split()[2][5:-1]
                    if subj not in interval_classes:
                        interval_classes.append(subj)
                    if obj not in interval_classes:
                        interval_classes.append(obj)
                    continue
                if predicate in ["rdf:type"]:
                    first_range_domain_flag = False
                    second_range_domain_flag = False
                    interval_classes = []
                    continue
                if (
                        predicate in ["rdfs:domain", "rdfs:range"]
                        and second_range_domain_flag == True
                ):
                    interval_end = index
                    if triple.split()[2][5:-1] not in interval_classes:
                        interval_classes.append(triple.split()[2][5:-1])
                    first_range_domain_flag = False
                    second_range_domain_flag = False
                    # modifico triple prima e dopo con variabile
                    var_name = f"?{interval_classes[0]}_{path_ID}"
                    rdf_path[interval_start - 1] = (
                        f"{rdf_path[interval_start-1].split()[0]} {rdf_path[interval_start-1].split()[1]} {var_name}."
                    )
                    rdf_path[interval_end] = (
                        f"{rdf_path[interval_end].split()[0]} {rdf_path[interval_end].split()[1]} {var_name}."
                    )
                    interval_classes = []
                    interval_indexes.append((interval_start, interval_end))

            for interval_start, interval_end in reversed(interval_indexes):
                rdf_path = rdf_path[:interval_start] + rdf_path[interval_end:]
                rdf_path_with_metadata[0] = rdf_path

    # ORA DEVO INDIVIDUARE LE REL E LE PROP E RISALIRE LUNGO DOMAIN E RANGE PER ATTRIBUIRLE AGLI INDIVIDUI O ALLE VARIABILI.
    for rdf_path_with_metadata in triples_rdf_list:
        rdf_path = rdf_path_with_metadata[0]
        if len(rdf_path) == 1:
            continue
        # individuare le relazioni
        rel_flag = False
        new_triples_list = []
        new_subject = None
        new_object = None
        prop_new_subject = None
        relationship = None
        for index, triple in enumerate(rdf_path):
            subject = triple.split()[0]
            predicate = triple.split()[1]
            object = triple.split()[2][:-1]
            stop_flag = False

            if (
                    subject[5:] in parsed_ontology_schema[2] and rel_flag == False
            ):  # se il subj è una custom rel e nella tripla precedente non l'avevo incontrata
                relationship = subject
                # vado indietro fino ad un individuo o variabile
                if predicate == "rdfs:domain" and (
                        object.startswith("?") or object[5:] in parsed_ontology_schema[3]
                ):
                    new_subject = object
                    stop_flag = True
                    rel_flag = True
                    int_start = index
                elif predicate == "rdfs:range" and (
                        object.startswith("?") or object[5:] in parsed_ontology_schema[3]
                ):
                    new_object = object
                    stop_flag = True
                    rel_flag = True
                    int_start = index
                if stop_flag == False:
                    i = index - 1
                while stop_flag == False:
                    prev_triple = rdf_path[i]
                    prev_subj = prev_triple.split()[0]
                    prev_pred = prev_triple.split()[1]
                    if prev_pred == "rdfs:subClassOf":
                        i -= 1
                    elif prev_pred == "rdf:type":
                        if predicate == "rdfs:domain":
                            new_subject = prev_subj
                        elif predicate == "rdfs:range":
                            new_object = prev_subj
                        stop_flag = True
                        rel_flag = True
                        int_start = i
                continue

            if subject[5:] in parsed_ontology_schema[2] and rel_flag == True:
                if predicate == "rdfs:domain" and (
                        object.startswith("?") or object[5:] in parsed_ontology_schema[3]
                ):
                    new_subject = object
                    stop_flag = True
                    rel_flag = False
                    int_end = index
                elif predicate == "rdfs:range" and (
                        object.startswith("?") or object[5:] in parsed_ontology_schema[3]
                ):
                    new_object = object
                    stop_flag = True
                    rel_flag = False
                    int_end = index
                if stop_flag == False:
                    i = index + 1
                while stop_flag == False:
                    next_triple = rdf_path[i]
                    next_subj = next_triple.split()[0]
                    next_pred = next_triple.split()[1]
                    if next_pred == "rdfs:subClassOf":
                        i += 1
                    elif next_pred == "rdf:type":
                        if predicate == "rdfs:domain":
                            new_subject = next_subj
                        elif predicate == "rdfs:range":
                            new_object = next_subj
                        stop_flag = True
                        rel_flag = False
                        int_end = i

            if None not in [new_subject, relationship, new_object]:
                new_triple = f"{new_subject} {relationship} {new_object}."
                new_triple_interval = (int_start, int_end)
                new_triples_list.append([new_triple, new_triple_interval])
                new_subject = None
                relationship = None
                new_object = None

            if (
                    subject[5:] in parsed_ontology_schema[1]
            ):  # data prop. ci si arriva sempre da domain
                prop = subject
                # risalgo dal lato domain e cerco un individuo o una variabile
                if predicate == "rdfs:domain" and (
                        object.startswith("?") or object[5:] in parsed_ontology_schema[3]
                ):
                    prop_new_subject = object
                    stop_flag = True
                    int_start = index
                if stop_flag == False:
                    i = index - 1
                while stop_flag == False:
                    prev_triple = rdf_path[i]
                    prev_subj = prev_triple.split()[0]
                    prev_pred = prev_triple.split()[1]
                    if prev_pred == "rdfs:subClassOf":
                        i -= 1
                    elif prev_pred == "rdf:type":
                        if predicate == "rdfs:domain":
                            prop_new_subject = prev_subj
                        stop_flag = True
                        int_start = i
                if prop_new_subject != None:
                    two_triples_after = rdf_path[
                        index + 2
                        ]  # here assuming that property is at the end of the path and built accordingly to previous function
                    prop_new_object = two_triples_after.split()[0]
                    new_triple = f"{prop_new_subject} {prop} {prop_new_object}."
                    new_triple_interval = (int_start, index + 2)
                    new_triples_list.append([new_triple, new_triple_interval])
                    prop_new_subject = None
                    break

                # guardo la tripla successiva (che dovrebbe essere l'ultima) e prendo il soggetto per usarlo come oggetto della nuova tripla

        if len(new_triples_list) != 0:
            for new_triple_data in reversed(new_triples_list):
                new_triple = new_triple_data[0]
                new_triple_start = new_triple_data[1][0]
                new_triple_end = new_triple_data[1][1]
                rdf_path = rdf_path[:new_triple_start] + rdf_path[(new_triple_end):]
                rdf_path[new_triple_start] = new_triple
                rdf_path_with_metadata[0] = rdf_path

    return triples_rdf_list


def apply_filters(ML4, ML2, ML1):
    grouping_list = []
    not_to_be_considered = []
    # filter row structure = [filtering_condition, [occurrence], [AVG/SUM/EMPTY]] or [filtering_condition, [occurrence1, occurrence2], [EMPTY]] for identical or dinstinct filters or [filtering_condition, [occurrence, limit number], [EMPTY]] for superlatives
    filters_list = (
        []
    )  # ["occurrence > x",...] qui da aggiungere clausola filter, perchè nel caso di OR devo impostarle diversamente
    superlatives_list = (
        []
    )  # [["ORDER BY ASC o DESC (occurrence)", "LIMIT x"],] qui già pronte per l'uso
    for filter_row in ML4:
        if filter_row not in not_to_be_considered:
            filtering_condition = filter_row[0]
            # aggiungo "?" se il termine di paragone è una variabile e non c'è greatest o lowest
            letter_flag = any(char.isalpha() for char in filtering_condition)
            if letter_flag == True and filtering_condition not in [
                "GREATEST",
                "LOWEST",
            ]:
                for index, char in enumerate(filtering_condition):
                    if char.isalpha() == True:
                        filtering_condition = (
                                filtering_condition[:index]
                                + "?"
                                + filtering_condition[index:]
                        )
                        break
            if (
                    filter_row[0] not in ["=", "!="]
                    and (len(filter_row[2]) + len(filter_row[3])) == 0
            ):  # for normal comparatives or data property sameness or difference filters, also including composite ones with inner operations
                filtered_occurrence = filter_row[1][0]
                word_type = None
                for row in ML2:
                    if row[0] == filtered_occurrence:
                        root_word = row[1]
                        for roww in ML1:
                            if root_word == roww[0]:
                                word_type = roww[2]
                                break
                if (
                        word_type == "data_property"
                        or word_type == None  # per multi argument è il None
                ):
                    if not any(
                            char in filtered_occurrence
                            for char in [" ", "-", "+", "/", "*"]
                    ):
                        filters_list.append(
                            f"?{filtered_occurrence} {filtering_condition}"
                        )
                    else:
                        filtered_occurrence = re.sub(
                            r"([a-zA-Z_]+\d+)\s*([\-\+\*/])\s*([a-zA-Z_]+\d+)",
                            r"?\1 \2 ?\3",
                            filtered_occurrence,
                        )
                        filters_list.append(
                            f"{filtered_occurrence} {filtering_condition}"
                        )
                elif word_type == "relationship":
                    for row in ML2:
                        if row[0] == filtered_occurrence:
                            grouping_variable = filter_row[4][0]
                            object = row[3][1]
                            break
                    having_row = f"HAVING (COUNT(?{object}){filtering_condition})"
                    for other_filter_row in ML4:
                        if other_filter_row != filter_row:
                            if other_filter_row[1][0] == filtered_occurrence:
                                not_to_be_considered.append(other_filter_row)
                                having_row = (
                                        having_row[:-1]
                                        + f" && COUNT(?{object}){other_filter_row[0]}"
                                        + having_row[-1]
                                )
                    grouping_list.append(f"GROUP BY ?{grouping_variable}")
                    grouping_list.append(having_row)
            elif (
                    len(filter_row[1]) == 1
                    and len(filter_row[2]) == 0
                    and len(filter_row[3]) == 1
                    and len(filter_row[4]) == 1
            ):
                # for normal AVG/SUM filters on data properties
                filtered_occurrence = filter_row[1][0]
                if not any(
                        char in filtered_occurrence for char in [" ", "-", "+", "/", "*"]
                ):
                    filtered_occurrence = "?" + filtered_occurrence
                else:
                    filtered_occurrence = re.sub(
                        r"([a-zA-Z_]+\d+)\s*([\-\+\*/])\s*([a-zA-Z_]+\d+)",
                        r"?\1 \2 ?\3",
                        filtered_occurrence,
                    )
                grouping_variable = filter_row[4][0]
                having_row = f"HAVING ({filter_row[3][0]}({filtered_occurrence}){filtering_condition})"
                for other_filter_row in ML4:
                    if other_filter_row != filter_row:
                        if other_filter_row[1][0] == filtered_occurrence:
                            not_to_be_considered.append(other_filter_row)
                            having_row = (
                                    having_row[:-1]
                                    + f" && {filter_row[3][0]}(?{object}){other_filter_row[0]}"
                                    + having_row[-1]
                            )
                grouping_list.append(f"GROUP BY ?{grouping_variable}")
                grouping_list.append(having_row)
            elif (
                    "GREATEST" in filtering_condition or "LOWEST" in filtering_condition
            ):  # superlative filters
                filtered_occurrence = filter_row[1][0]
                limit_number = filter_row[2][0]
                grouping_function = None
                grouping_variable = None
                if len(filter_row[3]) > 0:
                    grouping_function = filter_row[3][0]
                    grouping_variable = filter_row[4][0]
                if len(filter_row[4]) > 0:
                    grouping_variable = filter_row[4][0]
                if filtering_condition == "GREATEST":
                    order = "DESC"
                elif filtering_condition == "LOWEST":
                    order = "ASC"
                if grouping_function:
                    superlatives_list.append(
                        f"ORDER BY {order}({grouping_function}(?{filtered_occurrence}))"
                    )
                    grouping_list.append(f"GROUP BY ?{grouping_variable}")
                elif grouping_variable:
                    for row in ML2:
                        if row[0] == filtered_occurrence:
                            object = row[3][1]
                            break
                    superlatives_list.append(f"ORDER BY {order}(COUNT(?{object}))")
                    grouping_list.append(f"GROUP BY ?{grouping_variable}")
                else:
                    superlatives_list.append(
                        f"ORDER BY {order}(?{filtered_occurrence})"
                    )
                superlatives_list.append(f"LIMIT {limit_number}")
            elif (
                    filter_row[0] == "=" or filter_row[0] == "!="
            ):  # dunque filtri = o != tra variabili individui
                filtered_occurrence_1 = filter_row[1][0]
                filtered_occurrence_2 = filter_row[1][1]
                # verifico che non siano individui
                if check_for_occ_type(filtered_occurrence_1, ML2, ML1) != "individual":
                    filtered_occurrence_1 = "?" + filtered_occurrence_1
                else:
                    filtered_occurrence_1 = "base:" + filtered_occurrence_1
                if check_for_occ_type(filtered_occurrence_1, ML2, ML1) != "individual":
                    filtered_occurrence_2 = "?" + filtered_occurrence_2
                else:
                    filtered_occurrence_2 = "base:" + filtered_occurrence_2
                filters_list.append(
                    f"{filtered_occurrence_1} {filtering_condition} {filtered_occurrence_2}"
                )
    # cleaning for multiple group by of same variable
    group_by_flag = False
    index_list = []
    for index, row in enumerate(grouping_list):
        if "GROUP BY" in row:
            if group_by_flag == False:
                group_by_flag = True
            elif group_by_flag == True:
                index_list.append(index)
    for index in reversed(index_list):
        del grouping_list[index]

    return [filters_list, superlatives_list, grouping_list]


def check_for_occ_type(occurrence, ML2, ML1):
    for row in ML2:
        if occurrence == row[0]:
            root = row[1]
            for roww in ML1:
                if root == roww[0]:
                    type = roww[2]
                    return type


def rearrange_operators_by_scope(ML3):
    temp_op_dict = {}
    temp_ML3 = []
    while ML3:
        for logical_op_row in ML3:
            logical_operator = logical_op_row[0]
            right_moment_row_flag = True
            first_order_flag = True
            temp_scope_list = []
            for l in logical_op_row:
                if right_moment_row_flag == False:
                    break
                if type(l) == list:
                    for element in l:
                        if right_moment_row_flag == False:
                            break
                        # caso per ordini superiori al primo
                        if any(x in element for x in ["NOT", "OR"]):
                            first_order_flag = False
                            temp_scope_list.append(element)
                            # caso per ordini di scope superiori al primo
                            if element not in temp_op_dict.keys():
                                right_moment_row_flag = False
                                continue
            if right_moment_row_flag == True and first_order_flag == False:
                order = max([temp_op_dict[x] for x in temp_scope_list]) + 1
                temp_op_dict[logical_operator] = order
                ML3.remove(logical_op_row)
                temp_ML3.append(logical_op_row)
            if first_order_flag == True:
                temp_op_dict[logical_operator] = 0
                ML3.remove(logical_op_row)
                temp_ML3.append(logical_op_row)
    ML3 = temp_ML3
    return ML3


def in_single_char(expr1, expr2):
    expr1 = expr1.replace("?", "")
    if all(char in expr2 for char in expr1):
        return True


def full_in_question_mark(expr1, expr2):
    expr1 = expr1.replace("?", "")
    if expr1 in expr2:
        return True


def full_in_question_mark_and_space(expr1, expr2):
    expr1 = expr1.replace("?", "")
    expr1 = expr1.replace(" ", "")
    if expr1 in expr2:
        return True


def find_object_declaration(relationship_instance, ML2, triples_rdf_list):
    obj_declaration = None
    for row in ML2:
        if row[0] == relationship_instance:
            object = row[3][1]
    for row in ML2:
        if row[0] == object:
            rt_obj = row[1]
    for index, triple_with_metadata in enumerate(triples_rdf_list):
        if (triple_with_metadata[1], triple_with_metadata[2]) == (object, rt_obj):
            obj_declaration = triple_with_metadata
    return obj_declaration, index


def find_data_variable_declaration(property_instance, ML2, triples_rdf_list):
    var_declaration = None
    for row in ML2:
        if row[0] == property_instance:
            subject = row[3][0]
    for index, triple_with_metadata in enumerate(triples_rdf_list):
        if (triple_with_metadata[1], triple_with_metadata[2]) == (
                subject,
                property_instance,
        ):
            var_declaration = triple_with_metadata
            break
    return var_declaration, index


def logical_operators_applications(ML3, filters_list, triples_rdf_list, ML2, ML1):
    ML3 = rearrange_operators_by_scope(ML3)
    for logical_operator_row in ML3:
        # NOT
        logical_operator = logical_operator_row[0]
        if "NOT" in logical_operator:  # relationship negation
            path_list = []
            object_declaration_path_list = []
            filter_temp_list = []
            negata = logical_operator_row[1]
            for negatum in negata:
                if type(negatum) == str:
                    if "OR" in negatum:
                        for log_op_row in ML3:
                            if negatum == log_op_row[0]:
                                if type(log_op_row[1]) == list:
                                    for path_with_metadata in triples_rdf_list:
                                        occurrence = path_with_metadata[2]
                                        if occurrence == negatum:
                                            path_list.append(path_with_metadata)
                                            break
                                elif type(log_op_row[1]) == str:  # inner or
                                    conditions = log_op_row[2]
                                    occurrence = log_op_row[1]
                                    ##############################################
                                    for filter in filters_list:
                                        # FULL CHECK
                                        if all(
                                                full_in_question_mark_and_space(
                                                    condition, filter
                                                )
                                                for condition in conditions
                                        ) and full_in_question_mark_and_space(
                                            occurrence, filter
                                        ):
                                            filters_list.remove(filter)
                                            filter_temp_list.append(filter)

                                        """ SINGLE CHAR CHECK
                                        if all(
                                            in_single_char(condition, filter)
                                            for condition in conditions
                                        ):
                                            if in_single_char(occurrence, filter):
                                                filters_list.remove(filter)
                                                filter_temp_list.append(filter)
                                                """

                    else:
                        for path_with_metadata in triples_rdf_list:
                            occurrence = path_with_metadata[2]
                            if occurrence == negatum:
                                path_list.append(path_with_metadata)
                                if (
                                        check_for_occ_type(occurrence, ML2, ML1)
                                        == "relationship"
                                ):
                                    path_with_meta, _ = find_object_declaration(
                                        occurrence, ML2, triples_rdf_list
                                    )
                                    path_list.append(path_with_meta)
                                    object_declaration_path_list.append(path_with_meta)
                                break
                if type(negatum) == list:
                    if len(negatum) == 2:
                        filtered_occurrence = negatum[0]
                        filtering_condition = negatum[1]
                        for filter in filters_list:
                            if full_in_question_mark_and_space(
                                    filtering_condition, filter
                            ) and full_in_question_mark_and_space(
                                filtered_occurrence, filter
                            ):
                                filters_list.remove(filter)
                                filter_temp_list.append(filter)
                            """ SINGLE CHAR CHECK
                            if in_single_char(
                                filtered_occurrence, filter
                            ) and in_single_char(
                                filtering_condition, filter
                            ):  # non ottimale, perchè si espone a falsi positivi
                                filters_list.remove(filter)
                                filter_temp_list.append(filter)
                                """
                    elif len(negatum) == 3:
                        occurrence1 = negatum[0]
                        occurrence2 = negatum[1]
                        identity_condition = negatum[2]
                        for filter in filters_list:
                            if (
                                    full_in_question_mark_and_space(
                                        identity_condition, filter
                                    )
                                    and full_in_question_mark_and_space(occurrence1, filter)
                                    and full_in_question_mark_and_space(occurrence2, filter)
                            ):
                                filters_list.remove(filter)
                                filter_temp_list.append(filter)
                            """ SINGLE CHAR CHECK
                            if (
                                in_single_char(occurrence1, filter)
                                and in_single_char(occurrence2, filter)
                                and in_single_char(identity_condition, filter)
                            ):  # non ottimale, perchè si espone a falsi positivi
                                filters_list.remove(filter)
                                filter_temp_list.append(filter)
                                """
            temp_path = ["FILTER NOT EXISTS {"]
            for path_with_metadata in path_list:
                if not (path_with_metadata in object_declaration_path_list):
                    triples_rdf_list.remove(path_with_metadata)
                for triple in path_with_metadata[0]:
                    temp_path.append(triple)
            for filter in filter_temp_list:
                filter_split = filter.split()
                if filter_split[-2] in ["=", "!="]:  # filtro di identity or sameness
                    occ1 = filter_split[0].replace("?", "")
                    occ2 = filter_split[2].replace("?", "")
                    for row in ML2:
                        if row[0].replace("?", "") == occ1:
                            occ1_root = row[1]
                        if row[0].replace("?", "") == occ2:
                            occ2_root = row[1]
                    for path_with_metadata in triples_rdf_list:
                        if (path_with_metadata[1], path_with_metadata[2]) == (
                                occ1,
                                occ1_root,
                        ):
                            for triple in path_with_metadata[0]:
                                temp_path.append(triple)
                        if (path_with_metadata[1], path_with_metadata[2]) == (
                                occ2,
                                occ2_root,
                        ):
                            for triple in path_with_metadata[0]:
                                temp_path.append(triple)
                elif filter_split[0].replace("?", "") in [
                    prop_row[0] for prop_row in ML2
                ]:  # questo esclude i compositional
                    # trovo il path dove si attribuisce la prop e lo infilo qui. lo duplico? no
                    property_instance = [
                        prop_row[0]
                        for prop_row in ML2
                        if prop_row[0] == filter_split[0].replace("?", "")
                    ][0]
                    var_declaration_path_with_metadata, index = (
                        find_data_variable_declaration(
                            property_instance, ML2, triples_rdf_list
                        )
                    )
                    triples_rdf_list.remove(triples_rdf_list[index])
                    for triple in var_declaration_path_with_metadata:
                        temp_path.append(triple)
                else:  # compositional
                    filter_components = [
                        filt_comp.replace("?", "") for filt_comp in filter.split()
                    ]
                    filter_variables = [
                        filt_comp
                        for filt_comp in filter_components
                        if filt_comp in [prop_row[0] for prop_row in ML2]
                    ]
                    for variable_instance in filter_variables:
                        var_declaration_path_with_metadata, index = (
                            find_data_variable_declaration(
                                variable_instance, ML2, triples_rdf_list
                            )
                        )
                        triples_rdf_list.remove(triples_rdf_list[index])
                        for triple in var_declaration_path_with_metadata:
                            temp_path.append(triple)
            filter_temp_list = explicit_filters(filter_temp_list)
            for filter in filter_temp_list:
                temp_path.append(filter)
            temp_path.append("}")
            temp_path = list(set(temp_path))
            triples_rdf_list.append([temp_path, None, logical_operator])
        # caso 1: INNER PROPERTY OR (qui uso ||) [ora supporta anche blocchi conjuncted, ottimi per intervalli]
        elif "OR" in logical_operator and type(logical_operator_row[1]) == str:
            occurrence = logical_operator_row[1]
            conditions = []
            conjuncted_conditions = {}
            temp = []
            for index, x in enumerate(logical_operator_row[2]):
                if type(x) == str:
                    conditions.append(x)
                if type(x) == list:
                    for el in x:
                        conditions.append(el)
                        temp.append(el)
                    conjuncted_conditions[index] = temp
                    temp = []
            direct_temp_filter_list = []
            conjuncted_temp_filter_dict = {}
            for key in conjuncted_conditions.keys():
                conjuncted_temp_filter_dict[key] = None
            for filter in filters_list:
                if any(
                        y in filter.split() for y in ["-", "+", "*", "/"]
                ):  # se il filtro ha come occurrence un'operazione tra variabili
                    if (
                            occurrence.split()[0] in filter
                            and occurrence.split()[2] in filter
                    ):
                        if any(
                                z in filter.split() for z in conditions
                        ):  # per filtri numerici
                            key_flag = False
                            for key in conjuncted_conditions.keys():
                                if filter.split()[-1] in conjuncted_conditions[key]:
                                    key_flag = True
                                    if conjuncted_temp_filter_dict[key] == None:
                                        conjuncted_temp_filter_dict[key] = [filter]
                                    else:
                                        conjuncted_temp_filter_dict[key].append(filter)
                            if key_flag == False:
                                direct_temp_filter_list.append(filter)
                        else:
                            control_filter = filter.replace("?", "")
                            if any(a in control_filter.split() for a in conditions):
                                key_flag = False
                                for key in conjuncted_conditions.keys():
                                    if filter.split()[-1] in conjuncted_conditions[key]:
                                        key_flag = True
                                        if conjuncted_temp_filter_dict[key] == None:
                                            conjuncted_temp_filter_dict[key] = [filter]
                                        else:
                                            conjuncted_temp_filter_dict[key].append(
                                                filter
                                            )
                                if key_flag == False:
                                    direct_temp_filter_list.append(filter)
                elif (
                        f"?{occurrence}" in filter.split()
                ):  # se il filtro ha come occurrence una sola variabile
                    if any(
                            b in filter.split() for b in conditions
                    ):  # per filtri numerici
                        key_flag = False
                        for key in conjuncted_conditions.keys():
                            if filter.split()[-1] in conjuncted_conditions[key]:
                                key_flag = True
                                if conjuncted_temp_filter_dict[key] == None:
                                    conjuncted_temp_filter_dict[key] = [filter]
                                else:
                                    conjuncted_temp_filter_dict[key].append(filter)
                        if key_flag == False:
                            direct_temp_filter_list.append(filter)
                    else:  # condizioni che comprendono una vaariabile
                        control_filter = filter.replace("?", "")
                        if any(c in control_filter.split() for c in conditions):
                            key_flag = False
                            for key in conjuncted_conditions.keys():
                                if filter.split()[-1] in conjuncted_conditions[key]:
                                    key_flag = True
                                    if conjuncted_temp_filter_dict[key] == None:
                                        conjuncted_temp_filter_dict[key] = [filter]
                                    else:
                                        conjuncted_temp_filter_dict[key].append(filter)
                            if key_flag == False:
                                direct_temp_filter_list.append(filter)
            if len(direct_temp_filter_list) > 0:
                new_filter = direct_temp_filter_list[0]
                for index, filter in enumerate(direct_temp_filter_list):
                    if index == 0:
                        continue
                    else:
                        new_filter = new_filter + " || " + filter
            else:
                new_filter = None
            if new_filter:
                for key in conjuncted_temp_filter_dict.keys():
                    new_filter = new_filter + " || ("
                    for index, filter in enumerate(conjuncted_temp_filter_dict[key]):
                        if index == 0:
                            new_filter = new_filter + filter
                        else:
                            new_filter = new_filter + " && " + filter
                    new_filter = new_filter + ")"
            else:
                if len(conjuncted_temp_filter_dict.keys()) > 0:
                    for i, key in enumerate(conjuncted_temp_filter_dict.keys()):
                        if i == 0:
                            new_filter = "("
                        else:
                            new_filter = new_filter + "|| ("
                        for index, filter in enumerate(
                                conjuncted_temp_filter_dict[key]
                        ):
                            if index == 0:
                                new_filter = new_filter + filter
                            else:
                                new_filter = new_filter + " && " + filter
                        new_filter = new_filter + ")"

            filters_list.append(new_filter)

            for filter in direct_temp_filter_list:
                if filter in filters_list:
                    filters_list.remove(filter)
            for key in conjuncted_temp_filter_dict.keys():
                for filter in conjuncted_temp_filter_dict[key]:
                    filters_list.remove(filter)
        # caso 2:RELATIONSHIP OR OPPURE OUTER PROPERTY OR (qui uso UNION)
        elif "OR" in logical_operator and type(logical_operator_row[1]) == list:
            temp_path_list = []
            new_path = []
            number_of_disgiunta = len(logical_operator_row) - 1
            for i in range(1, number_of_disgiunta + 1):
                branch = logical_operator_row[i]
                branch_path_list = []
                branch_filter_temp_list = []
                for element in branch:
                    if type(element) == str:
                        if "OR" in element or "NOT" in element:
                            for log_op_row in ML3:
                                if element == log_op_row[0]:
                                    if type(log_op_row[1]) == list:  # outer or or not
                                        for path_with_metadata in triples_rdf_list:
                                            occurrence = path_with_metadata[2]
                                            if occurrence == element:
                                                branch_path_list.append(
                                                    path_with_metadata
                                                )
                                                temp_path_list.append(
                                                    path_with_metadata
                                                )
                                    elif type(log_op_row[1]) == str:  # inner or
                                        conditions = log_op_row[2]
                                        occurrence = log_op_row[1]
                                        for filter in filters_list:
                                            if all(
                                                    full_in_question_mark_and_space(
                                                        condition, filter
                                                    )
                                                    for condition in conditions
                                            ) and full_in_question_mark_and_space(
                                                occurrence, filter
                                            ):
                                                filters_list.remove(filter)
                                                branch_filter_temp_list.append(filter)
                                            """SINGLE CHAR CHECK
                                            if all(
                                                condition in filter
                                                for condition in conditions
                                            ):
                                                if in_single_char(occurrence, filter):
                                                    filters_list.remove(filter)
                                                    branch_filter_temp_list.append(
                                                        filter
                                                    )
                                                    """
                        else:
                            for path_with_metadata in triples_rdf_list:
                                occurrence = path_with_metadata[2]
                                if occurrence == element:
                                    branch_path_list.append(path_with_metadata)
                                    temp_path_list.append(path_with_metadata)
                                    if (
                                            check_for_occ_type(occurrence, ML2, ML1)
                                            == "relationship"
                                    ):
                                        path_with_meta, _ = find_object_declaration(
                                            occurrence, ML2, triples_rdf_list
                                        )
                                        branch_path_list.append(path_with_meta)
                                        # temp_path_list.append(path_with_meta) COMMENTO PERCHè NON VOGLIO CHE IL PATH DELLA DICHIARAZIONE DI VARIABILE DI ISTANZA VENGA ELIMINATO DAL CORPO CENTRALE DELLA QUERY
                                    break
                    if type(element) == list:
                        if len(element) == 2:
                            filtered_occurrence = element[0]
                            filtering_condition = element[1]
                            for filter in filters_list:
                                if full_in_question_mark_and_space(
                                        filtering_condition, filter
                                ) and full_in_question_mark_and_space(
                                    filtered_occurrence, filter
                                ):
                                    filters_list.remove(filter)
                                    branch_filter_temp_list.append(filter)
                                """ SINGLE CHAR CHECK
                                if in_single_char(
                                    filtered_occurrence, filter
                                ) and in_single_char(
                                    filtering_condition, filter
                                ):  # non ottimale, perchè si espone a falsi positivi. il problema qual è a fare un check normale?
                                    ###############################################################
                                    filters_list.remove(filter)
                                    branch_filter_temp_list.append(filter)
                                    """
                        elif len(element) == 3:
                            occurrence1 = element[0]
                            occurrence2 = element[1]
                            identity_condition = element[2]
                            for filter in filters_list:
                                if (
                                        full_in_question_mark_and_space(
                                            identity_condition, filter
                                        )
                                        and full_in_question_mark_and_space(
                                    occurrence1, filter
                                )
                                        and full_in_question_mark_and_space(
                                    occurrence2, filter
                                )
                                ):
                                    filters_list.remove(filter)
                                    branch_filter_temp_list.append(filter)
                                """SINGLE CHAR CHECK
                                if (
                                    in_single_char(occurrence1, filter)
                                    and in_single_char(occurrence2, filter)
                                    and in_single_char(identity_condition, filter)
                                ):  # non ottimale, perchè si espone a falsi positivi
                                    filters_list.remove(filter)
                                    branch_filter_temp_list.append(filter)
                                    """
                if i == 1:
                    new_path.append("{")
                    for path_with_metadata in branch_path_list:
                        for triple in path_with_metadata[0]:
                            new_path.append(triple)
                    for (
                            filter
                    ) in (
                            branch_filter_temp_list
                    ):  # qui infilo dichiarazioni di variabili di prop o di istanze di classe dentro le varie branch (le dichiarazioni di istanze di classe verranno lasciate nel corpo centrale della query, potrebbe causare issues ma far diversamente è davvero limitante. Le dichiarazioni di variabili di prop invece vengono elise dal corpo centrale)
                        filter_split = filter.split()
                        if filter_split[-2] in [
                            "=",
                            "!=",
                        ]:  # filtro di identity or sameness
                            occ1 = filter_split[0].replace("?", "")
                            occ2 = filter_split[2].replace("?", "")
                            for row in ML2:
                                if row[0].replace("?", "") == occ1:
                                    occ1_root = row[1]
                                if row[0].replace("?", "") == occ2:
                                    occ2_root = row[1]
                            for path_with_metadata in triples_rdf_list:
                                if (path_with_metadata[1], path_with_metadata[2]) == (
                                        occ1,
                                        occ1_root,
                                ):
                                    for triple in path_with_metadata[0]:
                                        new_path.append(triple)
                                if (path_with_metadata[1], path_with_metadata[2]) == (
                                        occ2,
                                        occ2_root,
                                ):
                                    for triple in path_with_metadata[0]:
                                        new_path.append(triple)
                        elif filter_split[0].replace("?", "") in [
                            prop_row[0] for prop_row in ML2
                        ]:  # questo esclude i compositional
                            # trovo il path dove si attribuisce la prop e lo infilo qui. lo duplico? no
                            property_instance = [
                                prop_row[0]
                                for prop_row in ML2
                                if prop_row[0] == filter_split[0].replace("?", "")
                            ][0]
                            var_declaration_path_with_metadata, index = (
                                find_data_variable_declaration(
                                    property_instance, ML2, triples_rdf_list
                                )
                            )
                            temp_path_list.append(triples_rdf_list[index])
                            for triple in var_declaration_path_with_metadata[0]:
                                new_path.append(triple)
                        else:  # compositional
                            filter_components = [
                                filt_comp.replace("?", "")
                                for filt_comp in filter.split()
                            ]
                            filter_variables = [
                                filt_comp
                                for filt_comp in filter_components
                                if filt_comp in [prop_row[0] for prop_row in ML2]
                            ]
                            for variable_instance in filter_variables:
                                var_declaration_path_with_metadata, index = (
                                    find_data_variable_declaration(
                                        variable_instance, ML2, triples_rdf_list
                                    )
                                )
                                temp_path_list.append(triples_rdf_list[index])
                                for triple in var_declaration_path_with_metadata[0]:
                                    new_path.append(triple)
                    branch_filter_temp_list = explicit_filters(branch_filter_temp_list)
                    for filter in branch_filter_temp_list:
                        new_path.append(filter)
                    new_path.append("}")
                else:
                    new_path.append("UNION")
                    new_path.append("{")
                    for path_with_metadata in branch_path_list:
                        for triple in path_with_metadata[0]:
                            new_path.append(triple)
                    for filter in branch_filter_temp_list:
                        filter_split = filter.split()
                        if filter_split[-2] in [
                            "=",
                            "!=",
                        ]:  # filtro di identity or sameness
                            occ1 = filter_split[0].replace("?", "")
                            occ2 = filter_split[2].replace("?", "")
                            for row in ML2:
                                if row[0].replace("?", "") == occ1:
                                    occ1_root = row[1]
                                if row[0].replace("?", "") == occ2:
                                    occ2_root = row[1]
                            for path_with_metadata in triples_rdf_list:
                                if (path_with_metadata[1], path_with_metadata[2]) == (
                                        occ1,
                                        occ1_root,
                                ):
                                    for triple in path_with_metadata[0]:
                                        new_path.append(triple)
                                if (path_with_metadata[1], path_with_metadata[2]) == (
                                        occ2,
                                        occ2_root,
                                ):
                                    for triple in path_with_metadata[0]:
                                        new_path.append(triple)
                        elif filter_split[0].replace("?", "") in [
                            prop_row[0] for prop_row in ML2
                        ]:  # questo esclude i compositional
                            # trovo il path dove si attribuisce la prop e lo infilo qui. lo duplico? no
                            property_instance = [
                                prop_row[0]
                                for prop_row in ML2
                                if prop_row[0] == filter_split[0].replace("?", "")
                            ][0]
                            var_declaration_path_with_metadata, index = (
                                find_data_variable_declaration(
                                    property_instance, ML2, triples_rdf_list
                                )
                            )
                            temp_path_list.append(triples_rdf_list[index])
                            for triple in var_declaration_path_with_metadata[0]:
                                new_path.append(triple)
                        else:  # compositional
                            filter_components = [
                                filt_comp.replace("?", "")
                                for filt_comp in filter.split()
                            ]
                            filter_variables = [
                                filt_comp
                                for filt_comp in filter_components
                                if filt_comp in [prop_row[0] for prop_row in ML2]
                            ]
                            for variable_instance in filter_variables:
                                var_declaration_path_with_metadata, index = (
                                    find_data_variable_declaration(
                                        variable_instance, ML2, triples_rdf_list
                                    )
                                )
                                temp_path_list.append(triples_rdf_list[index])
                                for triple in var_declaration_path_with_metadata[0]:
                                    new_path.append(triple)
                    branch_filter_temp_list = explicit_filters(branch_filter_temp_list)
                    for filter in branch_filter_temp_list:
                        new_path.append(filter)
                    new_path.append("}")
            new_path = list(set(new_path))
            triples_rdf_list.append([new_path, None, logical_operator])
            for path_with_metadata in temp_path_list:
                if path_with_metadata in triples_rdf_list:
                    triples_rdf_list.remove(path_with_metadata)


def explicit_filters(
        filters_list,
):  # easy, aggiunge esplicitamente i FILTER() ai filtri. da chiamare dopo aver gestito gli inner OR.
    if len(filters_list) == 0:
        return filters_list
    for index, filter in enumerate(filters_list):
        if "FILTER" not in filter:
            filter = "FILTER (" + filter + ")"
            filters_list[index] = filter
    return filters_list


def generate_query_head(ML5, base, graph_uri):
    prompt_word = ML5[0]  # questa è una stringa
    variables_with_metadata = ML5[1:]  # questa è una lista
    grouping_list = []
    namespace = base.base_iri
    query_head = [
        "PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>",
        "PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>",
        f"PREFIX base:<{namespace}>",
    ]
    prompt_row = f"{prompt_word} DISTINCT"
    for variable_row in variables_with_metadata:
        variable = variable_row[0][0]
        if len(variable_row[1]) == 0:
            prompt_row = prompt_row + f" ?{variable}"
        if len(variable_row[1]) == 1:
            if len(variable_row[2]) == 0:
                prompt_row = (
                        prompt_row
                        + f" ({variable_row[1][0]}(?{variable}) as ?overall_{variable})"
                )
            elif len(variable_row[2]) == 1:  # group by
                grouping_variable = variable_row[3][0]
                prompt_row = (
                        prompt_row
                        + f" ({variable_row[1][0]}(?{variable}) as ?grouped_{variable})"
                )
                grouping_list.append(f"GROUP BY ?{grouping_variable}")
    query_head.append(prompt_row)
    graph_row = f"FROM <{graph_uri}>"
    query_head.append(graph_row)
    where_row = "WHERE {"
    query_head.append(where_row)
    return query_head, grouping_list


def having_clean(grouping_list):
    having_flag = False
    temp_having_list = []
    for row in grouping_list:
        if "HAVING" in row:
            temp_having_list.append(row)
            if having_flag == False:
                having_temp = "HAVING ("
                temp_row = row[8:-1]
                having_temp = having_temp + temp_row
                having_flag = True
            else:
                having_temp = having_temp + "&&" + temp_row
    if having_flag == True:
        having_temp = having_temp + ")"
        for row in temp_having_list:
            if row in grouping_list:
                grouping_list.remove(row)
        grouping_list.append(having_temp)
    return grouping_list


def generate_query(
        query_head, triples_rdf_list, filters_list, grouping_list, superlatives_list
):
    query = []
    for row in query_head:
        query.append(row)
    for path_with_metadata in triples_rdf_list:
        for triple in path_with_metadata[0]:
            query.append(triple)
    for row in filters_list:
        query.append(row)
    query.append("}")
    grouping_list = having_clean(grouping_list)
    for row in grouping_list:
        query.append(row)
    for row in superlatives_list:
        query.append(row)
    return query


def write_query(output_path, query):
    with open(output_path, "w") as query_file:
        for line in query:
            query_file.write(line + "/n")


def fix_L1_L2_discrepances(L1, L2):
    for row in L2:
        rt_word = row[1]
        word_flag = False
        for rw in L1:
            if rw[0] == rt_word:
                word_flag = True
        if word_flag == False:
            row_to_be_added = [rt_word, []]
            for rw in L1:
                if rt_word in rw[1]:
                    row_to_be_added[1].append(rw[0])
            L1.append(row_to_be_added)
    return L1, L2


def nl_2_sparql(
        nl_query,
        ont_path,
        ont_namespace,
        graph_uri,
        client,
):
    try:
        ontology_schema = owl2.get_ontology(ont_path).load()
        ontology_graph = onto_to_graph(ont_path)  # type:ignore
        # GPT-based part
        wordlist = parse_wordlist(ontology_schema)
        parsed_query_lists = gpt_process_query_no_wordlist(
            nl_query, client
        )  # possible also to use wordlist for guidance and use gpt_process_query_with_wordlist(), but at the present time the model cagasburra
        print(parsed_query_lists)
        parsed_query_lists = add_commas_and_quotes(parsed_query_lists)
        # GEQB-based part
        try:
            exec(parsed_query_lists, globals())  # now the lists are defined
        except Exception as e:
            print("parsing is not python readable:", e)
        print(f"L1 = {L1}")  # type:ignore
        print(f"L2 = {L2}")  # type:ignore
        print(f"L3 = {L3}")  # type:ignore
        print(f"L4 = {L4}")  # type:ignore
        print(f"L5 = {L5}")  # type:ignore
        parsed_onto = parse_ontology_schema(ontology_schema)
        fixL1, fixL2 = fix_L1_L2_discrepances(
            L1, L2  # type:ignore
        )  # for correcting minor issues of missing rows for L1 which are in L2"""
        parsed_query = [fixL1, fixL2, L3, L4, L5]  # type: ignore
        base = owl2.get_namespace(ont_namespace)
        mapped_query = map_query(parsed_query, parsed_onto, base)
        subgraph = generate_query_subgraph(mapped_query[0], ontology_graph)
        class_occurrence_generation(subgraph, mapped_query[0], mapped_query[1])
        triples_rdf_list = single_paths_annotation(
            subgraph, mapped_query[0], mapped_query[1], base
        )
        triples_rdf_list = clean_rdf_path(triples_rdf_list, parsed_onto)
        filters_and_superlatives_and_grouping = apply_filters(
            mapped_query[3], mapped_query[1], mapped_query[0]
        )
        filters_list = filters_and_superlatives_and_grouping[0]
        superlatives_list = filters_and_superlatives_and_grouping[1]
        grouping_list = filters_and_superlatives_and_grouping[2]
        logical_operators_applications(
            mapped_query[2],
            filters_list,
            triples_rdf_list,
            mapped_query[1],
            mapped_query[0],
        )
        explicit_filters(filters_list)
        query_head = generate_query_head(mapped_query[4], base, graph_uri)[0]
        if (
                len(grouping_list) == 0
        ):  # non si accettano subqueries, quindi c'è solo un grouping
            grouping_list = generate_query_head(mapped_query[4], base, graph_uri)[1]
        sparql_query = generate_query(
            query_head, triples_rdf_list, filters_list, grouping_list, superlatives_list
        )
        return sparql_query
    except Exception as e:
        print("Error processing nl query:", e)
        raise e


"""
######TESTING

L1 = [
    ["x", ["points"]],
    ["y", ["points"]],
    ["z", ["points"]],
    ["points", ["historical_buildings", "constitutes"]],
    ["constitutes", ["points", "historical_buildings"]],
    ["historical_buildings", ["construction_year", "points", "constitutes"]],
    ["construction_year", ["historical_buildings"]],
]

L2 = [
    ["x1", "x", ["points1"], ["points1", None]],
    ["y1", "y", ["points1"], ["points1", None]],
    ["z1", "z", ["points1"], ["points1", None]],
    ["points1", "points", ["historical_buildings1", "constitutes1"], [None, None]],
    [
        "constitutes1",
        "constitutes",
        ["points1", "historical_buildings1"],
        ["points1", "historical_buildings1"],
    ],
    [
        "historical_buildings1",
        "historical_buildings",
        ["construction_year1", "points1", "constitutes1"],
        [None, None],
    ],
    [
        "construction_year1",
        "construction_year",
        ["historical_buildings1"],
        ["historical_buildings1", None],
    ],
]

L3 = [["OR1", "construction_year1", [[">1200", "<=1500"], [">=1700", "<1900"]]]]

L4 = [
    [">1200", ["construction_year1"], [], [], []],
    ["<=1500", ["construction_year1"], [], [], []],
    [">=1700", ["construction_year1"], [], [], []],
    ["<1900", ["construction_year1"], [], [], []],
]

L5 = ["SELECT", [["x1"], [], [], []], [["y1"], [], [], []], [["z1"], [], [], []]]


try:
    parsed_query = [L1, L2, L3, L4, L5]
    graph_uri = "http://localhost:8890/Testing"
    output_path = "nl-2-sparql_test_query.txt"
    onto = owl2.get_ontology(
        "/Users/matteocodiglione/Documents/GitHub/codiglione_projects/3DONT/ONTOLOGIA/URBAN/Urban_Ontology.rdf"
    ).load()
    base = owl2.get_namespace(
        "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#"
    )
    parsed_onto = parse_ontology_schema(onto)
    mapped_query = map_query(parsed_query, parsed_onto, base)
    G = onto_to_graph(
        "/Users/matteocodiglione/Documents/GitHub/codiglione_projects/3DONT/ONTOLOGIA/URBAN/Urban_Ontology.rdf"
    )
    subgraph = generate_query_subgraph(mapped_query[0], G)
    subgraph_with_occurrences = class_occurrence_generation(
        subgraph, mapped_query[0], mapped_query[1]
    )
    triples_rdf_list = single_paths_annotation(
        subgraph, mapped_query[0], mapped_query[1], base
    )
    triples_rdf_list = clean_rdf_path(triples_rdf_list, parsed_onto)

    filters_and_superlatives_and_grouping = apply_filters(
        mapped_query[3], mapped_query[1], mapped_query[0]
    )
    filters_list = filters_and_superlatives_and_grouping[0]
    superlatives_list = filters_and_superlatives_and_grouping[1]
    grouping_list = filters_and_superlatives_and_grouping[2]

    logical_operators_applications(mapped_query[2], filters_list, triples_rdf_list)
    explicit_filters(filters_list)
    query_head = generate_query_head(mapped_query[4], base, graph_uri)[0]
    if (
        len(grouping_list) == 0
    ):  # non si accettano subqueries, quindi c'è solo un grouping
        grouping_list = generate_query_head(mapped_query[4], base, graph_uri)[1]
    query = generate_query(
        query_head, triples_rdf_list, filters_list, grouping_list, superlatives_list
    )
    write_query(output_path, query)

except Exception as e:
    # Print the line and the cause of the exception
    print("An error occurred:")
    traceback.print_exc()  # This
"""
