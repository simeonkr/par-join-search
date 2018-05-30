
class SearchStats:

    def __init__(self):
        self.num_states = 0
        self.states = {}

    def log_state(self, state):
        self.num_states += 1
        state.priority = self.num_states
        state.joins = []
        state.hits = 0
        state.time = 0
        self.states[state] = state

    def log_join(self, state, join, solver_time, solver_succ):
        join.solver_time = solver_time
        join.solver_succ = solver_succ
        join.state = state
        self.states[state].joins.append(join)
        if join.solver_succ:
            self.states[state].hits += 1
        self.states[state].time += solver_time

    def print_worst_states(self, num):
        print('States which took the most time:')
        num = min(num, len(self.states.values()))
        for state in sorted(self.states.values(), key = lambda state : state.time, reverse=True)[:num]:
            print("%s -- %.2fs %d joins" % (state, state.time, len(state.joins)))

    def print_worst_joins(self, num):
        print('Joins which took the most time:')
        joins = []
        for state in self.states:
            joins.extend(state.joins)
        for join in sorted(joins, key = lambda join : join.solver_time, reverse=True)[:num]:
            print("%s -- %.3fs" % (join, join.solver_time))
            print("(from state %s)" % join.state)

    def print_summary(self):
        print()
        print("Total states encountered: %d" % self.num_states)
        print()
        self.print_worst_states(100)
        print()
        self.print_worst_joins(100)

    def print_benchmark_summary(self):
        pass
