from ..typing import Optional

def __mock_imports(): # type: ignore
    # Mock imports for the linter
    global renpy, Node
    from renpath import renpy
    from node import Node



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
