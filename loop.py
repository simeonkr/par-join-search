from copy import deepcopy

from terms import Const, Var, Term


class Loop:

    def __init__(self, state_init, state_terms):
        self.state_init = state_init[:]
        self.state_terms = [term.__deepcopy__() for term in state_terms]

    def __str__(self):
        return "{} {}".format(str(self.state_init), str(self.state_terms))

    def __repr__(self):
        return self.__str__()

    def __deepcopy__(self, memo=None):
        return Loop(self.state_init, self.state_terms)

    def get_num_states(self):
        return len(self.state_init)

    def get_state_init(self, i):
        return self.state_init[i]

    def get_state_term(self, i):
        return self.state_terms[i]

    def get_state_subst(self, i):
        return {Var("SV", "s", i+1) : self.state_terms[i]}

    def get_state_init_subst(self, i):
        return {Var("SV", "s", i+1) : self.state_init[i]}

    def get_full_state_subst(self, rv = False):
        subst = {}
        for i in range(self.get_num_states()):
            if not rv:
                subst[Var("SV", "s", i+1)] = self.state_terms[i]
            else:
                subst[Var("RSV", "s", i+1)] = self.state_terms[i].rename("SV", "RSV")
        return subst

    def get_full_init_subst(self, rv = False):
        subst = {}
        for i in range(self.get_num_states()):
            subst[Var("RSV" if rv else "SV", "s", i+1)] = self.state_init[i]
        return subst

    def add_state(self, init_val, term, j):
        k = self.get_num_states()
        for i in range(k):
            if self.state_init[i] == init_val and \
                    self.state_terms[i] == term.offset(i-j, "SV"):
                return i
        self.state_init.append(init_val)
        self.state_terms.append(term.offset(k-j, "SV"))
        return k
        
 
'''        
def recover_states(lp, t1, t2):
    return recover_states_rec(lp, t1, t2, "")

def recover_states_rec(lp, t1, t2, y):
    pass

def recover_join(lp, u1, u2):
    lp_out = Loop(lp.state_init, lp.loopSubst)
    if u1.state_free():
        if not u2.state_free():
            return None
        else:
            return recover_states(lp_out, u1, u2)
    elif type(u1) == Var:
        if type(u2) != Var or u2 != u1:
            return None
        else:
            return (Var("LSV", u1.name, u1.index), lp_out)
    elif type(u1) == Term:
        if type(u2) != Term or u1.op != u2.op or len(u2.terms) != len(u1.terms):
            return None
        else:
            ts = []
            for r in range(len(u1.terms)):
                rj = recover_join(lp, u1.terms[r], u2.terms[r])
                if rj:
                    t, lp_out = rj
                    ts.append(t)
                else:
                    return None
            return (Term(u1.op, ts, u1.infix), lp_out)           
'''           
