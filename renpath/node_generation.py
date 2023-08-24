from renpath import renpy
from .typing import Dict, Protocol, Type, Union

from .classes.nodes import *

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Edge, Graph
    from classes.edge import Edge
    from classes.graph import Graph



try:
    class NextGetter(Protocol):
        def __call__(self, node, skip_first=True):
            # type: (renpy.ast.Node, bool) -> Union[renpy.ast.Node, None] # type: ignore
            pass
except:
    pass



NODES_MAPPING = {
    renpy.ast.Label: Label,
    renpy.ast.Jump: Jump,
    renpy.ast.Call: Call,
    renpy.ast.Return: Return,
    renpy.ast.Menu: Menu,
    renpy.ast.If: If,
    renpy.ast.Python: Python,
    # renpy.ast.Node: Node
} # type: Dict[Type[renpy.ast.Node], Type[Node]]



def _next__all(node, skip_first=True):
    # type: (renpy.ast.Node, bool) -> Union[renpy.ast.Node, None]
    """Keeps every node"""
    if node is None:
        return None
    if skip_first:
        node = node.next # type: ignore
    return node

def _next__normal(node, skip_first=True):
    # type: (renpy.ast.Node, bool) -> Union[renpy.ast.Node, None]
    """Remove special nodes"""
    if node is None:
        return None
    if skip_first:
        node = node.next # type: ignore
    while isinstance(node, (
        renpy.ast.Translate,
        renpy.ast.EndTranslate,
        renpy.ast.Pass,
    )):
        node = node.next # type: ignore
    return node

def _next__minimalist(node, skip_first=True):
    # type: (Union[renpy.ast.Node, None], bool) -> Union[renpy.ast.Node, None]
    """Keeps branching nodes only"""
    if node is None:
        return None
    if skip_first:
        node = node.next
    while not isinstance(node, (
        renpy.ast.Label,
        renpy.ast.Jump,
        renpy.ast.Call,
        renpy.ast.Return,
        renpy.ast.Menu,
        renpy.ast.If,
        renpy.ast.Python,
        type(None),
    )):
        node = node.next
    return node

def _new_node(graph, rpynode, parents):
    # type: (Graph, renpy.ast.Node, List[Edge]) -> Node
    for rpytype, nodetype in NODES_MAPPING.items():
        if isinstance(rpynode, rpytype):
            break
    else:
        nodetype = Node
    node = nodetype(rpynode, parents, [])
    graph.add_node(node)
    return node
