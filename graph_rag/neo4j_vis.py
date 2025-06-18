from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path
import networkx as nx
from pyvis.network import Network
from dotenv import load_dotenv

load_dotenv(override=True)

# Default connection parameters for visualization.
DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USER = "neo4j"
DEFAULT_PASSWORD = "testpass"
DEFAULT_QUERY = "MATCH p=()-->() RETURN p;"
DEFAULT_OUTPUT_FILE = "test.html"


def visualize_neo4j_graph(
    uri=DEFAULT_URI,
    user=DEFAULT_USER,
    password=DEFAULT_PASSWORD,
    query=DEFAULT_QUERY,
    output_file=DEFAULT_OUTPUT_FILE,
):
    """
    Visualizes a graph from Neo4j query results and saves it as an HTML file using pyvis.
    """

    def graph_from_cypher(data):
        G = nx.MultiDiGraph()

        def add_node(node):
            u = node.element_id
            if G.has_node(u):
                return
            G.add_node(u, labels=node._labels, properties=dict(node))

        def add_edge(relation):
            for node in (relation.start_node, relation.end_node):
                add_node(node)
            u = relation.start_node.element_id
            v = relation.end_node.element_id
            eid = relation.element_id
            if G.has_edge(u, v, key=eid):
                return
            G.add_edge(u, v, key=eid, type_=relation.type, properties=dict(relation))

        def handle_path(path):
            for node in path.nodes:
                add_node(node)
            for rel in path.relationships:
                add_edge(rel)

        for d in data:
            for entry in d.values():
                if isinstance(entry, Node):
                    add_node(entry)
                elif isinstance(entry, Relationship):
                    add_edge(entry)
                elif isinstance(entry, Path):
                    handle_path(entry)
                else:
                    raise TypeError(f"Unrecognized object: {entry}")
        return G

    def serialize_node_labels(G):
        for node, data in G.nodes(data=True):
            if "labels" in data and isinstance(data["labels"], frozenset):
                data["labels"] = list(data["labels"])

    def serialize_edge_properties(G):
        for u, v, k, data in G.edges(data=True, keys=True):
            for key, value in data.items():
                if isinstance(value, frozenset):
                    data[key] = list(value)

    # Connect to Neo4j
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        data = list(session.run(query))
    G = graph_from_cypher(data)
    serialize_node_labels(G)
    serialize_edge_properties(G)
    net = Network(height="100vh", width="100vw", directed=True)
    net.from_nx(G)
    # Customize nodes and edges for visualization
    for node in net.nodes:
        node_id = node["id"]
        properties = G.nodes[node_id]["properties"]
        node["label"] = properties.get("id", "Unknown")
        node["title"] = (
            f"Entity Type: {properties.get('entity_type', 'Unknown')}\n"
            f"Description: {properties.get('description', 'No description')}\n"
            f"Source ID: {properties.get('source_id', 'Unknown')}"
        )
        if properties.get("entity_type") == "PERSON":
            node["color"] = "lightblue"
    for edge in net.edges:
        start = edge["from"]
        end = edge["to"]
        for key in G[start][end]:
            edge_data = G.edges[start, end, key]
            edge["label"] = edge_data.get("type_", "")
            edge["title"] = (
                f"Description: {edge_data['properties'].get('description', 'No description')}\n"
                f"Weight: {edge_data['properties'].get('weight', 1)}\n"
                f"Order: {edge_data['properties'].get('order', 'Unknown')}"
            )
            edge["value"] = edge_data["properties"].get("weight", 1)
    net.save_graph(output_file)
    print(f"Graph visualization saved to {output_file}")
    driver.close()
