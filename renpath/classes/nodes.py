from renpath import renpy
from .node import Node
from ..utility import lookup_or_none
from ..screens import Screen, get_screen
from ..typing import Dict, Iterator, List, Optional

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Edge, Graph, NextGetter
    from edge import Edge
    from graph import Graph
    from ..node_generation import NextGetter



class Label(Node):
    origin = None # type: renpy.ast.Label # type: ignore

class Jump(Node):
    origin = None # type: renpy.ast.Jump # type: ignore

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        from ..node_generation import _new_node # Local to prevent circular imports
        from .edge import Edge # Local to prevent circular imports
        target = lookup_or_none(self.origin.target) # type: renpy.ast.Node # type: ignore
        next_ = next_getter(target, False)
        if next_ is None:
            return []
        child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
        edge = Edge(self, child)
        edge = graph.get_edge(edge) or edge
        return [edge]

class Call(Node):
    origin = None # type: renpy.ast.Call # type: ignore

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        from ..node_generation import _new_node # Local to prevent circular imports
        from .edge import Edge # Local to prevent circular imports
        label = lookup_or_none(self.origin.label) # type: renpy.ast.Node # type: ignore
        next_ = next_getter(label, False)
        if next_ is None:
            return []
        child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
        edge = Edge(self, child)
        edge = graph.get_edge(edge) or edge
        return [edge]

class Return(Node):
    origin = None # type: renpy.ast.Return # type: ignore

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        return [] # Done during propagation

    def propagate(self, graph, next_getter):
        # type: (Graph, NextGetter) -> Iterator[Edge]
        from ..node_generation import _new_node # Local to prevent circular imports
        from .edge import Edge # Local to prevent circular imports
        for caller in self.callers:
            if caller is None:
                continue # TODO: To main menu
            for parent in caller.callers:
                label = "" if parent is None else parent.origin.label

                found = None
                for edge in self.children:
                    if edge.condition == label:
                        found = edge
                        break
                next_ = next_getter(caller.origin.next) # type: ignore
                if found is None and next_ is not None:
                    child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
                    edge = Edge(self, child, choice=label)
                    edge = graph.get_edge(edge) or edge
                    yield edge
                    found = edge

                if found is not None and parent not in found.end.callers:
                    found.end.callers.append(parent)
                    for edge in found.end.propagate(graph, next_getter):
                        yield edge

class Menu(Node):
    origin = None # type: renpy.ast.Menu # type: ignore

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        from ..node_generation import _new_node # Local to prevent circular imports
        from .edge import Edge # Local to prevent circular imports
        edges = []
        for text, condition, block in self.origin.items:
            if block is None:
                continue
            next_ = next_getter(block[0], False)
            if next_ is None:
                return []
            child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
            edge = Edge(self, child, condition, text)
            edge = graph.get_edge(edge) or edge
            edges.append(edge)
        return edges

class If(Node):
    origin = None # type: renpy.ast.If # type: ignore

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        from ..node_generation import _new_node # Local to prevent circular imports
        from .edge import Edge # Local to prevent circular imports
        edges = []
        entries = self.origin.entries[:]
        if not any(condition == "True" for condition, _ in entries):
            # If there is not else (= default), don't forget to still continue
            entries.append(("True", [self.origin.next]))
        for condition, block in entries:
            next_ = next_getter(block[0], False)
            if next_ is None:
                return []
            child = graph.get_node(next_) or _new_node(graph, next_, [], dict(self.screens))
            edge = Edge(self, child, condition)
            edge = graph.get_edge(edge) or edge
            edges.append(edge)
        return edges

class Python(Node):
    origin = None # type: renpy.ast.Python # type: ignore

    @property
    def is_mainmenu(self):
        # type: () -> bool
        return self.origin.code.source.lstrip().startswith("MainMenu")

    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        if self.is_mainmenu:
            return []
        return super(Python, self).generate_children(graph, next_getter)

    def __repr__(self):
        # type: () -> str
        if self.is_mainmenu:
            return "END"
        return super(Python, self).__repr__()

class UserStatement(Node):
    origin = None # type: renpy.ast.Python # type: ignore

    def __init__(self, origin, parents, callers, screens):
        # type: (renpy.ast.Node, List[Edge], List[Optional[Call]], Dict[str, Screen]) -> None
        super(UserStatement, self).__init__(origin, parents, callers, screens)

    def keep(self):
        # type: () -> bool
        return self.origin.get_name() in ["show screen", "hide screen", "call screen"]
    
    def generate_children(self, graph, next_getter):
        # type: (Graph, NextGetter) -> List[Edge]
        if self.origin.get_name() == "show screen":
            name = self.origin.parsed[1]["name"]
            if name not in self.screens:
                screen = get_screen(name)
                self.screens[name] = screen
        if self.origin.get_name() == "hide screen":
            name = self.origin.parsed[1]["name"]
            if name in self.screens:
                self.screens.pop(name)
        if self.origin.get_name() == "call screen":
            name = self.origin.parsed[1]["name"]
            screen = get_screen(name)
            return screen.get_connections(self, graph, next_getter)
        return super(UserStatement, self).generate_children(graph, next_getter)

INSTANT = (Label, Jump, Call, Return, If)
