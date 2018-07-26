from itertools import permutations, product

from terms import Const, Var, Term, assoc_ops, term_types


class Rule():

    def __init__(self, cost, app_funct = None):
        self.cost = cost
        self.app_funct = app_funct

    def __str__(self):
        return str(self.__class__.__name__)

    def get_cost(self):
        return self.cost

    def apply(self, term):
        return self.app_funct(term)

    def recurse_apply(self, term):
        if type(term) != Term:
            return []
        out = []
        for i in range(len(term.terms)):
            for rew in self.apply(term.terms[i]):
                new_terms = [subterm.__deepcopy__() for subterm in term.terms]
                new_terms[i] = rew
                out.append(Term(term.op, new_terms))
        return out


class SubstRule(Rule):

    def __init__(self, cost, subst):
        super().__init__(cost)
        self.subst = subst

    def apply(self, term):
        return term.apply_subst(subst)


class RewriteRule(Rule):

    def __init__(self, cost, t1, t2):
        super().__init__(cost)
        self.t1 = t1
        self.t2 = t2

    def apply(self, term):
        out = []
        rew = term.rewrite(self.t1, self.t2)
        if rew:
            out.append(rew)
        return out + self.recurse_apply(term)


class IdentIntroRule(Rule):

    def __init__(self, cost, op, id, target_var=None):
        super().__init__(cost)
        self.op = op
        self.id = id
        self.target_var = target_var
        #self.dont_target = [Var("SV", "s", 2, int)] if op == "+" and True else []

    def apply(self, term):
        out = []
        if type(term) == Var or type(term) == Const:
            if self.target_var and term != self.target_var:
                return []
            if term.type != term_types[self.op].get_ret_type(): # TODO: be careful here and elsewhere
                return []
            out.append(Term(self.op, [term.__deepcopy__(), self.id])) #if term not in self.dont_target else 0
        if type(term) == Term and term.op == self.op:
            if self.target_var is None or self.target_var in term.terms:
                new_term = term.__deepcopy__()
                new_term.terms.append(self.id)
                out.append(new_term)
        return out + self.recurse_apply(term)

class IdentElimRule(Rule):

    def __init__(self, cost, op, id, target_var=None):
        super().__init__(cost)
        self.op = op
        self.id = id
        self.target_var = target_var

    def apply(self, term, target_var=None):
        out = []
        if type(term) == Term and term.op == self.op:
            new_term = term.__deepcopy__()
            if self.id in new_term.terms:
                if self.target_var is None or self.target_var in new_term.terms:
                    new_term.terms.remove(self.id)
                    if len(new_term.terms) == 1:
                        new_term = new_term.terms[0]
                    out.append(new_term)
        return out + self.recurse_apply(term)


class InvIntroRule(Rule):

    def __init__(self, cost, op, inv_func, id, vars):
        super().__init__(cost)
        self.op = op
        self.inv_func = inv_func
        self.id = id
        self.vars = vars

    def apply(self, term):
        out = []
        if term == self.id:
            for var in self.vars:
                out.append(Term(self.op, [var.__deepcopy__(), self.inv_func(var)]))
        if type(term) == Term and term.op == self.op:
            if self.id in term.terms:
                for var in self.vars:
                    new_term = term.__deepcopy__()
                    new_term.terms.remove(self.id)
                    new_term.terms.append(var.__deepcopy__())
                    new_term.terms.append(self.inv_func(var))
                    out.append(new_term)
        return out + self.recurse_apply(term)


class InvElimRule(Rule):

    def __init__(self, cost, op, inv_func, id):
        super().__init__(cost)
        self.op = op
        self.inv_func = inv_func
        self.id = id

    def apply(self, term):
        out = []
        if type(term) == Term and term.op == self.op:
            for subterm in set(term.terms):
                if subterm in term.terms and self.inv_func(subterm) in term.terms:
                    new_term = term.__deepcopy__()
                    new_term.terms.remove(subterm)
                    new_term.terms.remove(self.inv_func(subterm))
                    new_term.terms.append(self.id)
                    if len(new_term.terms) == 1:
                        new_term = new_term.terms[0]
                    out.append(new_term)
        return out + self.recurse_apply(term)


class DupIntroRule(Rule):

    def __init__(self, cost, op):
        super().__init__(cost)
        self.op = op

    def apply(self, term):
        out = []
        if type(term) == Var or type(term) == Const:
            if term.type != term_types[self.op].get_ret_type():
                return []
            out.append(Term(self.op, [term.__deepcopy__(), term.__deepcopy__()]))
        if type(term) == Term and term.op == self.op:
            for subterm in set(term.terms):
                if type(subterm) == Var or type(subterm) == Const: # remember to remove this condition
                    new_term = term.__deepcopy__()
                    new_term.terms.append(subterm)
                    out.append(new_term)
        return out + self.recurse_apply(term)


