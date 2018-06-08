from rules import *
from defns import *
import unittest


s1 = Var("SV", "s", 1, int)
s2 = Var("SV", "s", 2, int)
a0 = Var("IV", "a", 0, int)
a1 = Var("IV", "a", 1, int)
a2 = Var("IV", "a", 2, int)

t1 = Term("max", [s1, Const(0)])
t2 = Term("max", [Term("+", [s1, Const(0)]), Const(0)])
t3 = Term("+", [Term("max", [s1, s1]), Const(0)])
t4 = Term("+", [s1, Const(0)])
t5 = Term("+", [Const(0), Term("max", [s1, s2])])
t6 = Term("max", [Term("+", [Const(0), s1]), Term("+", [Const(0), s2])])
t7 = Term("+", [Const(0), Term("IC", [Term(">", [s1, Const(0)]), Const(0), Const(1)])])
t8 = Term("IC", [Term(">", [s1, Const(0)]), Term("+", [Const(0), Const(0)]), Term("+", [Const(0), Const(1)])])
t9 = Term("max", [Term("+", [s1, Const(0), Const(1)]), Term("+", [Const(0), Const(1)])])
t10 = Term("+", [Const(0), Term("max", [Term("+", [s1, Const(1)]), Const(1)])])


class TestIdentIntroRule(unittest.TestCase):

    def test_zero_introduce_rule(self):
        self.assertIn(t2, zeroIntroduceRule.apply(t1))


class TestIdentElimRule(unittest.TestCase):

    def test_zero_elim_rule(self):
        self.assertIn(t1, zeroElimRule.apply(t2))


class TestInvElimRule(unittest.TestCase):
    pass


class TestDupIntroRule(unittest.TestCase):

    def test_max_introduce_rule(self):
        self.assertIn(t3, maxIntroduceRule.apply(t4))


class TestDupElimRule(unittest.TestCase):

    def test_max_elim_rule(self):
        self.assertIn(t4, maxElimRule.apply(t3))


class TestDistInRule(unittest.TestCase):

    def test_max_dist_rule(self):
        self.assertIn(t6, maxDistRule.apply(t5))
        self.assertIn(t9, maxDistRule.apply(t10))

    def test_cond_dist_rule(self):
        self.assertIn(t8, iCondDistRule.apply(t7))


class TestDistOutRule(unittest.TestCase):

    def test_max_dist_rev_rule(self):
        self.assertIn(t5, maxDistRevRule.apply(t6))
        self.assertIn(t10, maxDistRevRule.apply(t9))

    def test_cond_dist_rev_rule(self):
        self.assertIn(t7, iCondDistRevRule.apply(t8))


if __name__ == '__main__':
    unittest.main()
