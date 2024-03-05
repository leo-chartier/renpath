import re
from renpath import renpy
from .typing import Tuple, Type

from .classes.edge import Edge

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global Graph, Node
    from classes.graph import Graph
    from classes.node import Node



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
    r"^renpy\.pause\(",
    r"^persistent\.sprite_time",
    r"^volume\(",
	r"^set_mode_adv\(\)",
	r"^set_mode_nvl\(\)",
]



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
            if isinstance(node.origin, renpy.ast.UserStatement) and node.origin.get_name() in ("show screen", "hide screen", "call screen"):
                keep = True # Screen call
            if not node.parents and not node.children:
                keep = True # Single node with no connections

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
