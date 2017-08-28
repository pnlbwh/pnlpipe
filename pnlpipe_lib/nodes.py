from . import basenode

@basenode.node(params=['filepath'])
class InputFile(basenode.Node):
    def output(self):
        return self.params['filepath']
