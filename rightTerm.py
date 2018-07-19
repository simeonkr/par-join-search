from terms import Term, Const, Var, term_types
from loop import Loop
from util import powerset
from solver import EqSolver
from rules import unflatten, flatten

import itertools

LP = None
def loopthrough(s):
    i = 0
    for x in s:
        yield i,x
        i += 1
def printall(l):
    count = 1
    for x in l:
        print(count.__str__() +  ". ", x)
        count += 1

for i in range(1, 3):
    exec("s" + str(i) + " = Var(\"SV\", \"s\"," +  str(i) + ", int)")
for i in range(2):
    exec("a" + str(i) + " = Var(\"IV\", \"a\"," +  str(i) + ", int)")
Z = Const(0)
O = Const(1)

# Returns all of the right induced terms for the loop lp.
def rightAll(lp):
    l = []
    for term in lp.state_terms:
        l.append(right(lp, term))
    return l

#Returns the right-induced version of term, assuming it is in the lp.
def right(lp, term):
    if type(term) == Var and term.vclass == "SV":
        i = term.index
        return lp.get_state_init(i-1)
    if type(term) in {Const, Var}:
        return term
    returned = Term(term.op, [])
    for subterm in term.terms:
        returned.terms.append(right(lp, subterm))
    return returned

#Returns a set of potential start terms for the search algorithm to start from.
def generateStartTerms(lp, solver):
    init_term = lp.get_state_term(lp.get_num_states() - 1)
    rights = rightAll(lp)
    ret = generateStartTermsRecursive(init_term, rights)
    ret = [x for x in ret if equivalent(solver, init_term, x)]
    return ret

# Returns whether a term is made up of only constants and input variables or not.
def constantOnly(term):
    if type(term) == Const:
        return True
    if type(term) == Var:
        return term.vclass != "SV"
    return all([constantOnly(subterm) for subterm in term.terms])

# Returns a new term: same as the old one, but with items appended to its subterms.
#NOTE unused
def termAppendReturn(term, items):
    assert(type(term) == Term)
    term = term.__deepcopy__()
    for x in items:
        term.terms.append(x)
    return term

# Returns a new term: same as the old one, but with subs removed from its subterms.
#NOTE unused
def removeTheseReturn(term, subs):
    new_term = term.__deepcopy__()
    for sub in subs:
        new_term.terms.remove(sub)
    return new_term

def checker(terms):
    def checkit(term):
        if type(term) == Const:
            assert(term.type == type(term.value))
            assert(term.type != Const)
        if type(term) == Term:
            [checkit(subterm) for subterm in term.terms]
    [checkit(term) for term in terms]

# Looks for constant only terms (in this term and the recursively returned subterms)
# and replaces them with the right terms. Will return the set of these generare terms
# that are equivalent to the original term.
maxTerm = Term("max", [s1, a0])
max2Term = Term("max", [s2, Term("min", [s1, a0])])
def generateStartTermsRecursive(term, rights):

    if type(term) == Var and term.vclass == "SV":
        return {term}

    if type(term) in {Var, Const}:
        #dummy = Var("SV", "s", 0, None)
        return {term}.union({right_term for right_term in rights})

    if type(term_types[term.op].arg_type) is not list:

        # NOTE nto any more!!! The output of the algorithm. Initially, just put in the initial term.
        startTerms = set()

        # Generates all versions of this term, by replaces a subterm with a recursive call,
        # for every subterm.

        recursive = [generateStartTermsRecursive(subterm, rights) for subterm in term.terms if (not constantOnly(subterm))] # else [subterm]
        constants = [subterm for subterm in term.terms if constantOnly(subterm)]

        # Get results from applying recursively to subterms who are not state-free.
        for tup in itertools.product(*recursive):
            new_term = Term(term.op, [])
            new_term.terms = list(tup)
            startTerms = startTerms.union({new_term})

        # For every result in
        new_terms = {term}
        l, m = len(constants), len(rights)

        for item in startTerms:
            # removes some constant only terms from the term.
            for cons in powerset(constants):
                for right in powerset(rights):
                    if l != 0 and ((len(cons) == 0 == len(right)) or (len(cons) == l and len(rights) == m)):
                        continue
                    assert(l==0 or (len(list(cons) + list(right)) != 0))
                    new_term = item.__deepcopy__()
                    new_term.terms.extend(list(cons) + list(right))

                    if len(new_term.terms) == 0: #already covered above
                        continue
                    elif len(new_term.terms) == 1:
                        new_term = new_term.terms[0]

                    new_terms = new_terms.union({new_term})
        #

        return new_terms
    else:
        #TODO implement for things like ~, IC, whom have fixed args
        raise NotImplementedError
        return {term}
max2_invars = ["s2>=0", "s1>=0"] #"s1>=s2",
#max2_t = Term("max", [s2, Term("min", [s1, a0])])
max2solver = EqSolver(max2_invars)
#solver = EqSolver([])

def equivalent(solver, orig, new):
    assert(type(orig) in {Const, Term, Var} and type(new) in {Const, Term, Var})
    return True and solver.equivalent(unflatten(orig), unflatten(new))


#min(s1,a0,max(a0,0)) ?= min(s1,a0)
#print("BADDDD ", max2solver.equivalent(Term("min", [s1,a0, Term("max", [a0, Z])] ), Term("min", [s1,a0])))

"max(s2, min(s1,a0))   v.s.   max(s2, 0, min(0, a0), min(s1, max(0, a0)))"
"""print("good", equivalent(max2solver,
                          Term("max", [s2, Term("min", [s1, a0])]),
                          Term("max", [s2,
                                       Const(0),
                                       Term("min", [Const(0), a0]),
                                       Term("min", [s1, Term("max", [Const(0), a0])])])))"""


"max(s2, min(s1,a0)) v.s. max(s2,max(0,min(a0,0)),min(s1,max(a0,0)))"
"""print("not good", equivalent(max2solver,
                              Term("max", [s2, Term("min", [s1, a0])]),
                              Term("max", [s2,
                                           Term("max", [Const(0), Term("min", [Const(0), a0])]),
                              Term("min", [s1, Term("max", [Const(0), a0])])])))"""
