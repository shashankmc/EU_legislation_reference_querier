from SPARQLWrapper import SPARQLWrapper, JSON

def get_citations(source_celex, cites_depth=1, cited_depth=1):
    """
    Gets all the citations one to X steps away. Hops can be specified as either
    the source document citing another (defined by `cites_depth`) or another document
    citing it (`cited_depth`). Any numbers higher than 1 denote that new source document
    citing a document of its own.

    This specific implementation does not care about intermediate steps, it simply finds
    anything X or fewer hops away without linking those together.
    """
    sparql = SPARQLWrapper('https://publications.europa.eu/webapi/rdf/sparql')
    sparql.setReturnFormat(JSON)
    sparql.setQuery('''
        prefix cdm: <http://publications.europa.eu/ontology/cdm#>
        prefix xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT * WHERE
        {
        {
            SELECT ?name2 WHERE {
                ?doc cdm:resource_legal_id_celex "%s"^^xsd:string .
                ?doc cdm:work_cites_work{1,%i} ?cited .
                ?cited cdm:resource_legal_id_celex ?name2 .
            }
        } UNION {
            SELECT ?name2 WHERE {
                ?doc cdm:resource_legal_id_celex "%s"^^xsd:string .
                ?cited cdm:work_cites_work{1,%i} ?doc .
                ?cited cdm:resource_legal_id_celex ?name2 .
            }
        }
        }''' % (source_celex, cites_depth, source_celex, cited_depth))
    ret = sparql.queryAndConvert()

    targets = set()
    for bind in ret['results']['bindings']:
        target = bind['name2']['value']
        targets.add(target)
    targets = set([el for el in list(targets) if el.startswith('3')]) #Filters the list. Filtertype: '3'=legislation, '6'=case law.

    return targets


def get_citations_multiple(sources, cites_depth=1, cited_depth=1, union=True):
    """
    Gets citations coming from multiple sources (given as a list of CELEX IDs).
    By default gets the union of all the resulting CELEXes, but of interest
    might be the intersect instead, returning only documents that are common
    between all the sources.
    """
    results = [get_citations(source, cites_depth, cited_depth) for source in sources]
    results.append(sources) #ensures that source nodes (ie starting points) are included in nodes list

    if union:
        return set().union(*results)
    else:
        start_set = results[0]
        if len(sources) > 1:
            return start_set.union(*results[1:])
        else:
            return start_set

def get_citations_structure(source, cites_depth=1, cited_depth=1, dont_repeat=set()):
    if cites_depth > 0 and cited_depth > 0:
        cites, nodes1 = get_citations_structure(source, cites_depth, 0, dont_repeat)
        cited, nodes2 = get_citations_structure(source, 0, cited_depth, dont_repeat)
        return cites.union(cited), nodes1.union(nodes2)


    new_cites_depth = max(cites_depth - 1, 0)
    new_cited_depth = max(cited_depth - 1, 0)

    dont_repeat = dont_repeat.union({source})

    links = set()
    nodes = {source}
    targets = get_citations(source, min(cites_depth, 1), min(cited_depth, 1))

    for target in targets:
        nodes.add(target)
        # We're looking for citations from the source
        if cites_depth > 0:
            links.add((source, target))
        # Or to the source
        else:
            links.add((target, source))

        if new_cites_depth or new_cited_depth and target not in dont_repeat:
            new_links, new_nodes = get_citations_structure(target, new_cites_depth, new_cited_depth)
            links = links.union(new_links)
            nodes = nodes.union(new_nodes)

    return links, nodes


def get_citations_structure_multiple(sources, cites_depth=1, cited_depth=1):
    links = set()
    nodes = set(sources)
    for source in sources:
        if source.startswith('3'):
            new_links, new_nodes = get_citations_structure(source, cites_depth, cited_depth)
            links = links.union(new_links)
            nodes = nodes.union(new_nodes)
#            nodes = set([el for el in list(nodes) if el.startswith('3')]) #Filters the list. Filtertype: '3'=legislation, '6'=case law.
    return links, nodes


def do_stats(nodes, print_res=True):
    nodes = set(nodes)

    precision = len(nodes.intersection(expert_docs)) / float(len(nodes))
    recall = len(nodes.intersection(expert_docs)) / float(len(expert_docs))
    f1 = 2 * (precision * recall) / (precision + recall)
    if print_res:
        print(f'Total nodes found in search: {len(nodes)}')
        print(f'Precision: {precision}\nRecall: {recall}\nF1: {f1}')

        print(f'Common nodes ({len(nodes.intersection(expert_docs))}): {nodes.intersection(expert_docs)}')
        print(f'Missed nodes ({len(expert_docs - nodes)}): {expert_docs - nodes}')
        print(f"Extra nodes (ones it shouldn't ({len(nodes - expert_docs)}): {nodes - expert_docs}")
    return (precision, recall, f1)

