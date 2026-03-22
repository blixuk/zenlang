class DependencyGraph:
    def __init__(self):
        self.nodes = set() # Set of absolute file paths
        self.edges = {}    # Adjacency list: path -> [imported_paths]
        
    def add_node(self, path: str):
        self.nodes.add(path)
        if path not in self.edges:
            self.edges[path] = []
            
    def add_edge(self, from_path: str, to_path: str):
        if from_path not in self.nodes:
            self.add_node(from_path)
        if to_path not in self.nodes:
            self.add_node(to_path)
            
        self.edges[from_path].append(to_path)
        
    def has_node(self, path: str) -> bool:
        return path in self.nodes

    def get_compilation_order(self) -> list[str]:
        """
        Returns a topological sort of the graph, or at least a valid 
        compilation order (dependencies first).
        """
        visited = set()
        order = []
        
        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self.edges.get(node, []):
                visit(neighbor)
            order.append(node)
            
        for node in self.nodes:
            visit(node)
            
        return order
