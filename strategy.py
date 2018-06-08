from terms import *
from rules import *
from features import *


class Strategy:

    def state_visit(self, state):
        raise NotImplementedError()

    def get_cost(self, state, action):
        raise NotImplementedError()

    def get_heuristic(self, state):
        raise NotImplementedError()


class RewriteStrategy(Strategy):

    def __init__(self, rules, stats):
        self.rules = rules
        self.stats = stats

    def state_visit(self, state):
        pass

    def get_costs(self, state, new_term, rule_num):

        # TODO:
        # Make rule specific assumptions, i.e.:
        #   Ex 1: don't use max(0,0)  (pretty much always goes nowhere)
        #   Things like max(s1, 0) might be more useful, and yet have the same cost!
        #
        #   Ex 2: Punish harshly if applying a rule very deep. In particular go for a steep
        #           drop-off when a term has more than (say) 5 things in it.
        #
        #   Ex 3: NOTE what else?

        costs = []
        costs.append(5 * state_depth_diff_feature(state, new_term, rule_num))
        costs.append(5 * state_count_diff_feature(state, new_term, rule_num))
        costs.append(5 * term_length_diff_feature(state, new_term, rule_num))
        costs.append(5 * sq_branching_factor_diff_feature(state, new_term, rule_num))
        costs.append(50 * num_duplicates_feature(state, new_term, rule_num))
        costs.append(30 * rule_history_feature(state, new_term, rule_num))
        costs.append(3 * depth_diff_feature(state, new_term, rule_num))
        costs.append(1000 * const_only_terms_diff_feature(state, new_term, rule_num))
        # TODO: punish invariants; e.g.,
        if rule_num in [10, 12, 14, 16, 18] and rule_num in state.get_rule_history():
           costs.append(100)

        # TODO punish max(0,0), max(a0, a0), etc...

        return costs

    def get_cost(self, state, new_term, rule_num):
        return sum(self.get_costs(state, new_term, rule_num))

    def get_heuristic(self, state):
        '''
        terms = 0
        h = 0
        tcount = 0
        for _, uterm in loopthru(all_unflatten(state.term), I_UNFLATTEN,
                                 'select an unflattened variant of %s' % state.term):

            count = 0
            l = len(get_candidate_join_unfold_terms(self.lp, uterm))
            tcount += 0 if l == 0 else 1
            for join in get_candidate_join_unfold_terms(self.lp, uterm):
                if self.solver.equivalent(self.unfolded_term, unflatten(join.induced_term(2))): # temporarily using unflatten here
                    count += 1
                    if self.post_verification(join, 4): # used to be self.post_verification(join, 2)
                        return 0
            h += 0 if l==0 else (l-count)/l

        return 100 if tcount == 0  else 2*h/tcount
        '''
        return 0