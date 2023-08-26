from renpath import renpy
from ..screens import Screen
from ..typing import Dict, Iterator, List, Optional

from .edge import Edge

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Call, Graph, NextGetter
    from nodes import Call
    from graph import Graph
    from ..node_generation import NextGetter



class Node(object):
    def __init__(self, origin, parents, callers, screens):
        # type: (renpy.ast.Node, List[Edge], List[Optional[Call]], Dict[str, Screen]) -> None
        self.origin = origin
        self.parents = parents
        self.children = [] # type: List[Edge]
        self.callers = callers
        self.screens = screens

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        # Warning: Does not add the child not the edge to the graph
        from ..node_generation import _new_node # Local to prevent circular imports
        if self.origin is None:
            return []
        next_ = next_getter(self.origin)
        if next_ is None:
            return []
        child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
        edge = Edge(self, child)
        edge = graph.get_edge(edge) or edge
        return [edge]

    def propagate(self, graph, next_getter):
        # type: (Graph, NextGetter) -> Iterator[Edge]
        from .nodes import Call # Local to prevent circular imports
        from .nodes import Return
        todo = [self]
        while todo:
            current = todo.pop(0)
            if isinstance(current, Return):
                for edge in current.propagate(graph, next_getter):
                    yield edge
                # TODO: Merge here to prevent stackoverflow ?
                continue
            for edge in current.children:
                added = False
                for caller in current.callers:
                    if isinstance(current, Call):
                        if current in current.unwarp_calls():
                            # Already looping
                            continue
                        caller = current
                    if caller not in edge.end.callers:
                        edge.end.callers.append(caller)
                        added = True
                if added:
                    todo.append(edge.end)
                    # for next_edge in edge.end.propagate(graph, next_getter):
                    #     yield next_edge

    def unwarp_calls(self):
        # type: () -> List[Call]
        todo = [self]
        done = []
        while todo:
            current = todo.pop()
            if current is None:
                continue
            for caller in current.callers:
                if caller is None:
                    continue
                if caller not in done:
                    done.append(caller)
                    todo.append(caller)
        return done

    def __eq__(self, other):
        # type: (Union[Node, renpy.ast.Node]) -> bool
        if isinstance(other, Node):
            return self.origin == other.origin
        elif isinstance(other, renpy.ast.Node):
            return self.origin == other
        return False

    def __hash__(self):
        # type: () -> int
        return hash(self.origin)

    def __repr__(self):
        # type: () -> str
        if self.origin is None:
            return self.__class__.__name__ + " (None)"
        try:
            code = self.origin.get_code().strip()
        except:
            try:
                with open(self.origin.filename, "r") as f:
                    code = f.readlines()[self.origin.linenumber - 1].strip()
            except:
                code = self.origin
        return "{} ({}): {} ({}, {})".format(
            self.__class__.__name__,
            self.origin.__class__.__name__,
            repr(code),
            self.origin.filename,
            self.origin.linenumber
        )
