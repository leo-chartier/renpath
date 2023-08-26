from renpath import renpy
from .typing import List, Union

from .classes.graph import Graph
from .node_generation import NextGetter, _new_node

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Node
    from classes.node import Node



def convert(start_rpynode, end_rpynode, next_getter):
    # type: (renpy.ast.Node, Union[renpy.ast.Node, None], NextGetter) -> Graph

    # TODO: Stop at end_node

    graph = Graph()
    start = _new_node(graph, start_rpynode, [], {})
    start.callers = [None] # type: ignore # Error on type for no reason, works if empty list and then append None
    todo = [start] # type: List[Node]

    while todo:
        node = todo.pop(0)
        if isinstance(node, renpy.ast.Node) and not graph.has_node(node):
            # Should not happen, just in case
            node = _new_node(graph, node, [], {})

        for edge in node.generate_children(graph, next_getter):
            child = edge.end
            if not graph.has_edge(edge) and child not in todo:
                # If the edge exists, it may create an infinite loop: scan again
                todo.append(child)

            graph.add_node(child)
            graph.add_edge(edge)
            if edge not in edge.start.children:
                edge.start.children.append(edge)
            if edge not in child.parents:
                child.parents.append(edge)

        # Propagate the call stack and get any new returning edges
        for edge in node.propagate(graph, next_getter):
            child = edge.end
            if not graph.has_edge(edge) and child not in todo:
                # If the edge exists, it may create an infinite loop: scan again
                todo.append(child)

            graph.add_node(child)
            graph.add_edge(edge)
            if edge not in edge.start.children:
                edge.start.children.append(edge)
            if edge not in child.parents:
                child.parents.append(edge)
        
        # TODO: Generate screen connections

    return graph
