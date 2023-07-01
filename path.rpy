# Note: Python 2 compatible

init -99999 python: # type: ignore

    #########################
    #                       #
    #  Imports and utility  #
    #                       #
    #########################

    def __import_renpy(): # type: ignore
        # Mock import for the linter
        global renpy
        from ... import renpy

    import re
    try:
        from time import perf_counter
    except:
        from time import time as perf_counter

    try:
        from typing import Any, Callable, Dict, Iterator, List, Optional, Protocol, Tuple, Type, TypeVar, Union
        T = TypeVar('T')
        class NextGetter(Protocol):
            def __call__(self, node, skip_first=True):
                # type: (renpy.ast.Node, bool) -> Union[renpy.ast.Node, None] # type: ignore
                pass
    except:
        pass

    def print(*args):
        if len(args) > 1:
            renpy.display.log.write(" ".join(str(x) for x in args))
        else:
            renpy.display.log.write(str(args[0]))
    
    def lookup_or_none(name):
        # type: (str) -> Union[renpy.ast.Node, None]
        try:
            return renpy.game.script.lookup_or_none(name) # type: ignore
        except AttributeError:
            try:
                return renpy.game.script.lookup(name) # type: ignore
            except renpy.script.ScriptError:
                return None

    KEEP = (
        renpy.ast.Menu,
        renpy.ast.If,
        renpy.ast.Python,
        type(None),
    ) # type: Tuple[Type, ...]
    PYTHON_IGNORE = [
        r"^game_version\s*=.+",
        r"^renpy\.music\..+",
        r"^renpy\.end_replay\(\)",
    ]



    ##################
    #                #
    #  Custom nodes  #
    #                #
    ##################

    class Node:
        def __init__(self, origin, parents, callers):
            # type: (renpy.ast.Node, List[Edge], List[Union[Call, None]]) -> None
            self.origin = origin
            self.parents = parents
            self.children = [] # type: List[Edge]
            self.callers = callers

        def generate_children(self, graph, next_getter):
            # type: (Graph, NextGetter) -> List[Edge]
            # Warning: Does not add the child not the edge to the graph
            if self.origin is None:
                return []
            next_ = next_getter(self.origin)
            if next_ is None:
                return []
            child = graph.get_node(next_) or _new_node(graph, next_, [])
            edge = Edge(self, child)
            edge = graph.get_edge(edge) or edge
            return [edge]

        def propagate(self, graph, next_getter):
            # type: (Graph, NextGetter) -> Iterator[Edge]
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

    class Edge:
        def __init__(self, start, end, condition="True", choice=None):
            # type: (Node, Node, str, Optional[str]) -> None
            self.start = start
            self.end = end
            self.condition = condition
            self.choice = choice

        def __eq__(self, other):
            # type: (Edge) -> bool
            if not isinstance(other, Edge):
                return False
            if self.start != other.start or self.end != other.end:
                return False
            if self.choice != other.choice or self.condition != other.condition:
                return False
            return True

        def __repr__(self):
            # type: () -> str
            label = ""
            if self.choice is not None:
                label = repr(self.choice)
            if self.condition != "True":
                label += " if " + self.condition
            elif self.choice is None and len(self.start.children) > 1:
                label = "else"
            label = label.strip()
            if label:
                return "{} -> {} -> {}".format(self.start, label, self.end)
            return "{} -> {}".format(self.start, self.end)

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
                callers = [self.nodes.index(caller) if caller is not None else caller for caller in node.callers]
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


    class Label(Node):
        origin = None # type: renpy.ast.Label # type: ignore

    class Jump(Node):
        origin = None # type: renpy.ast.Jump # type: ignore

        def generate_children(self, graph, next_getter):
            # type: (Graph, NextGetter) -> List[Edge]
            target = lookup_or_none(self.origin.target) # type: renpy.ast.Node # type: ignore
            next_ = next_getter(target, False)
            if next_ is None:
                return []
            child = graph.get_node(next_) or _new_node(graph, next_, [])
            edge = Edge(self, child)
            edge = graph.get_edge(edge) or edge
            return [edge]

    class Call(Node):
        origin = None # type: renpy.ast.Call # type: ignore

        def generate_children(self, graph, next_getter):
            # type: (Graph, NextGetter) -> List[Edge]
            label = lookup_or_none(self.origin.label) # type: renpy.ast.Node # type: ignore
            next_ = next_getter(label, False)
            if next_ is None:
                return []
            child = graph.get_node(next_) or _new_node(graph, next_, [])
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
                        child = graph.get_node(next_) or _new_node(graph, next_, [])
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
            edges = []
            for text, condition, block in self.origin.items:
                next_ = next_getter(block[0], False)
                if next_ is None:
                    return []
                child = graph.get_node(next_) or _new_node(graph, next_, [])
                edge = Edge(self, child, condition, text)
                edge = graph.get_edge(edge) or edge
                edges.append(edge)
            return edges

    class If(Node):
        origin = None # type: renpy.ast.If # type: ignore

        def generate_children(self, graph, next_getter):
            # type: (Graph, NextGetter) -> List[Edge]
            edges = []
            entries = self.origin.entries[:]
            if not any(condition == "True" for condition, _ in entries):
                # If there is not else (= default), don't forget to still continue
                entries.append(("True", [self.origin.next]))
            for condition, block in entries:
                next_ = next_getter(block[0], False)
                if next_ is None:
                    return []
                child = graph.get_node(next_) or _new_node(graph, next_, [])
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

    #####################
    #                   #
    #  Conversion from  #
    #  renpy to custom  #
    #                   #
    #####################

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

    def convert(start_rpynode, end_rpynode, next_getter):
        # type: (renpy.ast.Node, Union[renpy.ast.Node, None], NextGetter) -> Graph

        # TODO: Stop at end_node

        graph = Graph()
        start = _new_node(graph, start_rpynode, [])
        start.callers = [None] # type: ignore # Error on type for no reason, works if empty list and then append None
        todo = [start] # type: List[Node]

        while todo:
            node = todo.pop(0)
            if isinstance(node, renpy.ast.Node) and not graph.has_node(node):
                # Should not happen, just in case
                node = _new_node(graph, node, [])

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

        return graph



    #########################
    #                       #
    #  Path simplification  #
    #                       #
    #########################

    def _remove_node(node, graph):
        # type: (Node, Graph) -> None
        old_parents = node.parents[:]
        old_children = node.children[:]

        # Remove old
        graph.nodes.remove(node)
        for parent_edge in old_parents:
            parent_edge.start.children.remove(parent_edge)
            graph.edges.remove(parent_edge)
        for child_edge in old_children:
            child_edge.end.parents.remove(child_edge)
            graph.edges.remove(child_edge)

        # Deal with call stacks
        if isinstance(node.origin, renpy.ast.Return):
            uniques = [] # type: list[Edge]
            for child_edge in old_children:
                for other in uniques:
                    if child_edge.start == other.start and child_edge.end == other.end:
                        break
                else:
                    uniques.append(child_edge)
            old_children = uniques
            # TODO: Remove edges that have a non-matching call stack

        # Create new ones
        for parent_edge in old_parents:
            for child_edge in old_children:

                if parent_edge.start == child_edge.end:
                    # Looping on itself: skipping
                    continue

                # TODO: Temporary hack to simply the condition
                pc, cc = parent_edge.condition, child_edge.condition
                if pc == "False" or cc == "False":
                    condition = "False"
                elif pc != "True" and cc != "True" and pc != cc:
                    condition = pc + " and " + cc
                elif cc != "True":
                    condition = cc
                else:
                    condition = pc

                edge = Edge(parent_edge.start, child_edge.end, condition, parent_edge.choice)
                parent_edge.start.children.append(edge)
                child_edge.end.parents.append(edge)
                graph.edges.append(edge)

    def simplify(graph, simplify_menus=False):
        # type: (Graph, bool) -> None

        changed = True
        while changed:
            changed = False

            # Remove unwanted nodes
            for node in graph.nodes[:]:
                keep = isinstance(node.origin, KEEP)
                if not keep and (not node.parents and node.children):
                    keep = True # Keep root of branches
                if isinstance(node.origin, renpy.ast.Python) and any(re.match(pattern, node.origin.code.source) for pattern in PYTHON_IGNORE):
                    keep = False # System command or unwanted assignation # TODO
                if isinstance(node.origin, renpy.ast.UserStatement) and node.origin.get_name() in ("show screen", "call screen"):
                    keep = True # Screen call
                if not node.parents and not node.children:
                    keep = False # Single node with no connections

                if keep:
                    continue
                _remove_node(node, graph)
                changed = True

            # Simplify ifs (and menus) and remove them
            for node in graph.nodes[:]:
                if not (isinstance(node.origin, renpy.ast.If) or (simplify_menus and isinstance(node.origin, renpy.ast.Menu))):
                    continue
                grouped_edges = {} # type: dict[Node, list[Edge]]
                for edge in node.children:
                    if edge.end not in grouped_edges:
                        grouped_edges[edge.end] = []
                    grouped_edges[edge.end].append(edge)

                for end, group in grouped_edges.items():
                    if len(group) == 1:
                        continue
                    # TODO: Temporary hack to simply the condition
                    conditions = [
                        edge.condition for edge in group
                        if edge.condition != "False"
                    ] or ["False"]
                    if "True" in conditions:
                        condition = "True"
                    elif len(conditions) == 1:
                        condition = conditions[0]
                    else:
                        condition = "(" + " or ".join(conditions) + ")"

                    for edge in group:
                        node.children.remove(edge)
                        end.parents.remove(edge)
                        graph.edges.remove(edge)
                    edge = Edge(node, end, condition)
                    node.children.append(edge)
                    end.parents.append(edge)
                    graph.edges.append(edge)

                # If there aren't too many edges, remove it
                if len(node.children) <= 1: # or len(node.parents) * len(node.edges) < MAX_IF_REDUCTION: # FIXME
                    if len(node.children) > 1 and any(isinstance(parent.start.origin, renpy.ast.Menu) for parent in node.parents):
                        continue # Cannot be removed because it would split the menu's choice
                    _remove_node(node, graph)
                    changed = True

        pass

        # FIXME: Find the bug and remove the line (After some returns, some edges are not simplified correctly and the edge remain)
        # edges = [edge for edge in edges if edge.start in nodes and edge.end in nodes] # TEMP



    ###############
    #             #
    #  Execution  #
    #             #
    ###############

    def timed(name, function, *args, **kwargs):
        # type: (str, Callable[..., T], *Any, **Any) -> T
        print("==========")

        start = perf_counter()
        result = function(*args, **kwargs)
        end = perf_counter()

        dt = end - start
        h, m, s = dt // 3600, (dt // 60) % 60, dt % 60

        if h:
            print("{} took {}h {:02}m {:02.0f}s".format(name, h, m, s))
        elif m:
            print("{} took {:02}m {:05.2f}s".format(name, m, s))
        else:
            print("{} took {:06.3f}s".format(name, s))
        print("==========")
        return result

    def main():
        start_node = lookup_or_none("start")
        end_node = None

        with open("graph.json", "r") as f:
            serialized = f.read()
        graph = timed("Deserialization", Graph.deserialize, serialized)
        # graph = timed("Generation", convert, start_node, end_node, _next__minimalist)
        timed("Simplification", simplify, graph, simplify_menus=True)
        timed("Vizualization", Graph.vizualize, graph)
        serialized = timed("Serialization", Graph.serialize, graph)
        with open("graph.json", "w") as f:
            f.write(serialized)

        renpy.quit() # type: ignore

    main() # type: ignore