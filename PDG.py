from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import *
import networkx as nx
import matplotlib.pyplot as plt


#Example generic traversal
def walk(node, depth=0):
    print(" " * depth + node.__class__.__name__)

    for child in node.children():
        walk(child, depth + 1)


class PDGExtractor:

    def __init__(self):
        self.graph = nx.DiGraph()
        self.control_stack = []

    ####################################################################
    # Main AST Visitor
    ####################################################################

    def visit(self, node):

        if node is None:
            return

        if isinstance(node, Assign):
            self.handle_assign(node)

        elif isinstance(node, BlockingSubstitution):
            self.handle_substitution(node)

        elif isinstance(node, NonblockingSubstitution):
            self.handle_substitution(node)

        elif isinstance(node, IfStatement):
            self.handle_if(node)
            return

        elif isinstance(node, CaseStatement):
            self.handle_case(node)
            return

        for child in node.children():
            self.visit(child)

    ####################################################################
    # Assignment Processing
    ####################################################################

    def handle_assign(self, node):

        lhs_signals = self.extract_targets(node.left)
        rhs_signals = self.extract_sources(node.right)

        self.add_dependencies(lhs_signals, rhs_signals)

    def handle_substitution(self, node):

        lhs_signals = self.extract_targets(node.left)
        rhs_signals = self.extract_sources(node.right)

        self.add_dependencies(lhs_signals, rhs_signals)

    ####################################################################
    # Control Dependencies
    ####################################################################

    def handle_if(self, node):

        controllers = self.extract_sources(node.cond)

        self.control_stack.extend(controllers)

        if node.true_statement:
            self.visit(node.true_statement)

        for _ in controllers:
            self.control_stack.pop()

        if node.false_statement:

            self.control_stack.extend(controllers)

            self.visit(node.false_statement)

            for _ in controllers:
                self.control_stack.pop()

    def handle_case(self, node):

        controllers = self.extract_sources(node.comp)

        self.control_stack.extend(controllers)

        for case_item in node.caselist:

            if hasattr(case_item, "statement"):
                self.visit(case_item.statement)

        for _ in controllers:
            self.control_stack.pop()

    ####################################################################
    # Graph Construction
    ####################################################################

    def add_dependencies(self, lhs_signals, rhs_signals):

        for lhs in lhs_signals:

            self.graph.add_node(lhs)

            #
            # DATA DEPENDENCIES
            #
            for rhs in rhs_signals:

                self.graph.add_node(rhs)

                if rhs != lhs:

                    self.graph.add_edge(
                        rhs,
                        lhs,
                        dep_type="data"
                    )

            #
            # CONTROL DEPENDENCIES
            #
            for ctrl in self.control_stack:

                self.graph.add_node(ctrl)

                if ctrl != lhs:

                    self.graph.add_edge(
                        ctrl,
                        lhs,
                        dep_type="control"
                    )

    ####################################################################
    # LHS Extraction
    ####################################################################

    def extract_targets(self, node):

        targets = []

        if node is None:
            return targets

        if isinstance(node, Identifier):
            targets.append(node.name)

        elif isinstance(node, Lvalue):
            targets.extend(self.extract_targets(node.var))

        elif isinstance(node, Pointer):
            targets.extend(self.extract_targets(node.var))

        elif isinstance(node, Partselect):
            targets.extend(self.extract_targets(node.var))

        elif isinstance(node, Concat):

            for item in node.list:
                targets.extend(self.extract_targets(item))

        return targets

    ####################################################################
    # RHS Extraction
    ####################################################################

    def extract_sources(self, node):

        sources = []

        if node is None:
            return sources

        #
        # Signal references
        #
        if isinstance(node, Identifier):
            sources.append(node.name)

        #
        # Wrapper nodes
        #
        elif isinstance(node, Lvalue):
            sources.extend(self.extract_sources(node.var))

        elif isinstance(node, Rvalue):
            sources.extend(self.extract_sources(node.var))

        #
        # Memory access
        #
        elif isinstance(node, Pointer):

            sources.extend(self.extract_sources(node.var))
            sources.extend(self.extract_sources(node.ptr))

        #
        # Slice
        #
        elif isinstance(node, Partselect):

            sources.extend(self.extract_sources(node.var))

        #
        # Concatenation
        #
        elif isinstance(node, Concat):

            for item in node.list:
                sources.extend(self.extract_sources(item))

        #
        # Generic recursive traversal
        #
        else:

            for child in node.children():
                sources.extend(self.extract_sources(child))

        return sources

    ####################################################################
    # Utility Functions
    ####################################################################

    def print_edges(self):

        for src, dst, attrs in self.graph.edges(data=True):

            dep_type = attrs.get("dep_type", "unknown")

            print(
                f"{src} --[{dep_type}]--> {dst}"
            )

    def get_data_edges(self):

        return [
            (u, v)
            for u, v, d in self.graph.edges(data=True)
            if d.get("dep_type") == "data"
        ]

    def get_control_edges(self):

        return [
            (u, v)
            for u, v, d in self.graph.edges(data=True)
            if d.get("dep_type") == "control"
        ]

    def export_graphml(self, filename):

        nx.write_graphml(
            self.graph,
            filename
        )

def main():
    try:

        file_name = input("Enter file name: ")
        ast, directives = parse([file_name])
        #ast.show()
        #walk(ast)

        extractor = PDGExtractor()
        extractor.visit(ast)
        extractor.print_edges()
    except Exception as e:
        print(f"An erro occured: {e}")
        print(f"Error type: {type(e).__name__}")




if __name__ == "__main__":
    main()
