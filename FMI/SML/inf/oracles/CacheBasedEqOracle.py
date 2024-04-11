from FMI.SML.inf.base import Oracle, SUL, CacheSUL

from random import choice

class CacheBasedEqOracle(Oracle):

    def __init__(self, alphabet: list, sul: SUL, num_walks=100, depth_increase=5, reset_after_cex=True):

        super(CacheBasedEqOracle, self).__(alphabet, sul)
        self.cache_tree = None
        self.num_walks = num_walks
        self.depth_increase = depth_increase
        self.reset_after_cex = reset_after_cex
        self.num_walks_done = 0


    def find_cex(self, hypothesis):
        assert isinstance(self.sul, CacheSUL)
        cache_tree = self.sul.cache

        paths_to_leaves = self.get_paths(self.cache_tree.root_node)
        max_tree_depth = len(max(paths_to_leaves, key=len))

        while self.num_walks_done < self.num_walks:
            self.num_walks_done += 1
            self.reset_hyp_and_sul(hypothesis)

            prefix = choice(paths_to_leaves)
            walk_len = (max_tree_depth + self.depth_increase) - len(prefix)
            inputs = []
            inputs.extend(prefix)

            for p in prefix:
                hypothesis.step(p)
                self.sul.step(p)
                self.num_steps += 1

            for _ in range(walk_len):
                inputs.append(choice(self.alphabet))

                out_sul = self.sul.step(inputs[-1])
                out_hyp = hypothesis.step(inputs[-1])
                self.num_steps += 1

                if out_sul != out_hyp:
                    if self.reset_after_cex:
                        self.num_walks_done = 0
                    self.sul.post()
                    return inputs
        return


    def get_paths(self, t, paths=None, current_path=None):

        if paths is None: paths = []
        if current_path is None: current_path = []

        if len(t.children) == 0: paths.append(current_path)
        else:
            for inp, child in t.children.items():
                current_path.append(inp)
                self.get_paths(child, paths, list(current_path))
        return paths


