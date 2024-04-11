import unittest
from FMI.SML.inf.utils.stats import Stats


class TestStats(unittest.TestCase):

    def setUp(self):
        self.stats = Stats()
        self.stats.num_queries += 2
        self.stats.num_submitted_queries += 3
        self.stats.num_letter += 4
        self.stats.num_submitted_letter += 5
        #self.stats.num_steps += 6
        self.stats.num_cached_queries += 7

    def test_num_queries(self):
        actual = self.stats.num_queries
        expected = 2
        self.assertEqual(actual,expected)

    def test_num_submitted_queries(self):
        actual = self.stats.num_submitted_queries
        expected = 3
        self.assertEqual(actual,expected)

    def test_num_letter(self):
        actual = self.stats.num_letter
        expected = 4
        self.assertEqual(actual,expected)

    def test_num_submitted_letter(self):
        actual = self.stats.num_submitted_letter
        expected = 5
        self.assertEqual(actual,expected)

    # def test_num_steps(self):
    #     actual = self.stats.num_steps
    #     expected = 6
    #     self.assertEqual(actual,expected)

    def test_num_cached_queries(self):
        actual = self.stats.num_cached_queries
        expected = 7
        self.assertEqual(actual,expected)

