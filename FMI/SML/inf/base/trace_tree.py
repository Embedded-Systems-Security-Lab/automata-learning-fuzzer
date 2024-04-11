from collections import defaultdict

class Node:
    __slots__ = ['output', 'children', 'parent', 'frequency_counter']
    def __init__(self, output):
        self.output = output
        self.children = defaultdict(list)
        self.parent = None
        self.frequency_counter = 0

    def get_child(self, inp, out):

        return next((child for child in self.children[inp] if child.output == out), None)

    def get_prefix(self):
        prefix = ()
        curr_node = self
        while curr_node.parent is not None:
            prefix = (curr_node.output,) + prefix
            curr_node = curr_node.parent
        return prefix


class TraceTree:
    def __init__(self):
        self.root_node = Node(None)
        self.curr_node = None

    def reset(self):
        self.curr_node = self.root_node

    def add_to_tree(self, inp, out):
        if inp not in self.curr_node.children.keys() or \
                out not in {child.output for child in self.curr_node.children[inp]}:
            node = Node(out)
            self.curr_node.children[inp].append(node)
            node.parent = self.curr_node

        self.curr_node = self.curr_node.get_child(inp, out)
        self.curr_node.frequency_counter += 1

    def add_trace(self, inputs, outputs):
        self.reset()
        for i, o in zip(inputs, outputs):
            self.add_to_tree(i, o)

    def get_to_node(self, inputs, outputs):
        curr_node = self.root_node
        for i, o in zip(inputs, outputs):
            node = curr_node.get_child(i, o)
            if node is None:
                return None
            curr_node = node

        return curr_node

    def get_all_traces(self, prefix, e=None):
        if not prefix or not e:
            return []

        curr_node = self.root_node
        for i, o in zip(prefix[0], prefix[1]):
            curr_node = curr_node.get_child(i, o)
            if curr_node is None:
                return []

        queue = [(curr_node, 0)]
        reached_nodes = []
        while queue:
            node, depth = queue.pop(0)
            if depth == len(e):
                reached_nodes.append(node)
            else:
                children_with_same_input = node.children[e[depth]]
                for c in children_with_same_input:
                    queue.append((c, depth + 1))

        cell = [node.get_prefix()[-len(e):] for node in reached_nodes]
        return cell

    def get_table(self, s, e):
        result = {}
        for prefix in s:
            result[prefix] = {}

            for inp in e:
                result[prefix][inp] = self.get_all_traces(prefix, inp)

        return result

    def find_cex_in_cache(self, hypothesis):

        queue = [(self.root_node, tuple())]
        while queue:
            curr_node, path = queue.pop(0)

            if path:
                hypothesis.reset_to_initial()
                inputs, outputs = [], []
                for i, o in zip(path[0::2], path[1::2]):
                    inputs.append(i)
                    outputs.append(o)
                    out = hypothesis.step_to(i, o)
                    if out is None:
                        return inputs, outputs
            for inp in curr_node.children.keys():
                children = curr_node.children[inp]
                for child in children:
                    queue.append((child, path + (inp, child.output)))

        return None

    def get_s_e_sampling_frequency(self, prefix, suffix):
        sampling_frequency = 0
        curr_node = self.root_node
        for i, o in zip(prefix[0], prefix[1]):
            curr_node = curr_node.get_child(i, o)
            if curr_node is None:
                return 0

        queue = [(curr_node, 0)]
        while queue:
            node, depth = queue.pop(0)
            children_with_same_input = node.children[suffix[depth]]
            if depth == len(suffix) - 1:
                for c in children_with_same_input:
                    sampling_frequency += c.frequency_counter
            else:
                for c in children_with_same_input:
                    queue.append((c, depth + 1))

        return sampling_frequency

    def get_sampling_distributions(self, prefix, input_from_alphabet):
        sampling_distribution = {}
        curr_node = self.root_node
        for i, o in zip(prefix[0], prefix[1]):
            curr_node = curr_node.get_child(i, o)

        children = curr_node.children[input_from_alphabet]
        sampling_sum = sum(c.frequency_counter for c in children)
        for c in children:
            sampling_distribution[c.output] = c.frequency_counter / sampling_sum

        return sampling_distribution
