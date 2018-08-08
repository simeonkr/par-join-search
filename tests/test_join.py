from join import *
from loop import *
from main import make_jsp
from parser import parse
import unittest


# TODO: use parser to define terms below

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

    # TODO: make these tests more thorough

    def test_mts_join(self):
        mts = make_jsp('../examples/mts.txt')
        goal_term = parse('max((s1+(a0+0)),max(0,(a0+0)))')
        self.assertIn(parse('max(sr1,(s1+sr2))'),
                      [join.term for join in get_candidate_join_unfold_terms(mts.lp, goal_term)])

    def test_mss_join(self):
        mss = make_jsp('../examples/mss.txt')
        goal_term = parse('max(s2,(s1+max(0,(a0+0))),max(0,max(a0,(a0+0))))')
        self.assertIn(parse('max(s2,sr2,(s1+sr4))'),
                      [join.term for join in get_candidate_join_unfold_terms(mss.lp, goal_term)])

    def test_pos_mts_join(self):
        pos_mts = make_jsp('../examples/pos_mts.txt')
        goal_term = parse('IC(((s2+(a0+0))>IC(((a0+0)>0),(a0+0),0)),s3,(s1+IC(((a0+0)>0),0,(0+1))))')
        self.assertIn(parse('IC(((s2+sr4)>sr2),s3,(s1+sr3))'),
                      [join.term for join in get_candidate_join_unfold_terms(pos_mts.lp, goal_term)])

        
if __name__ == '__main__':
    unittest.main()
