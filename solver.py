from z3 import *

from util import vprint
from config import P_SOLVER


class EqSolver:

    def __init__(self, invars = []):
        self.s = Solver()

        # TODO: specify types of variables properly
        self.eval_dict = {'s1' : Int('s1'),
                          's2' : Int('s2'),
                          's3' : Int('s3'),
                          's4' : Int('s5'),
                          's5' : Int('s5'),
                           #'a0' : Bool('a0'),
                           #'a1' : Bool('a1'),
                           #'a2' : Bool('a2'),
                           #'a3' : Bool('a3'),
                           #'a4' : Bool('a4')}
                           #"""
                           'a0' : Int('a0'),
                           'a1' : Int('a1'),
                           'a2' : Int('a2'),
                           'a3' : Int('a3'),
                           'a4' : Int('a4')}
                           #"""
        self.eval_dict['max'] = lambda x,y : If(x > y, x, y)
        self.eval_dict['BC'] = lambda x,y,z : If(x, y, z)
        self.eval_dict['IC'] = lambda x,y,z : If(x, y, z)
        self.eval_dict['And'] = lambda x,y : And(x, y)
        self.eval_dict['Or'] = lambda x,y : Or(x,y)

        self.s.add([eval(str(invar), {}, self.eval_dict) for invar in invars])

    def equivalent(self, t1, t2):
        vprint(P_SOLVER, 'Solver: %s ?= %s' % (t1, t2))
        self.s.push()
        self.s.add(eval(t1.get_str(True), {}, self.eval_dict) !=
                   eval(t2.get_str(True), {}, self.eval_dict))
        if self.s.check().r == Z3_L_FALSE:
            self.s.pop()
            return True
        self.s.pop()
        return False
