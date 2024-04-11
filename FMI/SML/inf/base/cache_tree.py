from FMI.utils.decorators import FMILogger

class Node(object):

    def __init__(self, value=None):
        self.value = value
        self.children = {}

@FMILogger
class CacheTree(object):

    """ This class is deterministic behavior"""
    def __init__(self):
        self.root_node = Node()
        self.curr_node = self.root_node
        self.inputs = []
        self.outputs = []

    def reset(self):
        self.curr_node = self.root_node
        self.inputs = []
        self.outputs = []


    def step(self, inp, out):

        self.inputs.append(inp)
        self.outputs.append(out)
        if inp is None:
            self.root_node.value = out
            return

        if inp not in self.curr_node.children:
            node = Node(out)
            self.curr_node.children[inp] = node
        else:
            node = self.curr_node.children[inp]
            # if node.value in out or out in node.value:
            #     print("continue")
            if node.value != out:
                expected_seq = list(self.outputs[:-1])
                expected_seq.append(node.value)
                msg = f'Non-determinism detected.\n' \
                      f'Error inserting: {self.inputs}\n' \
                      f'Conflict detected: {node.value} vs {out}\n' \
                      f'Expected Output: {expected_seq}\n' \
                      f'Received output: {self.outputs}'
                print(self.inputs, self.outputs)
                self._logger.debug(msg)
                raise Exception("Non matching output found expected '{}' found '{}'".format(node.value, out))
        self.curr_node = node

    def in_cache(self, input_seq):
        curr_node = self.root_node
        output_seq = []
        for letter in input_seq:
            if letter not in curr_node.children: return
            curr_node = curr_node.children[letter]
            output_seq.append(curr_node.value)

        return output_seq



