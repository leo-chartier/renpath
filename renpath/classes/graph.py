from renpath import renpy
from ..typing import Dict, List, Union

from .edge import Edge
from .node import Node



class Graph:
    def __init__(self):
        # type: () -> None
        self.nodes = [] # type: List[Node]
        self.edges = [] # type: List[Edge]

    def get_node(self, node):
        # type: (Union[Node, renpy.ast.Node, None]) -> Union[Node, None]
        for node2 in self.nodes:
            if node == node2:
                return node2
        return None

    def get_edge(self, edge):
        # type: (Edge) -> Union[Edge, None]
        for edge2 in self.edges:
            if edge == edge2:
                return edge2
        return None

    def has_node(self, node):
        # type: (Union[Node, renpy.ast.Node]) -> bool
        return self.get_node(node) is not None

    def has_edge(self, edge):
        # type: (Edge) -> bool
        return self.get_edge(edge) is not None

    def add_node(self, node):
        # type: (Node) -> None
        if isinstance(node, renpy.ast.Node):
            pass # TODO
        if not isinstance(node, Node):
            return
        if not self.has_node(node):
            self.nodes.append(node)

    def add_edge(self, edge):
        # type: (Edge) -> None
        if not isinstance(edge, Edge):
            return
        if not self.has_edge(edge):
            self.edges.append(edge)

    def vizualize(self):
        # Since it is very unlikely that pygraphviz will install successfully,
        # we generate the .dot file by hand.
        lines = ["digraph path {"]

        for i, node in enumerate(self.nodes):
            label = repr(node).replace("\"", "\\\"").replace("\n", "\\n")
            # TODO: Better label
            lines.append("\t{} [label=\"{}\"]".format(i, label))

        for edge in self.edges:
            try:
                i = self.nodes.index(edge.start)
                j = self.nodes.index(edge.end)
            except IndexError:
                continue
            label = ""
            if edge.choice is not None:
                label = edge.choice
            if edge.condition != "True":
                label += "\nif " + edge.condition
            elif edge.choice is None and len(edge.start.children) > 1:
                label = "else"
            label = label.strip().replace('"', '\\"').replace("\n", "\\n")
            if label:
                lines.append("\t{} -> {} [label=\"{}\"]".format(i, j, label))
            else:
                lines.append("\t{} -> {}".format(i, j))

        lines.append("}")
        with open("path.dot", "w") as f:
            f.write("\n".join(lines))
    
    def serialize(self):
        # type: () -> str
        import json

        nodes = []
        for node in self.nodes:
            location = node.origin.filename + '#' + str(node.origin.linenumber)
            parents = [self.edges.index(parent) for parent in node.parents]
            children = [self.edges.index(child) for child in node.children]
            callers = [self.nodes.index(caller) if caller is not None else None for caller in node.callers if caller in self.nodes or caller is None]
            data = {
                "location": location,
                "parents": parents,
                "children": children,
                "callers": callers
            }
            nodes.append(data)

        edges = []
        for edge in self.edges:
            start = self.nodes.index(edge.start)
            end = self.nodes.index(edge.end)
            data = {
                "start": start,
                "condition": edge.condition,
                "choice": edge.choice,
                "end": end
            }
            edges.append(data)

        serial = json.dumps({
            "nodes": nodes,
            "edges": edges
        })
        return serial
    
    @staticmethod
    def deserialize(serial):
        # type: (str) -> Graph
        import json
        from ..node_generation import _new_node # Local to prevent circular imports

        data = json.loads(serial)
        graph = Graph()

        located = {} # type: Dict[str, renpy.ast.Node]
        for raw_node in data["nodes"]:
            located[raw_node["location"]] = None # type: ignore
        for rpynode in renpy.game.script.all_stmts: # type: ignore
            location = rpynode.filename + "#" + str(rpynode.linenumber)
            if isinstance(rpynode, renpy.ast.Pass):
                continue
            if location in located and located[location] is None:
                located[location] = rpynode

        for raw_node in data["nodes"]:
            rpynode = located[raw_node["location"]]
            node = _new_node(graph, rpynode, [])
            graph.add_node(node)
        
        for raw_edge in data["edges"]:
            start = graph.nodes[raw_edge["start"]]
            end = graph.nodes[raw_edge["end"]]
            edge = Edge(start, end, raw_edge["condition"], raw_edge["choice"])
            graph.add_edge(edge)
        
        for raw_node in data["nodes"]:
            rpynode = located[raw_node["location"]]
            node = graph.get_node(rpynode)
            if node is None:
                continue
            for i in raw_node["parents"]:
                parent = graph.edges[i]
                node.parents.append(parent)
            for i in raw_node["children"]:
                child = graph.edges[i]
                node.children.append(child)

        return graph
