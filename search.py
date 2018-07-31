from time import time
from queue import PriorityQueue

from terms import Const, Var, Term
from loop import Loop
from join import get_candidate_join_unfold_terms
from rules import *
from strategy import RewriteStrategy
from solver import EqSolver
from statistics import SearchStats
import features
from util import loopthru, vprint
from rightTerm import *
from config import I_REWRITE, I_UNFLATTEN, \
    P_MAIN, P_STATES, P_SUCCESSORS, P_UNFLATTENED, \
    P_COSTS, P_STATE_PATH, P_SUCCESS_PATH, \
    R_CHECK


class JoinSearchProblem:

    def __init__(self, lp, rules, invars, initial_subst = None, pars = None):
        self.lp = lp
        self.init_term = lp.get_state_term(lp.get_num_states() - 1)
        if initial_subst:
            self.init_term = self.init_term.apply_subst(initial_subst)
        self.unfolded_term = self.init_term.apply_subst_multi(lp.get_full_state_subst(), 1)
        self.init_raw_term = self.init_term.__deepcopy__()
        for i in range(lp.get_num_states()):
            self.init_raw_term = self.init_raw_term.apply_subst(self.lp.get_state_init_subst(i))
        self.rules = rules
        self.stats = SearchStats()
        self.strategy = RewriteStrategy(self.rules, self.stats, self.init_raw_term)
        self.solver = EqSolver([str(invar) for invar in invars])
        self.state_count = 0
        self.hits = 0
        self.rule_choice_record = []
        self.benchmark_sequence = []
        self.notDeep = set()

    def get_initial_state(self):
        return State(flatten(self.init_term), 0, None)

    def get_successors(self, state):
        out = []
        new_terms = []
        for i in range(len(self.rules)):
            new = [flatten(rew) for rew in self.rules[i].apply(state.term)] # TODO: no need to flatten if rules preserve flatness
            new_terms = new if type(new) == list else [new]
            for new_term in new_terms:
                new_cost, breakdown = self.strategy.get_cost(state, new_term, i)
                new_state = State(new_term, new_cost, state, i)
                new_state.cost_breakdown = breakdown
                vprint(P_SUCCESSORS, 'Rule: ', state.term, '->', new_term,
                       '(%s)' % self.rules[i], new_cost)
                out.append(new_state)
        return out

    INITIAL = 0
    COMPLETE = 0 # for now only simple auxillary searches

    # check if state is a goal state
    def outcome(self, state):
        for _, uterm in loopthru(list(set(all_unflatten(state.term))), I_UNFLATTEN,
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

    def rewrite_check(self, state):
        if not self.solver.equivalent(unflatten(state.term), self.init_term):
            print("%%%Warning: Current state has term that is not equivalent to original!%%%")
            print(state.term, [st.term for st in state.get_predecessors()])
            print(state.rule_num)
            input('Press Enter to continue...')

    def good_guess(self, succ_term):
        if len(self.notDeep) == 0: #I_REWRITE or
            return True
        if succ_term.op == self.init_term.op:
            if self.notDeep.intersection(set(succ_term.terms)) != self.notDeep:
                if all(type(x) == Const for x in self.notDeep.difference(set(succ_term.terms))):
                    return True
                return False
        else:
            return False
        return True

    def preprocess_initial_state(self):
        self.notDeep = set()
        for subterm in flatten(self.init_term).terms:
            if type(subterm) == Var and subterm.vclass == "SV":
                self.notDeep = self.notDeep.union({subterm.__deepcopy__()})
        from rightTerm import right

        righty = flatten(right(self.lp, self.init_term))
        self.alt = self.init_term.__deepcopy__()
        self.alt.terms.extend(righty.terms)
        #self.alt.terms.
        if self.init_term.op != "IC" and self.solver.equivalent(unflatten(self.init_term), unflatten(self.alt)):
            self.notDeep = self.notDeep.union(set(righty.terms))
        else:
            self.alt = None

    def search(self):
        self.preprocess_initial_state()
        open_set = PriorityQueue()
        init_state = self.get_initial_state()
        seen = {}

        # Tries some guesses before starting the actual search.
        startTerms = generateStartTerms(self.lp, self.solver)
        for init_term in startTerms:
            state = State(init_term, 0, None)
            open_set.put((state.cost + self.strategy.get_heuristic(state), state))
            seen[init_state] = state.cost

        count = 0
        while count < 5*len(startTerms) and not open_set.empty():
            _, state = open_set.get()
            self.state_count += 1
            self.strategy.state_visit(state)
            self.stats.log_state(state)
            vprint(P_STATES, "State", "[%d, %d]:" %
                   (self.state_count, self.hits), state)
            outcome = self.outcome(state)
            if outcome:
                self.stats.log_state(state)
                return outcome

            for succ_state in [succ for succ in list(set(self.get_successors(state))) if self.good_guess(succ.term)]:
                succ_metric = succ_state.cost + self.strategy.get_heuristic(succ_state)
                if not succ_state in seen or succ_metric < seen[succ_state]:
                    seen[succ_state] = succ_metric
                    open_set.put((succ_metric, succ_state))
            count += 1

        init_state = init_state if self.alt is None else State(self.alt,0)
        open_set = PriorityQueue()
        open_set.put((init_state.cost + self.strategy.get_heuristic(init_state), init_state))
        seen = {init_state : init_state.cost}

        t1=time()

        while not open_set.empty():
            _, state = open_set.get()
            self.state_count += 1
            self.strategy.state_visit(state)
            self.stats.log_state(state)
            vprint(P_STATES, "State", "[%d, %d]:" %
                   (self.state_count, self.hits), state)
            vprint(P_COSTS, 'State costs: ', ', '.join(
                [str(cost) for cost in state.cost_breakdown]))
            for pred in [state] + state.get_predecessors():
                vprint(P_STATE_PATH, '^%-50s %s' % (pred.term, ', '.join(
                    ['%3s' % str(cost) for cost in pred.cost_breakdown])))
            if R_CHECK:
                self.rewrite_check(state)
            if self.benchmark_sequence: # benchmark mode
                if str(state.term) in self.benchmark_sequence:
                    t2=time()
                    vprint(True, "### Milestone:", self.state_count, ". ", state, " ", round(t2-t1,2), " secs ", "###")
                    if self.benchmark_sequence[-1] == str(state.term):
                        return None
                    self.benchmark_sequence.remove(str(state.term))
                    self.hits += 1 # variable has different meaning in this case
                    t1 = time()
            else:
                outcome = self.outcome(state)
                if outcome:
                    self.stats.log_state(state)
                    return outcome

            for i, succ_state in loopthru([succ for succ in list(set(self.get_successors(state))) if self.good_guess(succ.term)], I_REWRITE,
                                          'select a rewrite of %s:' % state):
                #if not self.good_guess(succ_state.term):
                #    continue
                succ_metric = succ_state.cost + self.strategy.get_heuristic(succ_state)
                if not succ_state in seen or succ_metric < seen[succ_state]:
                    seen[succ_state] = succ_metric
                    open_set.put((succ_metric, succ_state))
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

    def __init__(self, term, cost, par_state=None, rule_num=None):
        self.term = term
        self.cost = cost
        self.cost_breakdown = []
        self.par_state = par_state
        self.rule_num = rule_num

    def __eq__(self, other):
        if type(other) != State:
            return False
        return self.term == other.term

    def __lt__(self, other):
        return self.cost < other.cost

    def __hash__(self):
        return hash(self.term)

    def __str__(self):
        return "%s %s" % (self.term, self.cost)

    def get_predecessors(self):
        if self.par_state is None:
            return []
        return [self.par_state] + self.par_state.get_predecessors()

    def get_rule_history(self):
        if self.par_state is None:
            return []
        return [self.rule_num] + self.par_state.get_rule_history()
