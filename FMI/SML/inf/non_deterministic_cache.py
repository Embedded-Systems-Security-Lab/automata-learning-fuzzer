from FMI.SML.inf.base.cache_tree import Node, CacheTree
from FMI.SML.inf.base.sul import CacheSUL, SUL
from FMI.utils.decorators import FMILogger
from FMI.utils.exception import FMINonDeterministicError, FMITableError, FMIRepeatedNonDeterministicError


""" This code is an experiments I tried trying to solve the non-deterministic that could arise, 
didn't work exactly how I wanted it."""

@FMILogger
class NonDetNode(Node):
    def __init__(self,value=None):
        super(NonDetNode, self).__init__(value)
        self.nonDetCache = defaultdict(int)
        if value is not None:
            self.nonDetCache[value] = 1
        self.non_det_total = 0

@FMILogger
class NonDetCacheTree(CacheTree):

    def __init__(self, max_cache_buffer_size, max_pre_filled=20):
        super(NonDetCacheTree, self).__init__()
        self.root_node = NonDetNode()
        self.curr_node = self.root_node
        self.total_diff_outputs = 0
        self.max_cache_buffer_size = max_cache_buffer_size
        self.max_pre_filled = max_pre_filled

    def step(self, inp, out):

        self.inputs.append(inp)
        self.outputs.append(out)
        if inp is None:
            self.root_node.value = out
            return

        if inp not in self.curr_node.children:
            node = NonDetNode(out)
            self.curr_node.children[inp] = node
        else:
            node = self.curr_node.children[inp]
            node.non_det_total += 1
            if node.value != out:
                self.total_diff_outputs += 1
                if out in node.nonDetCache:
                    node.nonDetCache[out] += 1
                    if node.non_det_total < self.max_pre_filled:
                        print("Pre filling the cache size")
                        raise FMINonDeterministicError()
                    elif node.non_det_total >= self.max_pre_filled and node.nonDetCache[out] > node.nonDetCache[node.value]:
                        node.value = out
                        self._logger.info("Changed the node value to the most frequent value - {}".format(out))
                        raise FMITableError()
                else:
                    if len(node.nonDetCache) >= self.max_cache_buffer_size:
                        expected_seq = list(self.outputs[:-1])
                        expected_seq.append(node.value)
                        msg = f'Non-determinism detected.\n' \
                              f'Error inserting: {self.inputs}\n' \
                              f'Conflict detected: {node.value} vs {out}\n' \
                              f'Expected Output: {expected_seq}\n' \
                              f'Received output: {self.outputs}'
                        print(msg)
                        raise FMIRepeatedNonDeterministicError()
                    else:
                        node.nonDetCache[out] = 1
                        self._logger.info("Added new value to cache - {}".format(out))
                        raise FMINonDeterministicError()
            else:
                node.nonDetCache[out] += 1

        self.curr_node = node

@FMILogger
class NonDetCacheSUL(CacheSUL):

    def __init__(self, sul, max_cache_buffer_size):
        super(NonDetCacheSUL, self).__init__(sul)
        self.cache = NonDetCacheTree(max_cache_buffer_size)
        self.non_det_step_counter = 0
        self.non_det_query_counter = 0

    def query(self, word):
        cached_query = self.cache.in_cache(word)
        self.stats.num_queries += 1
        self.stats.num_letter += len(word)
        if cached_query:
            self.stats.num_cached_queries += 1
            return cached_query

        attempts = 0
        while attempts < 20:
            try:
                non_det_update = 0
                while non_det_update < 20:
                    try:
                        non_det_update += 1
                        out = self.sul.query(word)
                        self.cache.reset()
                        # Store value in a cache tree for later use
                        for i, o in zip(word, out):
                            self.cache.step(i,o)
                        self.stats.num_submitted_queries += 1
                        self.stats.num_submitted_letter += len(word)
                        return out
                    except FMINonDeterministicError:
                        continue
                    except FMITableError:
                        raise
            except FMIRepeatedNonDeterministicError as exp:
                attempts += 1
                print(exp)
                self.non_det_query_counter += 1
                if attempts == 20:
                    self.sul.post()
                    print("I hope it does not get here!")
                    raise


    def step(self, letter):
        out = self.sul.step(letter)
        try:
            self.cache.step(letter, out)
        except FMIRepeatedNonDeterministicError:
            Print("Non-deterministic in step execution detected")
            self.non_det_step_counter += 1
            raise
        return out



