from ast import Name
from renpath import renpy
from .classes.edge import Edge
from .utility import lookup_or_none

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Graph, List, NextGetter, Node, Tuple, Union
    from node_generation import NextGetter
    from .classes.graph import Graph
    from .classes.node import Node
    from .typing import List, Tuple, Union

def parse_actions(keywords):
    # type: (List[Tuple[str, object]]) -> List[Tuple[str, str | None]]
    # Don't you love some spaghetti code :yum:
    filtered = list(filter(lambda t: t[0] == "action", keywords))
    if not filtered:
        return []
    action_str = filtered[0][1]

    ccache = renpy.pyanalysis.CompilerCache()
    evaluation = ccache.ast_eval(action_str)
    if isinstance(evaluation, Name):
        ast_list = [] # TODO: Hotfix for DDLC, needs to verify utility
    elif hasattr(evaluation, "elts"):
        ast_list = evaluation.elts
    elif evaluation.func.id == "__renpy__list__":
        ast_list = evaluation.args[0].elts
    else:
        ast_list = [evaluation]
    
    actions = []
    for keyword in ast_list:
        # renpy.display.log.write(keyword) # TEMP
        id_ = keyword.func.id
        if id_ == "With":
            continue
        if id_ == "Function":
            renpy.display.log.write("TODO: Function call in screen") # TODO
            continue
        if keyword.args:
            actions.append((id_, keyword.args[0].s))
        actions.append((id_, None))
    return actions

class Screen:
    def __init__(self, origin):
        # type: (renpy.display.screen.Screen) -> None
        self.origin = origin
        self.base_screen = self.origin.function # type: renpy.sl2.slast.SLScreen
        # renpy.display.log.write("Found screen: " + self.base_screen.name) # TEMP
        self.base_screen.analyze_screen()
    
    def get_connections(self, start, graph, next_getter, edges=None, statement=None, condition=None):
        # type: (Node, Graph, NextGetter, Union[List[Edge], None], Union[renpy.sl2.slast.SLNode, None], Union[str, None]) -> List[Edge]
        from .node_generation import _new_node

        if edges is None:
            edges = []
        if statement is None:
            statement = self.base_screen
        if statement is None:
            return [] # TEMP: Used because the linter is dumb

        if isinstance(statement, renpy.sl2.slast.SLScreen):
            for child in statement.children:
                edges += self.get_connections(start, graph, next_getter, edges, child, condition)
        
        elif isinstance(statement, renpy.sl2.slast.SLDefault):
            renpy.display.log.write("TODO: Screen Default [" + start.origin.filename + "#" + str(start.origin.linenumber) + "]") # TODO
            
        elif isinstance(statement, renpy.sl2.slast.SLDisplayable):
            # renpy.display.log.write("Displayable at: " + start.origin.filename + "#" + str(start.origin.linenumber)) # TEMP
            actions = parse_actions(statement.keyword)
            for type_, value in actions:
                if value is None:
                    continue # TEMP: Used because the linter is dumb
                if type_ == "Jump":
                    # renpy.display.log.write("Added connection " + str(start) + " -> " + value) # TEMP
                    # Copied the code over from Jump.generate_children
                    target = lookup_or_none(value) # type: renpy.ast.Node
                    next_ = next_getter(target, False)
                    if next_ is None:
                        return []
                    child = graph.get_node(next_) or _new_node(graph, next_, [], dict(start.screens))
                    edge = Edge(start, child, choice="Jump " + value)
                    edge = graph.get_edge(edge) or edge
                    edges.append(edge)
                    # By not adding the edge to the graph right away, the destination node will automatically be scanned
            for child in statement.children:
                edges += self.get_connections(start, graph, next_getter, edges, child, condition)
        
        elif isinstance(statement, renpy.sl2.slast.SLFor):
            renpy.display.log.write("TODO: Screen For [" + start.origin.filename + "#" + str(start.origin.linenumber) + "]") # TODO
        
        elif isinstance(statement, renpy.sl2.slast.SLIf):
            for new_condition, block in statement.entries:
                if condition is not None:
                    new_condition = "(" + condition + ") and (" + new_condition + ")"
                for child in block.children:
                    # TODO: Condition
                    edges += self.get_connections(start, graph, next_getter, edges, child, new_condition)
        
        elif isinstance(statement, renpy.sl2.slast.SLPython):
            renpy.display.log.write("TODO: Screen Python [" + start.origin.filename + "#" + str(start.origin.linenumber) + "]") # TODO
        
        elif isinstance(statement, renpy.sl2.slast.SLShowIf):
            renpy.display.log.write("TODO: Screen ShowIf [" + start.origin.filename + "#" + str(start.origin.linenumber) + "]") # TODO
        
        elif isinstance(statement, renpy.sl2.slast.SLUse):
            renpy.display.log.write("TODO: Screen Use [" + start.origin.filename + "#" + str(start.origin.linenumber) + "]") # TODO
        
        else:
            raise NotImplementedError("cannot use screen statement " + str(type(statement)) + "yet")
        
        return edges

__screens = {} # type: dict[str, Screen]

def get_screen(name):
    # type: (str) -> Screen
    if name in __screens:
        return __screens[name]
    # renpy.display.log.write(renpy.display.screen.screens) # TEMP
    raw = renpy.display.screen.screens[(name, None)]
    screen = Screen(raw)
    __screens[name] = screen
    return screen
