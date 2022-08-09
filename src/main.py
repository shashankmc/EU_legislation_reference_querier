from helper_functions import get_citations, get_citations_multiple,
get_citations_structure, get_citations_structure_multiple, do_stats
import networkx as nx
from pyvis.network import Network

def get_started(source, source_type='single'):
    # Can be input dynamically, hardcoded for example
    if source_type == 'single':
        # obtain citations for single source 
        source = '32021R0664'
        links, nodes = get_citations_structure(source, cited_depth=0, cites_depth=2)
    else:
        # obtain citations for multiple sources
        sources = ['32019R0945','32021R0664']
        links, nodes = get_citations_structure_multiple(sources, cited_depth=1, cites_depth=2)

    # example on how to go through nodes in a set
    '''
    for node in nodes:
        print(node)
    '''

    # obtain stats on the extracted nodes
    do_stats(nodes)
    return links, nodes

def get_indv_stats(source, range_limit):
    # Go through matrix of depths and calculate stats for each
    # Not sure if this go into helper function
    for i in range(range_limit):
        for j in range(range_limit):
            try:
                precision, recall, f1 = do_stats(get_citations_multiple(sources, i, j), print_res=False)
                print(f'Cites depth: {i:02d} | Cited depth: {j:02d} | Pr {precision:.2f} Re {recall:.2f} F1 {f1:.2f}')
            except ZeroDivisionError:
                print("Tried dividing by zero, skipping")

def prep_edges_list(links):
    edges_list_for_csv = []
    for i in links:
        to_add = i[0][1:]+','+[1][1:]
        edges_list_for_csv.append(to_add)
    with open('./extracted_edges_network.csv', 'w', newline='') as f:
        for entries in edges_list_for_csv:
            f.write(entries)
            f.write("\n")
    print('Extracted edges of the network')

def generate_network(sources, filter_degree=2, filter_network=True):
    links, _ = get_citations_structure_multiple(sources, cites_depth=2,
            cited_depth=2)
    g = nx.Graph()
    g.add_edges_from(links)

    # filter by degree
    if filter_network:
        filtered = {node for node, degree in g.degree if degree >= filter_degree}
        do_stats(filtered)
    else:
        filtered = {node for node, degree in g.degree}
        do_stats(filtered)
    # saving graph created above in gefx format
    nx.write_gex(g, "./networkfile.gexf")
    return filtered

def visualise_network(width=1280, height=720, filtered, source):
    nt = Network(height, width)
    nt.add_nodes(filtered)
    nt.add_edges([(source, target) for source, target in g.edges if source in
        filtered and target in filtered])
    nt.show('filtered.html')
