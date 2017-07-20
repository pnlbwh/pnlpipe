import abc, six
from itertools import groupby


@six.add_metaclass(abc.ABCMeta)
class Node(object):
    @abc.abstractproperty
    def children(self):
        """Children nodes"""

    @abc.abstractproperty
    def tag(self):
        """A tag attached to the node"""

    @property
    def value(self):
        """A value attached to the node"""
        return None


class Leaf(Node):
    def __init__(self, tag, value=None):
        self._tag = tag
        self._value = value

    @property
    def tag(self):
        return self._tag

    @property
    def children(self):
        return []

    @property
    def value(self):
        return self._value


def concat(l):
    return l if l == [] else [item for sublist in l for item in sublist]


def isLeaf(node):
    return not node.children


def preorder(node, isLeaf=isLeaf):
    """Graph pre-order traversal. """
    if isLeaf(node):
        return [node]
    return [node] + concat([preorder(n, isLeaf) for n in node.children])


def showDAG(node):
    if not node.children:
        if node.value:
            return '{}:{}'.format(node.tag, node.value)
        return '{}:None'.format(node.tag)
    childDAGStrings = [showDAG(n) for n in node.children]
    return '{}({})'.format(node.tag, ','.join(childDAGStrings))


def _getRepeatedNodes(node, isLeaf=isLeaf):
    if isLeaf(node):
        return []
    grandchildren = concat([preorder(d, isLeaf) for d in node.children])
    grandchildren = sorted(grandchildren, key=lambda x: showDAG(x))
    groupedDAGStrings = [(s, list(
        g)) for (s, g) in groupby(grandchildren, lambda x: showDAG(x))]
    repeatedDAGStrings = [(s, ns) for (s, ns) in groupedDAGStrings
                          if len(ns) > 1]
    return repeatedDAGStrings


def _showDAGWithoutRepeats(n, repeatedDAGStrings, isLeaf=isLeaf):
    if showDAG(n) in [s for s, _ in repeatedDAGStrings]:
        return ''
    if isLeaf(n):
        return showDAG(n)
    childDAGStrings = filter(lambda x: x != '', [_showDAGWithoutRepeats(
        d, repeatedDAGStrings, isLeaf) for d in n.children])
    if childDAGStrings:
        return '{}({})'.format(n.tag, ','.join(childDAGStrings))
    else:
        return n.tag.__str__()


def showCompressedDAG(node, isLeaf=isLeaf):
    if isLeaf(node):
        return showDAG(node)
    repeatedDAGStrings = _getRepeatedNodes(node, isLeaf)
    depStrings = filter(lambda x: x != '',
                        [_showDAGWithoutRepeats(d, repeatedDAGStrings, isLeaf)
                         for d in node.children])
    # now remove repeated nodes from other repeated nodes
    trimmedRepeats = []
    for s, ns in repeatedDAGStrings:
        trimmed = _showDAGWithoutRepeats(
            ns[0], [(x, ys) for (x, ys) in repeatedDAGStrings if x != s],
            isLeaf)
        trimmedRepeats.append(trimmed)

    if repeatedDAGStrings:
        return '{}({})-{}'.format(node.tag, ','.join(depStrings),
                                  '-'.join(sorted(trimmedRepeats)))
    return '{}({})'.format(node.tag, ','.join(depStrings))
