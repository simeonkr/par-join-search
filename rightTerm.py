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

for i in range(1, 5):
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
    d = {}
    i = 1
    for term in lp.state_terms:
        rsv = Var("RSV", "s", i, lp.get_state_init(i-1).type)
        d[rsv] = right(lp, term)
        i += 1
    return d

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

# For the given term/invariant, returns the same invariant but with all of its
# state variables replaced with the RSV versions.
def rightMe(invar):

    if type(invar) == Const:
        return invar
    if type(invar) == Var:
        return invar if invar.vclass == "RSV" else Var("RSV", invar.name, invar.index, invar.type)
    return Term(invar.op, [rightMe(x) for x in invar.terms])

# Simplifies a term from the algorithm by remving any repeated subterms or
# other redudancies.
def removeDup(solver, rights, term, invars, lastState):
    #print()
    if type(term) in {Const, Var} or not term_types[term.op].fixed_args:
        return term

    term = Term(term.op, list(set(flatten(term).terms)))
    # Supposed to be something like op(si, ...) ==> join = op(siL, siR, ...)
    # Doesn't always work : see mps
    # Also seems redundant
    """if lastState in term.terms and rightMe(lastState) not in term.terms:
        new_term = term.__deepcopy__()
        new_term.terms.append(rightMe(lastState))
        if equivalent(solver, rights, induceRight(term, rights), new_term, True):
            term = new_term"""

    # If term is like max(a,b,...) and a >= b is an invaraint, then turn the
    # term into max(a,...)
    for invar in invars:
        # TODO generalize
        invar2 = rightMe(invar)
        if invar.op in {">=", ">"}:
            for x in [invar, invar2]:
                if set(x.terms).issubset(term.terms):
                    if term.op == "max":
                        term.terms.remove(x.terms[1])
                    elif term.op == "min":
                        term.terms.remove(x.terms[0])
    #print("ABA", new_term)
    return term

THRESHOLD = 1
# Returns the number of occurences of a right state variable in a term.
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


infinity = 10000000
#NOTE here the depth is sometimes counted wrong because of one term being contained in another!
#So a thing TODO change so it does all right things at the same time.
"Returns how deep each right SV is in term. 1000000000 if not in term"
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
            if x in y:
                pass
            elif y in x:
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

def stringDeclaration(term, rec=True):
    if type(term) == Const:
        return "Const(" + term.value.__str__() + ")"
    if type(term) == Var:
        return "Var(" + term.vclass + ", " + term.name + "," + str(term.index) + ", " + str(term.type) + ")"

    if rec:
        return "Term(" + term.op + ", " + str([stringDeclaration(subterm, rec) for subterm in term.terms]) + ")"

    return "Term(" + term.op + ", " + str(term.terms) + ")"

def highDepthRight(solver, rights, init_term, ret, lastState):

    if type(init_term) in {Const, Var} or not term_types[init_term.op].fixed_args or lastState not in init_term.terms:
        return ret
    new_term = init_term.__deepcopy__()
    rightSV = rightMe(lastState)
    new_term.terms.append(rightSV)

    if not equivalent(solver, rights, init_term, new_term):
        return ret

    canAdd = lambda subterm: not ((type(subterm) == Const) or (type(subterm) == Var and subterm != rightSV and subterm.vclass == "RSV"))
    cond = lambda item : type(item) == Term and lastState in item.terms and rightSV in item.terms

    new_ret = []
    for item in ret:
        if cond(item):
            new_ret.append(item)
        elif all(canAdd(subterm) for subterm in item.terms):
            new_item = item.__deepcopy__()
            new_item.terms.append(rightSV)
            new_ret.append(new_item)
    return new_ret

def generateStartTerms(lp, solver, invars):
    STR = "IC(((s2+a0)>=IC(((a0+0)>=0),(a0+0),0)),s3,(s1+IC(((a0+0)>=0),0,(0+1))))"
    init_term = flatten(lp.get_state_term(lp.get_num_states() - 1))
    lastState = Var("SV", "s", lp.get_num_states())

    rights = rightAll(lp)
    print("rights : ", rights)
    print("right vars :", [str(x) for x in list(rights.keys())])
    ret = generateStartTermsRecursive(init_term, init_term, solver, list(rights.keys()))
    #print("at first :")
    #printall(ret)
    #print("rer", ret)
    ret = {x for x in ret if equivalent(solver, rights, init_term, x)}# or x.__str__() == STR]
    print("equiv")
    printall(ret)
    ret = highDepthRight(solver, rights, init_term,  ret, lastState)
    ret = {removeDup(solver, rights, x, invars, lastState) for x in ret}.difference({None})
    print("removeDup")
    printall(ret)




    ret = {term for term in ret if not TOOmany(term, rights)}

    #print("rer")
    #printall(ret)

    #ret = filterReturned(ret, rights)

    #right_init = rights[len(rights)-1]
    #right_init_subs = getOccurences(right_init, rights, True)
    #ret = list(filter(lambda x: x.__str__() == STR or all([depth <= right_init_subs[right] + 1 for right,depth in getOccurences(x, rights).items()]), ret))
    #assert([x for x in ret if x.__str__() == STR] != [])


    #ret = [x for x in ret if x.__str__() == "max(s2,0,IC(a0,(s1+1),0),IC(a0,(0+1),0))"]
    #ret = [x for x in ret if x.__str__() in {"max(s2,a0,(s1+max(a0,0,(a0+0))),(a0+0))", "max(s2,a0,0,(s1+a0),(a0+0))"}]
    #printall(ret)

    mtsR = Term("IC", [ Term(">=", [Term("+", [Z, a0]), Z]), Term("+", [Z, a0]), Z])
    posR = Term("IC", [Term(">=", [Term("+", [Z, a0]), Z]), Z, Term("+", [Z, O])])


    #IC(0+a0 + s2 > IC(0+a0>0, 0+a0, 0), S3, S1+ IC(0 + a0 > 0, 0, 0+1))
    """ret = [Term("IC", [ Term(">=", [
                                   Term("+", [Z, a0, s2]),
                                   mtsR]),
	                    s3,
	                    Term("+", [s1, posR])])]"""
    #print(ret[0])
    #ret = [unflatten(x) for x in ret]

    print("init:", init_term)
    print("### Final output : ")
    printall(ret)
    print()
    #print([list({induceRight(term, rights) for term in ret})[len(ret)-1]])
    return list({induceRight(term, rights) for term in ret})
    #return [list({induceRight(term, rights) for term in ret})[len(ret)-1]] #ret

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

