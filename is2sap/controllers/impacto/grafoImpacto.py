#Simple graph implementation:
#Directed or undirected graph
#Without weight in the edges, yet
#Edges and vertices can't be repeated
#DFS and BFS added
 
class Graph:
    def __init__(self):
        self.graph = {}
    
    def __get_iterator(self, obj):
        try:
            iterator = iter(obj)
        except TypeError:
            iterator = (obj, )
        return iterator
 
    def add_vertex(self, vertex):
        """
            Add vertex to the graph
        """
        for i in self.__get_iterator(vertex):
            self.graph[i] = set()
 
    def del_vertex(self, vertex):
        """
            Remove the vertex if it's in the graph
            And all the edges
        """
        vertex = set(self.__get_iterator(vertex))
        for i in vertex:
            if i in self.graph:
                self.graph.pop(i)
        for i in self.graph.iterkeys():
            self.graph[i] -= vertex
        
    def is_vertex(self, vertex):
        """
            Return True if vertex is in the graph
            otherwise return False
        """
        if vertex in self.graph:
            return True
        return False
 
    def add_edge(self, src, dest, undirected=False):
        """
            Add a edge from src to dest
            Or add edges from the cartesian product of src cross dest
            Example: add_edge((1, 2, 3), (2, 3))
            Add the edges:
                (1, 2)
                (1, 3)
                (2, 3)
                (3, 2)
        """
        for s in self.__get_iterator(src):
            if s not in self.graph:
                self.graph[s] = set()
            for d in self.__get_iterator(dest):
                if s == d:
                    continue
                if d not in self.graph:
                    self.graph[d] = set()
                self.graph[s].add(d)
                if undirected:
                    self.graph[d].add(s)
 
    def delete_edge(self, src, dest):
        """
            Remove the edge from src to dest
            Or the edges of the cartesian product of src cross dest
            Example: delete_edge((1, 2, 3), (2, 3))
            Will delete the edges:
                (1, 2)
                (1, 3)
                (2, 3)
                (3, 2)
        """
        dest = set(self.__get_iterator(dest))
        src = set(self.__get_iterator(src))
        for i in src:
            if i in self.graph:
                self.graph[i] -= dest
 
    def get_edge(self, vertex):
        """
            Return the neighbors of a vertex if the vertex is in the graph
        """
        return self.graph[vertex]
    
    def walk(self, source, topdown=False):
        """
        Walk through the graph:
            DFS(Deep First Search)if topdown = True
            Otherwise BFS(Breath First Search)
        """
        v = set()
        l = [source]
        if topdown:
            print "DFS:"
        else:
            print "BFS:"
        v.add(source)
        while l:
            node = l.pop()
            print node,
            for i in self.graph[node]:
                if i not in v:
                    v.add(i)
                    if topdown:
                        l.append(i)
                    else:
                        l.insert(0, i)
                else:
                    print "Ya fue visitado:", i                    
        print ""

 
    def __str__(self):
        #Print the vertex
        s = "Vertex -> Edges\n"
        for k, v in self.graph.iteritems():
            s += "%-6s -> %s\n" % (k, v)
        return s
 
if __name__ == '__main__':            
    graph = Graph()
    graph.add_edge(1, 2)
    graph.add_edge(2, 3)
    graph.add_edge(3, 4)
    graph.add_edge(4, 5)
    graph.add_edge(3, 1)
    hayciclo = graph.walk(1)
    print hayciclo
    print graph
