from collections import Counter
from util import concat


class Node(object):
    def __init__(self, tag, children):
        self.children = children
        self.tag = tag

    def showDAG(self):
        if not self.children:
            return str(self.tag)
        childDAGStrings = [n.showDAG() for n in self.children]
        return '{}({})'.format(self.tag, ','.join(childDAGStrings))

    def isLeaf(self):
        return not self.children


def preorder(node):
    """Graph pre-order traversal"""
    if node.isLeaf():
        return [node]
    return [node] + concat([preorder(n) for n in node.children])


def getRepeatedNodes(node):
    if node.isLeaf():
        return []
    grandchildren = concat([preorder(d) for d in node.children])
    nodeShowMap = [(n, n.showDAG()) for n in grandchildren]
    subtreeCounts = Counter(nodeShowMap)
    return [(n, dagStr) for (n, dagStr), count in subtreeCounts.items()
            if count > 1 and not dagStr.startswith('Src')]


def showDAGWithoutRepeats(n, repeatedNodes):
    if n.showDAG() in [s for _, s in repeatedNodes]:
        return ''
    if n.isLeaf():
        return n.showDAG()
    childDAGStrings = filter(
        lambda x: x != '',
        [showDAGWithoutRepeats(d, repeatedNodes) for d in n.children])
    if childDAGStrings:
        return '{}({})'.format(n.tag, ','.join(childDAGStrings))
    else:
        return n.tag