def generateStartTermsRecursive(term, init_term, solver, rights):
    if type(term) == Var and term.vclass == "SV":
        return [ term ]

    if type(term) in {Var, Const}:
        #dummy = Var("SV", "s", 0, None)
        #print("A", term)
        #print([ term ] + [ right_term for right_term in rights if term.type == return_type_of_term(right_term)  ])
        return [ term ] + [ right_term for right_term in rights if term.type == return_type_of_term(right_term)  ]

    old = 0
    if old:
        if type(term_types[term.op].arg_type) is not list:
            #print("AAA")
            # NOTE nto any more!!! The output of the algorithm. Initially, just put in the initial term.
            startTerms = list()

            # Generates all versions of this term, by replaces a subterm with a recursive call,
            # for every subterm.

            recursive = [generateStartTermsRecursive(subterm, init_term, solver, rights) for subterm in term.terms if (not constantOnly(subterm))] # else [subterm]
            #print("recursive =", recursive)
            constants = [subterm for subterm in term.terms if constantOnly(subterm)]
            #print("constants =", constants)
            #print("rights =", [str(x) for x in rights])

            # Get results from applying recursively to subterms who are not state-free.
            for tup in itertools.product(*recursive):
                new_term = Term(term.op, [])
                new_term.terms = [x for x in tup]
                startTerms.append(new_term)

            # For every result in
            new_terms = [term.__deepcopy__()]
            #new_dict = dict(sum([Counter(generateStartTermsRecursive(subterm, rights)[1]) for subterm in term.terms]))
            l, m = len(constants), len(rights)

            for item in startTerms:
                # removes some constant only terms from the term.
                for cons in powerset(constants):
                    for right in powerset([right for right in rights if return_type_of_term(right) == item.get_arg_type(0)]):
                        #print("\t", list(cons) + list(right))
                        if len(constants) !=0 and len(cons) == 0 == len(right):
                            #print("\tbad", list(cons) + list(right))
                            continue
                        assert(l==0 or (len(list(cons)) + len(list(right)) != 0))
                        new_term = item.__deepcopy__()
                        new_term.terms.extend(list(cons) + list(right))

                        if len(new_term.terms) == 0: #already covered above
                            continue
                        elif len(new_term.terms) == 1:
                            new_term = new_term.terms[0]

                        new_terms.append(new_term)
            #print("new_terms =", new_terms)
            #return [ x for x in new_terms if equivalent(solver, init_term, x) ]
            return new_terms
        else: #type(term_types[term.op].arg_type) is list:
            #TODO implement for things like ~, IC, whom have fixed args
            NUM = len(term_types[term.op].arg_type)

            # NOTE nto any more!!! The output of the algorithm. Initially, just put in the initial term.
            startTerms = list()

            # Generates all versions of this term, by replaces a subterm with a recursive call,
            # for every subterm.

            recursive = [generateStartTermsRecursive(subterm, init_term, solver, rights) for subterm in term.terms] # if not constantOnly(subterm) else [subterm]

            # Get results from applying recursively to subterms who are not state-free.
            for tup in itertools.product(*recursive):
                new_term = Term(term.op, [])
                new_term.terms = [x for x in tup]
                startTerms.append(new_term)

            return startTerms

    else:
        startTerms = list()
        # Generates all versions of this term, by replaces a subterm with a recursive call,
        # for every subterm.
        recursive = [generateStartTermsRecursive(subterm, init_term, solver, rights) for subterm in term.terms]

        for tup in itertools.product(*recursive):
            new_term = Term(term.op, [])
            new_term.terms = [x for x in tup]
            startTerms.append(new_term)

        if constantOnly(term):
            startTerms.extend([ right_term for right_term in rights if return_type_of_term(term) == return_type_of_term(right_term)  ])

        return startTerms

# =====================================================================
# Some testing. Probably should move to rightTermTest.py
# =====================================================================


max2_invars = ["s2>=0", "s1>=0"] #"s1>=s2",
max2solver = EqSolver(max2_invars)
maxTerm = Term("max", [s1, a0])
max2Term = Term("max", [s2, Term("min", [s1, a0])])


def induceRight(term, rights):
    if type(term) == Const:
        return term.__deepcopy__()
    if type(term) == Var:
        if term.vclass == "RSV":
            return rights[term]
        return term.__deepcopy__()
    return Term(term.op, [induceRight(subterm, rights) for subterm in term.terms])

def equivalent(solver, rights, orig, new, printMe=False):
    assert(type(orig) in {Const, Term, Var} and type(new) in {Const, Term, Var})
    out = solver.equivalent(unflatten(flatten(orig)), unflatten(flatten(induceRight(new, rights))))
    print("### Solver: ", flatten(orig), "v.s.", flatten(new), "(", flatten(induceRight(new, rights)) , ") = ", out) if printMe else 0
    return True and out


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

assert(sub in term)
assert(not term in sub)
