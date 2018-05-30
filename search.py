from time import time

from terms import Const, Var, Term
from loop import Loop
from join import get_candidate_join_unfold_terms
from rules import *
from strategy import RewriteStrategy, NewStrategy
from solver import EqSolver
from defns import *
from statistics import SearchStats
from util import PriorityQueue
from util import loopthru, vprint
from config import I_REWRITE, I_UNFLATTEN, \
    P_MAIN, P_STATES, P_SUCCESSORS, P_UNFLATTENED, P_SUCCESS_PATH


class JoinSearchProblem:

    def __init__(self, lp, rules, invars, initial_subst = None, pars = None):
        self.lp = lp
        self.init_term = lp.get_state_term(lp.get_num_states() - 1)
        if initial_subst:
            self.init_term = self.init_term.apply_subst(initial_subst)
        self.unfolded_term = self.init_term.apply_subst_multi(lp.get_full_state_subst(), 1)
        self.rules = rules
        self.strategy = NewStrategy(self.rules)
        self.solver = EqSolver([str(invar) for invar in invars])
        self.state_count = 0
        self.hits = 0
        self.rule_choice_record = []
        self.stats = SearchStats()
        self.benchmark_sequence = []

    def get_initial_state(self):
        return State(flatten(self.init_term), 0,
                     self.strategy.get_heuristic(None, flatten(self.init_term), None))

    def get_successors(self, state):
        out = []
        new_terms = []
        for i in range(len(self.rules)):
            new = [flatten(rew) for rew in self.rules[i].apply(state.term)] # TODO: no need to flatten if rules preserve flatness
            new_terms = new if type(new) == list else [new]
            for new_term in new_terms:
                new_cost = state.cost + self.strategy.get_cost(state, new_term, i)
                heuristic = self.strategy.get_heuristic(state, new_term, i)
                new_state = State(new_term, new_cost, heuristic, state, i)
                vprint(P_SUCCESSORS, 'Rule: ', state.term, '->', new_term,
                       '(%s)' % self.rules[i], new_cost)
                out.append(new_state)
        return out

    INITIAL = 0
    COMPLETE = 0 # for now only simple auxillary searches

    # check if state is a goal state
    def outcome(self, state):
        for _, uterm in loopthru(all_unflatten(state.term), I_UNFLATTEN,
                                 'select an unflattened variant of %s' % state.term):
            vprint(P_UNFLATTENED, "Unflattened %s to %s" % (state.term, uterm))
            for join in get_candidate_join_unfold_terms(self.lp, uterm):
                # temporarily using unflatten here
                solver_start = time()
                equiv = self.solver.equivalent(self.unfolded_term, unflatten(join.induced_term(2)))
                solver_end = time()
                self.stats.log_join(state, join, solver_end - solver_start, equiv)
                if equiv:
                    self.hits += 1
                    if self.post_verification(join, 4): # used to be self.post_verification(join, 2)
                        vprint(P_SUCCESS_PATH, "\nSuccessful sequence:")
                        rewrite_seq = '\n'.join(['%s -%d->' % (term, choice+1) for choice, term
                                       in zip(self.rule_choice_record, reversed(state.get_predecessors()))])
                        vprint(P_SUCCESS_PATH, rewrite_seq)
                        vprint(P_SUCCESS_PATH, state)
                        return join
                    else:
                        vprint(P_MAIN, "### Join failed to pass post-verification tests ###")
                        vprint(P_MAIN, join)
        return None

    def post_verification(self, join, unfolds):
        for i in range(1, unfolds+1):
            ith_unfold = self.init_term.apply_subst_multi(self.lp.get_full_state_subst(), i)
            if not self.solver.equivalent(ith_unfold, unflatten(join.induced_term(i+1))):
                return False
        return True

    def search(self):
        open_set = PriorityQueue()
        init_state = self.get_initial_state()
        open_set.push(init_state, init_state.cost + init_state.heuristic)
        seen = {init_state : init_state.cost}
        while not open_set.is_empty():
            state = open_set.pop()
            self.state_count += 1
            self.strategy.state_visit(state)
            self.stats.log_state(state)
            vprint(P_STATES, "State", "[%d, %d]:" %
                   (self.state_count, self.hits), state)
            if self.benchmark_sequence: # benchmark mode
                if str(state.term) in self.benchmark_sequence:
                    vprint(True, "### Milestone:", state, "###")
                    self.benchmark_sequence.remove(str(state.term))
                    self.hits += 1 # variable has different meaning in this case
                if not self.benchmark_sequence:
                    return None
            else:
                outcome = self.outcome(state)
                if outcome:
                    return outcome

            for i, succ_state in loopthru(self.get_successors(state), I_REWRITE,
                                          'select a rewrite of %s:' % state):
                succ_metric = succ_state.cost + succ_state.heuristic
                if not succ_state in seen or succ_metric < seen[succ_state]:
                    seen[succ_state] = succ_metric
                    open_set.push(succ_state, succ_metric)
                self.rule_choice_record.append(i)
        return None

    '''
    def verify(self, rule_sequence):
        state = self.get_initial_state()
        for (rule, i) in rule_sequence:
            new_term = [flatten(rew) for rew in rule.apply(state.term)][i]
            new_cost = state.get_cost()
            new_cost += rule.get_cost()
            new_cost += self.term_heuristic(new_term)
            state = State(new_term, new_cost, state.rule_cost + rule.get_cost(), 0, state)
            vprint(P_SUCCESSORS, 'Rule: ', state.term, '->', new_term, '(%s)' % rule, new_cost)
            vprint(P_STATES, "State:" , state)
            outcome = self.outcome(state)
        return outcome
    '''


class State:

    def __init__(self, term, cost, heuristic, par_state=None, rule_num=None):
        self.term = term
        self.cost = cost
        self.heuristic = heuristic
        self.par_state = par_state
        self.rule_num = rule_num

    def __eq__(self, other):
        if type(other) != State:
            return False
        return self.term == other.term

    def __lt__(self, other):
        return self.cost + self.heuristic < other.cost + other.heuristic

    def __hash__(self):
        return hash(self.term)

    def __str__(self):
        return "%s %s (%s+%s)" % (self.term, self.cost + self.heuristic,
                                    self.cost, self.heuristic)

    def get_predecessors(self):
        if self.par_state is None:
            return []
        return [self.par_state] + self.par_state.get_predecessors()

    def get_rule_history(self):
        if self.par_state is None:
            return []
        return [self.rule_num] + self.par_state.get_rule_history()

