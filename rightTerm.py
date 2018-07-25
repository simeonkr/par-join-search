from terms import Term, Const, Var, term_types, comm_ops, assoc_ops
from loop import Loop
from util import powerset
from solver import EqSolver
from rules import unflatten, flatten
from collections import Counter

import itertools

# =====================================================================
# Helper functions that can be moved to util.py or deleted later.
# Also some variables declared for testing.
# =====================================================================
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

# =====================================================================
# Helper functions for the function generateStartTerms.
# =====================================================================

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

def removeDup(term):
    if type(term) in {Const, Var}:
        return term
    new_term = Term(term.op, [])
    new_term.terms = list(set(flatten(term).terms))
    return new_term

THRESHOLD = 1
def TOOmanyHELP(term, rights):
    if term in rights:
        return Counter({term: 1})

    if type(term) == Term:
        c1 = sum([ Counter(TOOmanyHELP(subterm, rights)) for subterm in term.terms], Counter())
        c2 = sum([ Counter({term: 1}) for right in rights
                                 if (type(right) == Term and right.op == term.op
                                                         and term.op in comm_ops
                                                         and all([(r in term.terms) for r in right.terms]) )], Counter())
        return c1 + c2

    else:
        return Counter()

"Returns depth of subterm in term. -1 if not in subterm."
def TOOmany(term, rights):
    return any([y > THRESHOLD for y in dict(TOOmanyHELP(term, rights)).values()])

# REturn true iff subterm a is in term b. TODO put in Var/Const/Term classes.
# TODO
def inn(a, b):
    if type(b) in {Const, Var}:
        return a==b
    return a==b or any(inn(a, sub) for sub in b.terms)

infinity = 10000000
#NOTE here the depth is sometimes counted wrong because of one term being contained in another!
#So a thing TODOP change so it does all right things at the same time.
"Returns depth of subterm in term. 1000000000 if not in subterm"
def depthOfSub(term, rights):
    if type(term) in {Const, Var}:
        if term in rights:
            d = {right : infinity for right in rights if right != term}
            d[term] = 0
            return d
        else:
            return {right : infinity for right in rights}
    d = {}

    for subterm in rights:
        if term == subterm or (type(subterm) == Term and subterm.op == term.op and term.op in assoc_ops and all([(t in term.terms) for t in subterm.terms])):
            d[subterm] = 0
        else:

            temp = min([depthOfSub(sub, rights)[subterm] for sub in term.terms])
            d[subterm] = infinity if temp == infinity else 1 + temp
    return d

"""Unused and unimplemented function (for now).
Should return lst so that if x in y, then x only occurs before y in the lst
(or the opposite, doesn't really matter)."""
def dependencySort(lst):
    return lst
    l = []
    count = 0
    for x in lst:
        pos = count
        for y in l:
            if inn(x,y):
                pass
            elif inn(y,x):
                pass
            else:
                pass
        l.insert(x)
        count += 1
    return l

"""Returns only the elements from generateStartTermsRecursive
that have the right subterms at a higher level."""
def outermost(ret, rights):
    returned = list(ret)
    keepers = []
    R = list(rights)
    R.reverse()
    for right in R[len(R)-2 : len(R)-1]:#range(len(rights), -1, -1):
        mindepth = infinity
        for r,depth in [(r, depthOfSub(r, rights)[right]) for r in returned]:#filter(lambda x : x[0] != -1, [(r, depthOfSub(r, right)) for r in returned]):
            if depth < mindepth:
                mindepth = depth
                keepers = [r]
            elif depth == mindepth:
                keepers.append(r)
    return keepers

def getOccurences(term, rights, inf=False):
    return dict(filter(lambda x : inf or x[1] < infinity, [(right, depthOfSub(term, rights)[right]) for right in rights]))

def filterReturned(terms, rights):
    out = set(terms)
    R = list(rights)
    R.reverse()
    #R = {R[0]} #NOTE /TODO ???!?!??!
    depth = {term: getOccurences(term, rights) for term in terms}
    for right in R:
        mindepth = infinity
        the = set()
        for term in terms:
            if right in depth[term]:
                if depth[term][right] < mindepth:
                    the = {term}
                    mindepth = depth[term][right]
                elif depth[term][right] == mindepth:
                    the = the.union({term})
            else:
                the = the.union({term})
        out = out.intersection(the)
    return out
# =====================================================================
# generateStartTerms:

# Returns a set of potential start terms for the search algorithm to start from.
# =====================================================================

