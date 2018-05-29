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
            #state.rule_costs = [2*x for x in state.rule_costs]
            state.rule_costs[state.rule_num] *= 2 # = pow(2, state.rule_costs[state.rule_num])


    def get_cost(self, state, new_term, rule_num):
        cost = 0
        if rule_num:
            cost += state.rule_costs[rule_num]
        cost += 5 * state_depth(new_term)
        cost += 5 * new_term.length()
        # cost += 3 * int(sq_branching_factor(new_term))

        return cost

class NewStrategy(Strategy):

    def __init__(self, rules):
        self.rules = rules

    def state_visit(self, state):
        if state.par_state is None:
            # do some initalization
            state.rule_costs = [rule.get_cost() for rule in self.rules]
        else:
            state.rule_costs = state.par_state.rule_costs[:]
            # prevent consecutive applications of most recently used rule
            #state.rule_costs = [2*x for x in state.rule_costs]
            state.rule_costs[state.rule_num] *= 2 # = pow(2, state.rule_costs[state.rule_num])

    def get_cost(self, state, new_term, rule_num):

        # TODO:
        # Make rule specific assumptions, i.e.:
        #   Ex 1: don't use max(0,0)  (pretty much always goes nowhere)
        #   Things like max(s1, 0) might be more useful, and yet have the same cost!
        #
        #   Ex 2: Punish harshely if applying a rule very deep. In particular go for a steep
        #           drop-off when a term has more than (say) 5 things in it.
        #
        #   Ex 3: NOTE what else?

        cost = 0
        if rule_num:
            cost += state.rule_costs[rule_num]
        cost += 5 * (max_state_depth(new_term) - max_state_depth(state.get_term()))*max_state_depth(new_term)
        cost += 5 * (max(0, new_term.length() - state.get_term().length()))

        #TODO punish max(0,0), max(a0, a0), etc...
        #if get_diff(term) is not None:
        #    pass

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

def max_state_depth(term, depth=0):
    if type(term) == Const:
        return 0
    if type(term) == Var:
        return depth if term.vclass == "SV" else 0
    return max([state_depth(subterm, depth + 1) for
                subterm in term.terms])

# What I'm thinking off seems just to be max_state_depth, w/o SV I think?
def max_length_subterm(term):
    if type(term) == Const:
        return 1
    if type(term) == Var:
        return 1
    return max(len(term.terms), max([max_length_subterm(t) for t in term.terms]))

def get_diff(term, new_term):
    if type(term) == Const or type(term) == Const:
        return None
    if type(new_term) == Var or type(new_term) == Var:
        return None

    newsubterms = subterm.terms[:]
    changed = []
    for x in term.terms:
        if x in newsubterms:
            newsubterms.remove(x)
        else:
            changed.append(x)

    if len(newsubterms) == 0:
        return None
    elif len(newsubterms) == 1 and len(changed) == 0:
        return (None, newsubterms[0])
    else: # len(newsubterms) == 1 and len(changed) == 1: TODO o/w?
        assert len(newsubterms) == 1 and len(changed) == 1
