from join import *
from loop import *
import unittest


s1 = Var("SV", "s", 1, int)
s2 = Var("SV", "s", 2, int)
s3 = Var("SV", "s", 3, int)
s4 = Var("SV", "s", 4, int)
s5 = Var("SV", "s", 5, int)
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


class TestMerge(unittest.TestCase):

    def test_merge(self):
        lp0 = Loop([],[])
        lp1 = Loop([True],
                   [Term("&", [a0, s1])])
        lp2 = Loop([0, 1],
                   [Term("+", [Const(0), s1]),
                    Term("+", [s2, Term("+", [Const(0), s1])])])
        lp3 = Loop([0, 0],
                   [Term("max", [Const(0), s1]),
                    Term("max", [s2, s1])])
        self.assertEqual(merge(lp0, "+", [Join(lp1, s1), Join(lp2, s2), Join(lp3, Const(0))]).loop.state_terms,
                         [Term("&", [a0, s1]),
                          Term("+", [Const(0), s2]),
                          Term("+", [s3, Term("+", [Const(0), s2])]),
                          Term("max", [Const(0), s4]),
                          Term("max", [s5, s4])])
        
if __name__ == '__main__':
    unittest.main()
