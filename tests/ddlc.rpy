init -99998 python:
    start_node = renpy.game.script.lookup("start")
    end_node = None

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

    graph = timed("Generation", convert, start_node, end_node, _next__minimalist)
    timed("Simplification", simplify, graph, simplify_menus=True)
    timed("Vizualization", Graph.vizualize, graph)

    renpy.quit()