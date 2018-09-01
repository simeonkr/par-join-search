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


def _gcjut_rec(loop, t, conj_existing_states=False):

    # Base case
    if type(t) == Var or type(t) == Const:
        if type(t) == Var and t.vclass == "IV":
            i = loop.get_num_states() + 1
            sRi = Var("RSV", "s", i, t.type)
            si = Var("SV", "s", i, t.type)
            l = loop.__deepcopy__()
            l.state_init.append(t)
            l.state_terms.append(si)
            vprint(P_JOIN_GEN, "Join: got join:", Join(l, sRi))
            # TODO still a manual turn off/on.
            return [Join(loop, t), Join(l, sRi)]#, Join(l2, sRi)]
        return [Join(loop, t)]

    out = []

    # Recursively call function on subterms
    joins = [_gcjut_rec(loop, st) for st in t.terms]

    for j_comb in product(*joins):

        # For this particular combination of joins, obtain a merged join
        merged_join = merge(loop, t.op, j_comb)
        vprint(P_JOIN_GEN, "Join: merged these joins:")
        for join in j_comb:
            vprint(P_JOIN_GEN, "Join:", join)
        out.append(merged_join) # Case when merged join is not a new auxillary
        vprint(P_JOIN_GEN, "Join: candidate join (merged) =\n", merged_join)
        if not merged_join.term.state_free("SV"):
            continue

        # Find all constants and obtain a mapping to their locations
        const_indv = _get_const_indv(merged_join.term)
        if not const_indv:
            # TODO why return?
            continue
            #return out

        for const in const_indv.keys():
            vprint(P_JOIN_GEN, "Join: const %s appears in locations %s within %s)" %
                   (str(const), str(const_indv[const]), str(merged_join.term)))
            for ind_set in powerset(const_indv[const]):
                if not ind_set:
                    continue
                rem_set = const_indv[const][:]
                auxjn = Join(merged_join.loop, merged_join.term)
                k = auxjn.loop.get_num_states()

                # Conjecture that this particular choice of indices corresponds
                # to locations of an auxillary state variable
                for ind in ind_set:
                    auxjn.term.set_term_at(ind, Var("RSV", "s", k+1))
                    rem_set.remove(ind)
                # Unfold right variables in term to obtain definition for auxillary
                auxterm = auxjn.term.rename("RSV", "SV").apply_subst(
                    merged_join.loop.get_full_state_subst())

                # For all remaining indices, conjecture that some of them point to
                # existing state variables (if conj_existing_states is True)
                for state_assgn in product(
                        *[list(range(loop.get_num_states() + 1)) for _ in range(len(rem_set))]) \
                        if conj_existing_states else [[0] * len(rem_set)]:
                    auxjn_v = deepcopy(auxjn)
                    auxterm_v = deepcopy(auxterm)
                    for i in range(len(rem_set)):
                        if state_assgn[i] != 0:
                            auxterm_v.set_term_at(rem_set[i], Var("SV", "s", state_assgn[i]))

                    # Add the auxillary variable and set the join to be the auxillary
                    # Note: the auxillary variable could already exist among the states,
                    # in which case, r is an index to the existing state
                    r = auxjn_v.loop.add_state(const, auxterm_v, k)
                    auxjn_v.term = Var("RSV", "s", r+1)

                    out.append(auxjn_v)
                    vprint(P_JOIN_GEN, "Join: new auxillary variable:")
                    vprint(P_JOIN_GEN, "Join: %s = %s" % (str(auxjn_v.term), str(auxterm_v)))
                    vprint(P_JOIN_GEN, "Join: candidate join (with auxillaries) =\n", str(auxjn_v))
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


def _get_const_inds(t):
    # Given a term, return a list of indices (list of integers) to all constants
    if type(t) == Const:
        return [[]]
    elif type(t) == Var:
        return []
    elif type(t) == Term:
        out = []
        for i in range(len(t.terms)):
            inds = _get_const_inds(t.terms[i])
            for index in inds:
                out.append([i] + index)
        return out


def _get_const_indv(t):
    # Given a term, return a mapping of constants to indices pointing to that constant
    const_inds = _get_const_inds(t)
    if not const_inds:
        return {}
    const_indv = {}
    for ind in const_inds:
        const = t.get_term_at(ind)
        if const.type != t.get_ret_type():
            continue  # incompatible op type
        if const not in const_indv:
            const_indv[const] = []
        const_indv[const].append(ind)
    return const_indv
