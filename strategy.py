from terms import *
from rules import *


class Strategy:

    def state_visit(self, state):
        raise NotImplementedError()

    def get_cost(self, state, action):
        raise NotImplementedError()


class RewriteStrategy(Strategy):

    def __init__(self, rules):
        self.rules = rules

    def state_visit(self, state):
        if state.par_state is None:
            # do some initalization
            state.rule_costs = [] # these will override default costs
            for i in range(len(self.rules)):
                state.rule_costs.append(self.rules[i].get_cost())
        else:
            state.rule_costs = state.par_state.rule_costs[:]
            # prevent consecutive applications of most recently used rule
            state.rule_costs[state.rule_num] *= 2

    def get_cost(self, state, new_term, rule_num):
        cost = 0
        if rule_num:
            cost += state.rule_costs[rule_num]
        # cost += 5 * state_depth(new_term)
        cost += 5 * new_term.length()
        # cost += 3 * int(sq_branching_factor(new_term))

        return cost


def state_depth(term, depth = 0):
    if type(term) == Const:
        return 0
    if type(term) == Var:
        return depth if term.vclass == "SV" else 0
    return sum([state_depth(subterm, depth + 1) for
                subterm in term.terms])


def _sq_sum_of_lens(term):
    if type(term) == Const or type(term) == Var:
        return 0
    return len(term.terms) ** 2 + sum([_sq_sum_of_lens(subterm) for
                                       subterm in term.terms])


def sq_branching_factor(term):
    return _sq_sum_of_lens(term) / term.length()