class DupElimRule(Rule):

    def __init__(self, cost, op):
        super().__init__(cost)
        self.op = op

    def apply(self, term):
        out = []
        if type(term) == Term and term.op == self.op:
            term_counts = {}
            for subterm in term.terms:
                if subterm not in term_counts:
                    term_counts[subterm] = 1
                else:
                    term_counts[subterm] += 1
            for subterm in term_counts.keys():
                if term_counts[subterm] > 1:
                    new_term = term.__deepcopy__()
                    new_term.terms.remove(subterm)
                    if len(new_term.terms) == 1:
                        new_term = new_term.terms[0]
                    out.append(new_term)
        return out + self.recurse_apply(term)


class DistInRule(Rule):

    def __init__(self, cost, dist_ops, over_ops, over_term_inds=None):
        super().__init__(cost)
        self.dist_ops = dist_ops
        self.over_ops = over_ops
        self.over_term_inds = over_term_inds

    def apply(self, term):
        out = []
        if type(term) == Term and term.op in self.dist_ops:
            for over_op in self.over_ops:
                term_inds = []
                other_terms = []
                for i in range(len(term.terms)):
                    if type(term.terms[i]) == Term and term.terms[i].op == over_op:
                        term_inds.append(i)
                    else:
                        other_terms.append(term.terms[i])
                for i in term_inds:
                    for other_term in other_terms:
                        new_term = term.__deepcopy__()
                        for j in range(len(new_term.terms[i].terms)):
                            if self.over_term_inds is None or j in self.over_term_inds:
                                if type(new_term.terms[i].terms[j]) == Term and \
                                        new_term.terms[i].terms[j].op == term.op:
                                    new_term.terms[i].terms[j].terms.append(other_term.__deepcopy__())
                                else:
                                    new_term.terms[i].terms[j] = \
                                        Term(term.op, [other_term.__deepcopy__(),
                                                       new_term.terms[i].terms[j]])
                        new_term.terms.remove(other_term)
                        if len(new_term.terms) == 1:
                            new_term = new_term.terms[0]
                        out.append(new_term)
        return out + self.recurse_apply(term)


class DistOutRule(Rule): # TODO: case when over_term is left with a single variable

    def __init__(self, cost, dist_ops, over_ops, over_term_inds=None):
        super().__init__(cost)
        self.dist_ops = dist_ops
        self.over_ops = over_ops
        self.over_term_inds = over_term_inds

    def apply(self, term):
        if self.over_term_inds is None:
            return self._apply_general(term)
        out = []
        if type(term) == Term and term.op in self.over_ops:
            for dist_op in self.dist_ops:
                dist = True
                comm_terms = None
                for i in self.over_term_inds:
                    subterm = term.terms[i]
                    if type(subterm) == Term and subterm.op == dist_op:
                        if comm_terms == None:
                            comm_terms = set(subterm.terms)
                        else:
                            comm_terms.intersection_update(set(subterm.terms))
                    else:
                        dist = False
                        break
                if dist:
                    for comm_term in comm_terms:
                        p_term = term.__deepcopy__()
                        for i in self.over_term_inds:
                            p_term.terms[i].terms.remove(comm_term)
                            if len(p_term.terms[i].terms) == 1:
                                p_term.terms[i] = p_term.terms[i].terms[0]
                        out.append(Term(dist_op, [comm_term, p_term]))
        return out + self.recurse_apply(term)

    def _apply_general(self, term):
        out = []
        if type(term) == Term and term.op in self.over_ops:
            for dist_op in self.dist_ops:
                ct = {}
                for i in range(len(term.terms)):
                    subterm = term.terms[i]
                    if type(subterm) == Term and subterm.op == dist_op:
                        for subsubterm in subterm.terms:
                            if subsubterm not in ct:
                                ct[subsubterm] = []
                            if i not in ct[subsubterm]:
                                ct[subsubterm].append(i)
                for r_term in ct.keys():
                    if len(ct[r_term]) > 1:
                        paired_terms = []
                        other_terms = []
                        for i in range(len(term.terms)):
                            if i in ct[r_term]:
                                p_term = term.terms[i].__deepcopy__()
                                p_term.terms.remove(r_term)
                                if len(p_term.terms) == 1:
                                    p_term = p_term.terms[0]
                                paired_terms.append(p_term)
                            else:
                                other_terms.append(term.terms[i].__deepcopy__())
                        t_term = Term(dist_op, [r_term, Term(term.op, paired_terms)])
                        if other_terms:
                            out.append(Term(term.op, [t_term] + other_terms))
                        else:
                            out.append(t_term)
        return out + self.recurse_apply(term)


# TODO: generalize the two rules below
class MaxStrengthenRule(Rule):

    def __init__(self, cost, ineq):
        ''' ineq must be of the form x >= y '''
        super().__init__(cost)
        self.greater_term = ineq.terms[0]
        self.lesser_term = ineq.terms[1]

    def apply(self, term):
        out = []
        if term == self.greater_term:
            out.append(Term('max', [self.greater_term.__deepcopy__(),
                                    self.lesser_term.__deepcopy__()]))
        if type(term) == Term and term.op == 'max':
            if self.greater_term in term.terms and self.lesser_term not in term.terms:
                new_term = term.__deepcopy__()
                new_term.terms.append(self.lesser_term.__deepcopy__())
                out.append(new_term)
        return out + self.recurse_apply(term)


