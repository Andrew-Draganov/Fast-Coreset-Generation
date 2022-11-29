import numpy as np
import matplotlib as plt
from sklearn.random_projection import SparseRandomProjection
import sys
sys.setrecursionlimit(5000)

class HST:
    def __init__(self, points, root=True, depth=0, cell_path=''):
        """
        Initialize Hierarchically Separated Tree
        input:
            P : numpy array, shape (n x d)
        """
        self.points = points
        self.n, self.d = points.shape
        self.depth = depth
        self.max_depth = 0
        self.cell_path = cell_path
        self.root = root # Only true if this is the root of the tree

        self.parent = None
        self.left_child = None
        self.right_child = None

        if self.root:
            self.get_delta()
            self.random_shift()

    def get_delta(self):
        """ Get maximum distance in points along one axis """
        axis_dists = np.array([np.max(self.points[:, i]) - np.min(self.points[:, i]) for i in range(1, self.d)])
        self.delta = np.max(axis_dists)

    def random_shift(self):
        """ Apply a random shift to points so that all points are in the [0, 2 * Delta]^d box """
        # Move pointset to all-positive values
        self.points[:, 1:] -= np.min(self.points[:, 1:], axis=1, keepdims=True)
        self.points[:, 1:] += 1e-3

        # Apply a random shift in [0, delta]
        self.points[:, 1:] += np.random.random([1, self.d - 1]) * self.delta

    def has_left_child(self):
        return self.left_child != None

    def has_right_child(self):
        return self.right_child != None

def get_split_vars(split_d, delta, d):
    next_d = split_d + 1
    next_delta = delta
    if next_d >= d + 1:
        next_d = 1
        next_delta = delta / 2

    return next_d, next_delta

def fit_tree(points):
    point_to_cell_dict = {}
    root = HST(points)
    # g_* indicates global variable name for fit_tree()
    #   - this way it won't be confused with variables in _fit()
    g_split_d = 1
    g_delta = root.delta
    g_prev_split = np.zeros([root.d + 1])

    def _fit(node, split_d, delta, prev_split):
        if len(node.points) == 1:
            node.max_depth = node.depth
            point_to_cell_dict[node.points[0, 0]] = node
            return

        left_inds = node.points[:, split_d] <= (prev_split[split_d] + delta)
        left_points = node.points[left_inds]
        right_points = node.points[np.logical_not(left_inds)]

        next_d, next_delta = get_split_vars(split_d, delta, node.d)

        if len(left_points) >= 1:
            left_split = np.copy(prev_split)
            node.left_child = HST(left_points, root=False, depth=node.depth+1, cell_path=node.cell_path + 'l')
            _fit(node.left_child, next_d, next_delta, left_split)
            node.left_child.parent = node
            left_depth = node.left_child.max_depth
        else:
            left_depth = 0

        if len(right_points) >= 1:
            right_split = np.copy(prev_split)
            right_split[split_d] += delta
            node.right_child = HST(right_points, root=False, depth=node.depth+1, cell_path=node.cell_path + 'r')
            _fit(node.right_child, next_d, next_delta, right_split)
            node.right_child.parent = node
            right_depth = node.right_child.max_depth
        else:
            right_depth = 0
            right_id = 0

        node.max_depth = max(left_depth, right_depth)

    _fit(root, g_split_d, g_delta, g_prev_split)
    return root, point_to_cell_dict

def tree_dist(ptc_dict, a, b, root):
    """
    root -- base of the tree
    a, b -- two points that we want the tree-distance between
    """
    cell_a = ptc_dict[a]
    cell_b = ptc_dict[b]
    substring = ''
    i = 0
    while cell_a.cell_path[i] == cell_b.cell_path[i]:
        substring += cell_a.cell_path[i]
        i += 1

    print(substring)
    print(cell_a.cell_path, cell_b.cell_path)


if __name__ == '__main__':
    points = np.random.randn(5000, 1000)
    k = 10
    eps = 1e-1
    d = np.ceil(np.log(k) / (eps ** 2)).astype(np.int32)
    jl_proj = SparseRandomProjection(d)

    points = jl_proj.fit_transform(points)
    indices = np.expand_dims(np.arange(len(points)), -1)
    points = np.concatenate((indices, points), axis=1)
    root, ptc_dict = fit_tree(points)
    print(root.max_depth)

    tree_dist(ptc_dict, 10, 30, root)
