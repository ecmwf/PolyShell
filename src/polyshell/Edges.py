import numpy as np
import heapq
import scipy.spatial as spt
import numpy.typing as npt

#TODO unit tests ...
class CharShape:
    """Class to represent boundary edges of a vertex cloud, along with a Maxheap.

    It remembers their ordering, and ensure the ordering is maintained on operations.
    Additionally, it handles converting between local simplical coordinates (where edge in 
    simplex?), global simplical coordinates, and internal ordering of the edges.
    Specifically, ids is an array running from 0 to the number of current edges.
    All mutable arrays follow this order, but the heap just spits outs the respective index
    based on length. When an old edge is removed, the id at that position is set to -1 (yes,
    bad for memory).

    Attributes
    ---
    ids : List[int]
        matches lengths to edge properties, -1 for edge that were removed
    points : List[List[float]]
        stores all the input points, used for calculating lengths
    simplices : ndarray[ndarray[int]]
        stores all the input simplices, i.e. arrays of 3 point indices
    bound_edges : List[List[int]] 
        the array of all the edges forming the current boundary
    simp_ids : List[int]  
        an array matching edges to their respective member simplex
    bound_points : Set[int] 
        a *set* of all point indices forming the boundary
    heap : List[Tuple(float, int)]
        an implicit heap of edge length, edge index, heaped by length

    Methods
    ---

    """
    def __init__(self, tri : spt.Delaunay, points : npt.NDArray):
        """Creates the CharacteristicShape class and all its necessary arrays.

        Args:
            tri (_type_): a scipy delaunay triangulation, neighbours and simplices as attributes
            points (_type_): _description_
        """
        #this gives us the ordering with respect to the total points
        #the following are supposed to be immutable 
        #this allows us to remember the input data
        self.points = points
        #we store the simplices
        self.simplices = tri.simplices
        #and the neighbours
        self.neighbors = tri.neighbors

        #we seek the boundary edges
        #i.e. which simplices are such that their kth node has no neighbour?
        #then take the (k+1) mod 3 and (k+2) mod 3 nodes
        be_1 = tri.simplices[tri.neighbors[:,0] == -1][:,[1,2]]
        be_2 = tri.simplices[tri.neighbors[:,1] == -1][:,[0,2]]
        be_3 = tri.simplices[tri.neighbors[:,2] == -1][:,[0,1]]

        #an array of simplex ids
        simp_range = np.arange(tri.simplices.shape[0])
        #which simplex is such that its kth vertex has no opposite neighbour?
        #this can be moved to a function
        simp_1_id = simp_range[tri.neighbors[:,0] == -1]
        simp_2_id = simp_range[tri.neighbors[:,1] == -1]
        simp_3_id = simp_range[tri.neighbors[:,2] == -1]

        #and their coprime nodes
        #take the node opposite the boundary edge
        be_1_prime = tri.simplices[tri.neighbors[:,0] == -1][:,0]
        be_2_prime = tri.simplices[tri.neighbors[:,1] == -1][:,1]
        be_3_prime = tri.simplices[tri.neighbors[:,2] == -1][:,2]


        #TODO is it more efficien to have python arrays, since each iteration they grow?
        #importantly, each array is actually a list of indices, corresponding to points

        #a nx2 matrix, where the columns are star and end of the edge
        self.bound_edges = np.concatenate([be_1, be_2, be_3])

        #which simplex is the ith edge at?
        #TODO move this to a function
        self.simp_ids = list(np.concatenate([simp_1_id, simp_2_id, simp_3_id]))

        #what is the simplex's 3rd node for the ith edge?
        #TODO move this to a function
        self.coprime_node = list(np.concatenate([be_1_prime, be_2_prime, be_3_prime]))

        #and the boundary points
        self.bound_points = set(np.unique(self.bound_edges.flatten()))

        #now we get the lengths
        lengths = np.linalg.norm(self.points[self.bound_edges[:,0]] - \
                                      self.points[self.bound_edges[:,1]], axis = 1)
        
        #convert to list for more efficient appending?
        self.bound_edges = self.bound_edges.tolist()
        #it's a minheap, so need to reverse sizes ... going to be confusing
        self.ids = np.arange(len(self.bound_edges))
        self.heap = [(-lengths[i], self.ids[i]) for i in self.ids]

        #this is inplace
        heapq.heapify(self.heap)
    
    #TODO fix the weird self crossings: just check if the edge is on the original boundary
    def check_regularity(self, index: int) -> bool:
        """Is the coprime node of the ith edge on the boundary or not?
        Args:
            index (int): idx of the edge

        Returns:
            bool: regular or not
        """
        if self.coprime_node[index] in self.bound_points:
            return False
        if np.abs((self.bound_edges[index][0] - self.bound_edges[index][1])) == 1:
            return False
        
        return True
    
    #TODO break this up more
    #TODO why hold coprime node in array? quite cheap to check with a function
    def reveal(self, index):
        """Creates 2 new edges by removing the boundary_edge at index.

        Assumes regularity was checked.

        Args:
            index (_type_): position of edge with respect
        """
        #what is the edge's coprime node
        coprime_node = self.coprime_node[index]
        #which simplex is the edge in?
        simpInd = self.simp_ids[index]
        #and which edge is this?
        old_edge = self.bound_edges[index]
        #local numbering of edge and coprime node in their simplex
        #(edge[0], edge[1], coprimeNode)
        vertexOrdering = self.edgeSimplexOrder(old_edge, simpInd)

        #revealing gives us 2 new edges
        edge1 = [old_edge[0], coprime_node]
        edge2 = [old_edge[1], coprime_node]

        #and gives us 2 new lengths
        length1 = np.linalg.norm(self.points[old_edge[0]] - self.points[coprime_node])
        length2 = np.linalg.norm(self.points[old_edge[1]] - self.points[coprime_node])

        #the edge's simplex is going to be opposite its coprime node
        #by regularity, we can assume there is going to be a neighbour existing
        simp_id1 = self.neighbors[simpInd,vertexOrdering[1]][0]
        simp_id2 = self.neighbors[simpInd,vertexOrdering[0]][0]
        
        #to get the new coprime nodes
        local_order1 = self.edgeSimplexOrder(edge1, simp_id1)
        local_order2 = self.edgeSimplexOrder(edge2, simp_id2)

        coprime1 = self.simplices[simp_id1][local_order1[2]][0]
        coprime2 = self.simplices[simp_id2][local_order2[2]][0]

        #now update everything
        #really should be deleting here, this is so ugly
        #TODO oopsie memory leak
        self.updateHeap(index, length1, length2)
        self.updateArrays((edge1, edge2), (simp_id1, simp_id2), (coprime1, \
                                            coprime2), coprime_node)

    
    def updateArrays(self, edges, simp_ids, coprime_nodes, bound_point):
        """_summary_

        Args:
            edges (_type_): _description_
            simp_ids (_type_): _description_
            coprime_nodes (_type_): _description_
            bound_point (_type_): _description_
        """
        self.bound_edges.append(edges[0]) # type: ignore
        self.bound_edges.append(edges[1]) # type: ignore
        self.simp_ids.append(simp_ids[0])
        self.simp_ids.append(simp_ids[1])
        self.coprime_node.append(coprime_nodes[0])
        self.coprime_node.append(coprime_nodes[1])
        self.bound_points.add(bound_point)

    def iterate(self, print_index = False):
        __, id = heapq.heappop(self.heap)
        if print_index == True:
            print(self.bound_edges[id])
        if self.check_regularity(id):
            self.reveal(id)
        
    def updateHeap(self, old_index, length1, length2):
        new_id1 = self.ids.size
        new_id2 = self.ids.size + 1
        #this might be better with just a fixed numpy array, and a ticker remembering max
        #TODO
        self.ids = np.append(self.ids, [new_id1, new_id2])
        self.ids[old_index] = -1
        heapq.heappush(self.heap,(-length1, new_id1))
        heapq.heappush(self.heap, (-length2, new_id2))
        
    def edgeSimplexOrder(self, edge, simpInd):
        """local numbering of edge vertices with respect to a simplex

        Args:
            edge (tuple): of the form (point_idx1, point_idx2)
            simpInd (int): which simplex are does the edge belong in?

        Returns:
            tuple: 3-element tuple, with local numbering of the edge origin, destination,
            and coprime node. each is an int from 0 to 2.
        """
        edge = edge
        simplex = self.simplices[simpInd]
        ids = (np.where(simplex == edge[0])[0], np.where(simplex ==edge[1])[0])
        coprime_id = 3 - ids[0] - ids[1]
        return (ids[0], ids[1], coprime_id)
