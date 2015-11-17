import numpy as np


class OctreeError(Exception):
    """Generic octree error."""


class OctreeBoundsError(OctreeError):
    """Raised when a point is inserted outside of the bounds of the octree."""


class _Frame(object):
    """
    Dummy frame class.

    In a real application, it might normally include the pose at which the image
    was taken (perhaps as a quaternion), its timestamp, a thumbnail, and the
    full image. A quality score might also be added, based on blur.

    Parameters
    ----------
    position : ndarray
        The x, y, z coordinates at which the frame was taken.
    contents : any
        Any content.

    Attributes
    ----------
    position : ndarray
        The x, y, z coordinates at which the frame was taken.
    contents : any
        Any content.

    """
    def __init__(self, position, contents):
        self.position = np.asarray(position)
        self.contents = contents

    def __repr__(self):
        return "Pic ({}): {}".format(self.position.tolist(), self.contents)


class Data(object):
    """
    A data class.

    It represents the data value of a given node. If there is no data, the
    position field is also cleared.

    Attributes
    ----------
    is_empty
    position : ndarray
        The x, y, z position of the data stored at the node.
    contents : list of _Frame
        A list of all frames added to the octree at this point, in the order
        they were added. A full implementation might sort the frames by
        quality.

    """
    def __init__(self):
        self.position = None
        self.contents = []

    def __len__(self):
        """The length of the `contents` field."""
        return len(self.contents)

    def __repr__(self):
        return "Data ({}): {}".format(self.position, self.contents)

    @property
    def is_empty(self):
        """
        Check whether the data has no content.

        Returns
        -------
        bool
            True if the data has no content.
        """
        return not len(self.contents)

    def append(self, item):
        """
        Append an item to `contents`.

        Parameters
        ----------
        item : _Frame
            Any item with a position attribute.

        """
        if self.position is None:
            self.position = np.asarray(item.position)
        elif any(item.position != self.position):
            raise OctreeError("Wrong position")
        self.contents.append(item)

    def pop(self):
        """Return and remove the last item in `contents`."""
        return self.contents.pop()

    def clear(self):
        """Reset the `Data` object to its default state."""
        self.position = None
        self.contents = []