class MaxWeakenRule(Rule):

    def __init__(self, cost, ineq):
        ''' ineq must be of the form x >= y '''
        super().__init__(cost)
        self.greater_term = ineq.terms[0]
        self.lesser_term = ineq.terms[1]

    def apply(self, term):
        out = []
        if type(term) == Term and term.op == 'max':
            if self.greater_term in term.terms and self.lesser_term in term.terms:
                new_term = term.__deepcopy__()
                new_term.terms.remove(self.lesser_term)
                if len(new_term.terms) == 1:
                    new_term = new_term.terms[0]
                out.append(new_term)
        return out + self.recurse_apply(term)

class BooleanAxioms(Rule):
    def __init__(self, cost, booleans):
        super().__init__(cost)
        self.booleans = booleans

    def apply(self, term):
        out = []
        if type(term) == Var:
            return []
        """if type(term) == Const:
            if term.type is bool:
                if term.value:
                    for b in self.booleans:
                        out.append(Term("|", [b, Term("~", [b])]))
                if not term.value:
                    pass"""

        if type(term) == Term:# and term.op == self.op:

            if term.get_ret_type() == bool:
                out.append(Term("&", [term.__deepcopy__(), Const(True)]))

            if len(term.terms) == 2:
                subterm = term.terms[0]
                other = term.terms[1]
                if Term("~", [subterm]) == other or subterm == Term("~", [other]):
                    out.append(Const(True))

                """for i in range(2):
                    subterm = term.terms[1-i]
                    other = term.terms[i]
                    if type(subterm) == Term and subterm.op in {"|", "&"}:
                        out.append(Term(subterm.op,
                                        [Term(term.op,
                                               [subsubterm.__deepcopy__(), other])
                                                for subsubterm in subterm.terms]))"""

        return out + self.recurse_apply(term)

    def recurse_apply(self, term):
        if type(term) != Term:
            return []
        out = []
        for i in range(len(term.terms)):
            for rew in self.apply(term.terms[i]):
                new_terms = [subterm.__deepcopy__() for subterm in term.terms]
                new_terms[i] = rew
                out.append(Term(term.op, new_terms))
        return out
### Associativity / Commutativity ###


def flatten(term):
    if type(term) == Const:
        return Const(term.value)
    elif type(term) == Var:
        return Var(term.vclass, term.name, term.index, term.type)
    else:
        new_terms = []
        for subterm in term.terms:
            if type(subterm) == Term and subterm.op in assoc_ops and subterm.op == term.op:
                new_terms.extend(flatten(subterm).terms)
            else:
                new_terms.append(flatten(subterm))
        return Term(term.op, new_terms)


def unflatten(term):
    if type(term) == Term and term.op in assoc_ops and len(term.terms) > 2: #term.flattened
        return Term(term.op, [unflatten(term.terms[0].__deepcopy__()),
                              unflatten(Term(term.op, term.terms[1:]))])
    if type(term) == Term:
        # recurse
        return Term(term.op, [unflatten(subterm) for subterm in term.terms])
    return term.__deepcopy__()


def all_unflatten(term): # modulo state vars
    out = []
    if type(term) == Term:
        if term.op not in assoc_ops:
            for prod in product(*[all_unflatten(subterm) for subterm in term.terms]):
                out.append(Term(term.op, prod))
            return out
        state_terms, raw_terms = [], []
        for i in range(len(term.terms)):
            if not term.terms[i].state_free():
                state_terms.append(term.terms[i].__deepcopy__())
            else:
                raw_terms.append(term.terms[i].__deepcopy__())
        for state_prod in product(*[all_unflatten(state_term) for state_term in state_terms]):
            state_prod = list(state_prod)
            if len(raw_terms) < 2:
                return [Term(term.op, state_prod + raw_terms)]
            if len(raw_terms) == 2:
                for left_unflatten in all_unflatten(raw_terms[0]):
                    for right_unflatten in all_unflatten(raw_terms[1]):
                        if state_prod:
                            out.append(Term(term.op, state_prod +
                                            [Term(term.op, [left_unflatten, right_unflatten])]))
                        else:
                            out.append(Term(term.op, [left_unflatten, right_unflatten]))
            else:
                for perm in set(permutations(raw_terms)): # TODO: identify permutations with same last two terms
                    for left_unflatten in all_unflatten(perm[0]):
                        for right_unflatten in all_unflatten(Term(term.op, perm[1:])):
                            if state_prod:
                                out.append(Term(term.op, state_prod +
                                                [Term(term.op, [left_unflatten, right_unflatten])]))
                            else:
                                out.append(Term(term.op, [left_unflatten, right_unflatten]))
            return out
    return [term.__deepcopy__()]
