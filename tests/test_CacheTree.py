import unittest
from FMI.SML.inf.base.cache_tree import CacheTree

class TestCacheTree(unittest.TestCase):

    def setUp(self):
        self.cache = CacheTree()
        self.cache.step('a', 'b')
        self.cache.step('c', 'd')
        self.cache.step('e', 'f')
        self.cache.step('g', 'h')
        self.cache.reset()
        self.cache.step('c', 'd')
        self.cache.reset()
        self.cache.step('e', 'f')
        self.cache.reset()
        self.cache.step('g', 'h')

    def test_cache_in_a(self):
        actual = self.cache.in_cache('a')
        expected = ['b']
        self.assertListEqual(actual,expected)

    def test_cache_in_c(self):
        actual = self.cache.in_cache('c')
        expected = ['d']
        self.assertListEqual(actual,expected)

    def test_cache_in_e(self):
        actual = self.cache.in_cache('e')
        expected = ['f']
        self.assertListEqual(actual,expected)

    def test_cache_in_g(self):
        actual = self.cache.in_cache('g')
        expected = ['h']
        self.assertListEqual(actual,expected)

    def test_cache_in_ac(self):
        actual = self.cache.in_cache('ac')
        expected = ['b','d']
        self.assertListEqual(actual,expected)

    def test_cache_in_ace(self):
        actual = self.cache.in_cache('ace')
        expected = ['b', 'd', 'f']
        self.assertListEqual(actual,expected)


    def test_cache_in_aceg(self):
        actual = self.cache.in_cache('aceg')
        expected = ['b', 'd', 'f','h']
        self.assertListEqual(actual,expected)

    def test_cache_in_q(self):
        actual = self.cache.in_cache('q')
        expected = None
        self.assertEqual(actual,expected)

    def test_cache_in_z(self):
        actual = self.cache.in_cache('z')
        expected = None
        self.assertEqual(actual,expected)