class Octree(object):
    """
    An octree class.

    In this implementation, octrees are perfectly cubical, and they can only
    accept one data point. If more than one data point is inserted, the octree
    splits. If an item is removed, and that node's siblings have no data either,
    it currently does not merge those nodes to form the parent node.

    Changes to the boundaries, the centre, or the length update the other
    variables simultaneously.

    Parameters
    ----------
    centre : ndarray
        The x, y, z coordinates of the centre of the octree.
    half_dim : float
        Half the length of one side of the cube.
    parent : Octree, optional
        The parent of the octree. Default (for the root node) is None.

    Attributes
    ----------
    centre
    half_dim
    side
    bound_min
    bound_max
    parent : Octree
        The parent of the octree. Root nodes have a parent of None.
    children: dict of {str: Octree}
        The dictionary containing the list of children, one at each octant. The
        dictionary keys are three characters long. The characters represent the
        value of the x, y, and z coordinates respectively. If a coordinate's
        value is less than the centre's, it will be displayed as "-";
        coordinates with a value greater than or equal to the centre's are
        displayed as "+".
    data : Data
        The data contained in the octree.

    """
    def __init__(self, centre, half_dim, parent=None):
        self.parent = parent
        self._centre = np.asarray(centre)
        self._half_dim = half_dim
        self._bound_min = self.centre - self.half_dim * np.ones(3)
        self._bound_max = self.centre + self.half_dim * np.ones(3)
        self._n_items = 0

        self.children = {
            "---": None,
            "--+": None,
            "-+-": None,
            "-++": None,
            "+--": None,
            "+-+": None,
            "++-": None,
            "+++": None
        }
        self.data = Data()

    def __len__(self):
        """Return the number of items in the subtree."""
        return self._n_items

    def __repr__(self):
        return "[{}D{}C{}I]".format(0 if self.data.is_empty else 1,
                                    0 if self.children else 1,
                                    self._n_items)

    def _get_octant(self, point):
        """
        Return the octant that the point is in.

        The characters represent the value of the x, y, and z coordinates
        respectively. If a coordinate's value is less than the centre's, it will
        be displayed as "-"; coordinates with a value greater than or equal to
        the centre's are displayed as "+".

        Parameters
        ----------
        point : ndarray
            The x, y, z coordinates of the point whose quadrant is to be found.

        Returns
        -------
        str
            The octant that the point is in.

        """
        pos = point >= self.centre
        return "".join("+" if i else "-" for i in pos)

    def _is_leaf(self):
        """
        Check whether the node is a leaf node.

        A leaf node does not have any children, and may contain data.

        Returns
        -------
        bool
            True if the node is a leaf node.

        """
        return self.children["---"] is None

    def _check_bounds(self, point):
        """
        Check whether a point's coordinates are within the node boundaries.

        Returns
        -------
        bool
            True if the point is within the bounding box.

        """
        return self._check_box(point, self.bound_min, self.bound_max)

    def _check_box(self, point, bound_min, bound_max):
        """
        Check whether a point's coordinates are within a box boundaries.

        Returns
        -------
        bool
            True if the point is within the bounding box.

        """
        return all(point >= bound_min) and all(point <= bound_max)

    def _node_outside_box(self, node, bound_min, bound_max):
        """
        Check whether a node is completely outside a box boundaries.

        Returns
        -------
        bool
            True if a node is completely outside the box boundaries.

        """
        node_bmin = node.bound_min
        node_bmax = node.bound_max
        return any(node_bmin > bound_max) or any(node_bmax < bound_min)

    def insert(self, item):
        """
        Insert an item into the tree.

        The item is inserted into a relevant leaf node; it splits the node as
        necessary in order to maintain the constraint of one position per node.

        Parameters
        ----------
        item : _Frame
            The item to be inserted. The item must have a position attribute.

        Raises
        ------
        OctreeBoundsError
            If the item coordinates are outside the boundaries of the octree.

        Notes
        -----
        This algorithm is recursive. Whenever it enters a new node, it calls
        the function again.

        """
        if not self._check_bounds(item.position) and self.parent is None:
            raise OctreeBoundsError

        if self._is_leaf():
            # Data can be added.
            if self.data.is_empty or all(self.data.position == item.position):
                # A node may only have data at one position.
                self.data.append(item)
            else:
                # Split the node by creating new children.
                new_half_dim = self.half_dim / 2
                for child in self.children:
                    new_centre = self.centre.copy()
                    for i, sign in enumerate(child):
                        multiplier = 1 if sign == "+" else -1
                        new_centre[i] += new_half_dim * multiplier
                    self.children[child] = Octree(new_centre,
                                                  new_half_dim,
                                                  parent=self)

                # The old data contents must be moved into a child node.
                old_data_octant = self._get_octant(self.data.position)
                self.children[old_data_octant].extend(self.data.contents)
                self.data.clear()

                # The new data is inserted recursively into the child node.
                new_data_octant = self._get_octant(item.position)
                self.children[new_data_octant].insert(item)

        else:
            # This is an interior node. We need to go the leaf.
            octant = self._get_octant(item.position)
            self.children[octant].insert(item)

        self._n_items += 1

    def extend(self, items):
        """
        Extend the octree with a sequence of items.

        This function inserts each item in the sequence into its respective node
        on the tree.

        Parameters
        ----------
        items : list of _Frame
            An iterable of items to be added.

        Raises
        ------
        OctreeBoundsError
            If at least one item in the list is outside the bounding box of the
            octree.

        """
        for item in items:
            self.insert(item)

    def get(self, point):
        """
        Retrieve the data at a given point.count

        Parameters
        ----------
        point : ndarray
            The x, y, z coordinates of the point whose data is to be retrieved.

        Returns
        -------
        data : Data
            The data requested.

        Raises
        ------
        KeyError
            If the data does not exist.

        Notes
        -----
        This method is recursive.

        """
        if self._is_leaf():
            if self.data.is_empty or any(self.data.position != point):
                raise KeyError("Could not find point.")
            else:
                return self.data

        octant = self._get_octant(point)
        return self.children[octant].get(point)

    def remove(self, point, clear=False):
        """
        Remove the last item from a point.

        Parameters
        ----------
        point : ndarray
            The x, y, z coordinates of the point to be removed.
        clear : bool, optional
            If True, empties the contents of the data at the point. Default is
            False.

        Raises
        ------
        KeyError
            If the data does not exist.

        """
        data = self.get(point)
        node = self

        if clear:
            n_cleared = len(data.contents)
            data.clear()

            while node is not None:
                node._n_items -= n_cleared
                node = node.parent
        else:
            data.pop()
            if data.is_empty:
                data.clear()
            while node is not None:
                self._n_items -= 1
                node = node.parent

    def get_points_in_box(self, bound_min, bound_max):
        """
        Get all the points in a given box.

        Parameters
        ----------
        bound_min : ndarray
            The x, y, z coordinates of the vertex with the minimum values.
        bound_max : ndarray
            The x, y, z coordinates of the vertex with the maximum values.

        Yields
        ------
        Data
            The data at the points that fall within the bounding box.

        Notes
        -----
        This method is recursive.

        """
        if self._is_leaf():
            if not self.data.is_empty:
                if self._check_box(self.data.position, bound_min, bound_max):
                    yield self.data
        else:
            for child in self.children:
                if self._node_outside_box(self.children[child],
                                          bound_min, bound_max):
                    continue
                for point in self.children[child].get_points_in_box(bound_min,
                                                                    bound_max):
                    yield point

    def get_nearest(self, point):
        """Get the point nearest to a given point."""
        raise NotImplementedError

    @property
    def centre(self):
        """
        Return the x, y, z coordinates of the centre of the octree.

        Returns
        -------
        ndarray
            The x, y, z coordinates of the centre of the octree.

        """
        return self._centre

    @centre.setter
    def centre(self, values):
        """
        Move the x, y, z coordinates of the centre of the octree.

        Update the bounds simultaneously.

        Parameters
        ----------
        values : ndarray
            The coordinates of the centre.

        """
        self._centre = np.asarray(values)
        self._bound_min = self.centre - self.half_dim * np.ones(3)
        self._bound_max = self.centre + self.half_dim * np.ones(3)

    @property
    def half_dim(self):
        """
        Return half the length of one side of the cube.

        Returns
        -------
        float
            Half the length of one side of the cube.

        """
        return self._half_dim

    @half_dim.setter
    def half_dim(self, value):
        """
        Set the length of half one side of the cube, while keeping the centre.

        Update the bounds simultaneously.

        Parameters
        ----------
        value : float
            The new length of half of one side.

        """
        self._half_dim = value
        self._bound_min = self.centre - self.half_dim * np.ones(3)
        self._bound_max = self.centre + self.half_dim * np.ones(3)

    @property
    def side(self):
        """
        Return the length of one side of the octree.

        Returns
        -------
        float
            The length of one side of the octree.

        """
        return self.half_dim * 2

    @property
    def bound_min(self):
        """
        Return the coordinates of the vertex with the minimum values.

        Returns
        -------
        ndarray
            The x, y, z coordinates of the vertex with the minimum values.

        """
        return self._bound_min

    @bound_min.setter
    def bound_min(self, values):
        """
        Set the minimum boundary of the octree while keeping the maximum.

        Update the centre and half_dim lengths simultaneously.

        Parameters
        ----------
        values : ndarray
            The x, y, z coordinates of the vertex with the minimum values.

        """
        self._bound_min = np.asarray(values)
        self._centre = (self.bound_max + self.bound_min) / 2
        self._half_dim = (self.bound_min - self.bound_min) / 2

    @property
    def bound_max(self):
        """
        Return the coordinates of the vertex with the maximum values.

        Returns
        -------
        ndarray
            The x, y, z coordinates of the vertex with the maximum values.

        """
        return self._bound_max

    @bound_max.setter
    def bound_max(self, values):
        """
        Set the maximum boundary of the octree while keeping the minimum.

        Update the centre and half_dim lengths simultaneously.

        Parameters
        ----------
        values : ndarray
            The x, y, z coordinates of the vertex with the maximum values.

        """
        self._bound_max = np.asarray(values)
        self._centre = (self.bound_max + self.bound_min) / 2
        self._half_dim = (self.bound_min - self.bound_min) / 2


if __name__ == "__main__":
    o = Octree((0, 0, 0), 100)
    item1 = _Frame((20, 30, 40), "An item 1")
    item1_copy = _Frame((20, 30, 40), "An item 1 copy")
    item2 = _Frame((30, 30, 40), "An item 2")
    item3 = _Frame((40, 30, 40), "An item 3")

    o.insert(item1)
    o.insert(item1_copy)
    o.insert(item2)
    o.insert(item3)
    print(list(o.get_points_in_box((0, 0, 0), (25, 35, 50))))