def generateStartTerms(lp, solver):
    init_term = lp.get_state_term(lp.get_num_states() - 1)
    rights = rightAll(lp)
    print("rights : ", rights)
    ret = generateStartTermsRecursive(init_term, rights)
    ret = [term for term in ret if not TOOmany(term, rights)]

    ret = {removeDup(x) for x in ret}
    ret = {x for x in ret if equivalent(solver, init_term, x)}
    # TODO limit new_terms so it only includes min depth terms
    #TODO perhaps store a dictionary then filter?
    # also because recursion do in caller function?
    #new_terms = [x for x in new_terms if True]
    #ret = set(outermost(ret, rights))

    printall(ret)
    printall(outermost(ret, rights))
    #ret = filterReturned(ret, rights)
    #ret = [x for x in ret if x.__str__() != "max(s2,0,IC(a0,(s1+1),IC(a0,(0+1),0)),IC(a0,(0+1),0))"]
    print("A")


    right_init = rights[len(rights)-1]
    right_init_subs = getOccurences(right_init, rights, True)
    ret = list(filter(lambda x: all([depth <= right_init_subs[right] + 1 for right,depth in getOccurences(x, rights).items()]), ret))

    #ret = [x for x in ret if x.__str__() == "max(s2,0,IC(a0,(s1+1),0),IC(a0,(0+1),0))"]
    #ret = [x for x in ret if x.__str__() in {"max(s2,a0,(s1+max(a0,0,(a0+0))),(a0+0))", "max(s2,a0,0,(s1+a0),(a0+0))"}]

    return ret

# =====================================================================
# Helpers for the function generateStartTermsRecursive.
# =====================================================================

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

return_type_of_term = lambda term: term.type if type(term) in {Var, Const} else term.get_ret_type()

# =====================================================================

# Looks for constant only terms (in this term and the recursively returned subterms)
# and replaces them with the right terms. Will return the set of these generare terms
# that are equivalent to the original term.

# =====================================================================

def generateStartTermsRecursive(term, rights):

    if type(term) == Var and term.vclass == "SV":
        return [ term ]

    if type(term) in {Var, Const}:
        #dummy = Var("SV", "s", 0, None)
        return [ term ] + [ right_term for right_term in rights if term.type == return_type_of_term(right_term)  ]

    if type(term_types[term.op].arg_type) is not list:

        # NOTE nto any more!!! The output of the algorithm. Initially, just put in the initial term.
        startTerms = list()

        # Generates all versions of this term, by replaces a subterm with a recursive call,
        # for every subterm.

        recursive = [generateStartTermsRecursive(subterm, rights) for subterm in term.terms if (not constantOnly(subterm))] # else [subterm]
        constants = [subterm for subterm in term.terms if constantOnly(subterm)]

        # Get results from applying recursively to subterms who are not state-free.
        for tup in itertools.product(*recursive):
            new_term = Term(term.op, [])
            new_term.terms = [x for x in tup]
            startTerms.append(new_term)

        # For every result in
        new_terms = [term]
        #new_dict = dict(sum([Counter(generateStartTermsRecursive(subterm, rights)[1]) for subterm in term.terms]))
        l, m = len(constants), len(rights)

        for item in startTerms:
            # removes some constant only terms from the term.
            for cons in powerset(constants):
                for right in powerset([right for right in rights if return_type_of_term(right) == item.get_arg_type(0)]):
                    if l != 0 and ((len(cons) == 0 == len(right)) or (len(cons) == l and len(rights) == m)):
                        continue
                    assert(l==0 or (len(list(cons)) + len(list(right)) != 0))
                    new_term = item.__deepcopy__()
                    new_term.terms.extend(list(cons) + list(right))

                    if len(new_term.terms) == 0: #already covered above
                        continue
                    elif len(new_term.terms) == 1:
                        new_term = new_term.terms[0]

                    new_terms.append(new_term)
        #

        return new_terms
    else: #type(term_types[term.op].arg_type) is list:
        #TODO implement for things like ~, IC, whom have fixed args
        NUM = len(term_types[term.op].arg_type)

        # NOTE nto any more!!! The output of the algorithm. Initially, just put in the initial term.
        startTerms = list()

        # Generates all versions of this term, by replaces a subterm with a recursive call,
        # for every subterm.

        recursive = [generateStartTermsRecursive(subterm, rights) if not constantOnly(subterm) else [subterm] for subterm in term.terms]

        # Get results from applying recursively to subterms who are not state-free.
        for tup in itertools.product(*recursive):
            new_term = Term(term.op, [])
            new_term.terms = [x for x in tup]
            startTerms.append(new_term)

        # For every result in
        new_terms = [term]

        for item in startTerms:
            # removes some constant only terms from the term.
            for i,subterm in loopthrough(item.terms):
                if constantOnly(subterm):
                    for right in [right for right in rights if return_type_of_term(right) == return_type_of_term(subterm)]:
                        new_term = item.__deepcopy__()
                        new_term.terms[i] = right

                        new_terms.append(new_term)
        #

        return new_terms

# =====================================================================
# Some testing. Probably should move to rightTermTest.py
# =====================================================================


max2_invars = ["s2>=0", "s1>=0"] #"s1>=s2",
max2solver = EqSolver(max2_invars)
maxTerm = Term("max", [s1, a0])
max2Term = Term("max", [s2, Term("min", [s1, a0])])

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

#====================================================
# Testing the subset of term feature
#====================================================

sub = Term("+", [s1, a0])
term = Term("max", [s2, sub, a0])

assert(inn(sub, term))
assert(not inn(term, sub))
