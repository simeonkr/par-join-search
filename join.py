from copy import deepcopy
from itertools import product, compress

from terms import Const, Var, Term, term_types
from loop import Loop
from util import powerset, all_injective
from util import vprint
from config import P_JOIN_GEN


class Join:

    def __init__(self, loop, term):
        self.loop = loop.__deepcopy__()
        self.term = term.__deepcopy__()

    def __deepcopy__(self, memo=None):
        return Join(self.loop, self.term)

    def __str__(self):
        return "jn({} {})".format(str(self.loop), str(self.term))

    def __repr__(self):
        return self.__str__()

    def get_term(self):
        return self.term

    def induced_term(self, k):
        return self.term.apply_subst_multi(self.loop.get_full_state_subst(True), k). \
                apply_subst(self.loop.get_full_init_subst(True))


def get_candidate_join_unfold_terms(loop, t):
    vprint(P_JOIN_GEN, "Join: Starting gcjut")
    vprint(P_JOIN_GEN, "Join: loop = \n", loop)
    vprint(P_JOIN_GEN, "Join: term = %s" % str(t))
    return [join for join in _gcjut_rec(loop, t) if join.term.state_free("IV")]


def _gcjut_rec(loop, t):
    if type(t) == Var or type(t) == Const:
        return [Join(loop, t)]
    out = []
    joins = [_gcjut_rec(loop, st) for st in t.terms]
    for j_comb in product(*joins):
        merged_join = merge(loop, t.op, j_comb)
        vprint(P_JOIN_GEN, "Join: merged these joins:")
        for join in j_comb:
            vprint(P_JOIN_GEN, "Join:", join)
        out.append(merged_join)
        vprint(P_JOIN_GEN, "Join: candidate join (merged) =\n", merged_join)
        if not merged_join.term.state_free("SV"):
            continue

        const_inds = get_const_inds(merged_join.term)
        if const_inds == []:
            return out
        const_indv = {}
        for ind in const_inds:
            const = merged_join.term.get_term_at(ind)
            if const.type != merged_join.term.get_ret_type():
                continue # incompatible op type
            if const not in const_indv:
                const_indv[const] = []
            const_indv[const].append(ind)

        for const in const_indv.keys():
            vprint(P_JOIN_GEN, "Join: const %s appears in locations %s within %s)" %
                   (str(const), str(const_indv[const]), str(merged_join.term)))
            for ind_set in powerset(const_indv[const]):
                if not ind_set:
                    continue
                auxjn = Join(merged_join.loop, merged_join.term)
                k = auxjn.loop.get_num_states()
                for ind in ind_set:
                    auxjn.term.set_term_at(ind, Var("RSV", "s", k+1))
                auxterm = auxjn.term.rename("RSV", "SV").apply_subst(
                    merged_join.loop.get_full_state_subst())
                r = auxjn.loop.add_state(const, auxterm, k)
                auxjn.term = Var("RSV", "s", r+1)
                out.append(auxjn)
                vprint(P_JOIN_GEN, "Join: new auxillary variable:")
                vprint(P_JOIN_GEN, "Join: %s = %s" % (str(auxjn.term), str(auxterm)))
                vprint(P_JOIN_GEN, "Join: candidate join (with auxillaries) =\n", str(auxjn))
    return out


# TODO: thorougly test this
def merge(loop, op, joins):
    new_loop = loop.__deepcopy__()
    new_terms = []
    for i in range(len(joins)):
        new_term = joins[i].term.__deepcopy__()
        r = 0
        reindex = []
        for j in range(joins[i].loop.get_num_states()):
            r = new_loop.add_state(joins[i].loop.state_init[j],
                                   joins[i].loop.state_terms[j], j)
            reindex.append(r)
        for j in reversed(range(len(reindex))):
            r = reindex[j]
            new_term = new_term.reindex(Var("SV", "s", j+1), r+1).\
                reindex(Var("RSV", "s", j+1), r+1)
        new_terms.append(new_term)
    return Join(new_loop, Term(op, new_terms))


def get_const_inds(t):
    if type(t) == Const:
        return [[]]
    elif type(t) == Var:
        return []
    elif type(t) == Term:
        out = []
        for i in range(len(t.terms)):
            inds = get_const_inds(t.terms[i])
            for index in inds:
                out.append([i] + index)
        return out
