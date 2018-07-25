from terms import Var, Const, Term, term_types

def validJoin(join):
    if not (validLoop(join.loop) and validTerm(join.term)):
        return False

    #TODO ensure all vars in term are also in loop?
    return True


def validLoop(loop, debug=1):

    init_values = loop.state_init
    terms = loop.state_terms
    
    if len(init_values) != len(terms):
        return False
    diction = {}
    for i in range(len(terms)):
        init = init_values[i]
        term = terms[i]

        (init_type, _) = term_type(init)
        (term_typed, term_dict) = term_type(term)

        if init_type is False or term_typed is False:
            return False

        for key in term_dict:
            if key in diction and diction[key] != term_dict[key]:
                return False
            else:
                diction[key] = term_dict[key]

    #TODO check s_i values against infered values?
    return True


def validTerm(term):
    return True

def term_type(term, debug=0):
    """ Returns the type of the term, plus the type of each var in a dict.
     or None is the term is not valid. Invalid
    because one of the following holds:
    -
    -
    -
    """

    if type(term) == Const:
        if debug:
            print("\t", term, " type = ", (term.type, {}))
        return (term.type, {})

    if type(term) == Var:


        if term.type is None:
            if debug:
                print("\t", term, " type = ", (term.type, {}))
            return (term.type, {})

        if debug:
            print("\t", term, " type = ", (term.type, {term: term.type}))

        return (term.type, {term: term.type})

    # The value of the result of the operator
    ret = term.get_ret_type()

    n = 0
    diction = {}
    for t in term.terms:
        (typed, type_dict) = term_type(t, debug)

        if typed is False or (typed is not None and typed != term.get_arg_type(n)):
            return (False, {})

        # Has no type, must infer
        if typed is None:
            type_dict[t] = term.get_arg_type(n)

        for key in type_dict:
            if key in diction and diction[key] != type_dict[key]:
                return (False, {})
            elif key not in diction:
                diction[key] = type_dict[key]
        n += 1

    return (ret, diction)

# checks
s1 = Var("SV", 's', 1, int)
s3 = Var("SV", 's', 3, bool)
s4 = Var("SV", 's', 4) # THIS is supposed to be bool
a0b = Var("IV", "a", 0, bool)
z = Const(0)
"""
assert(term_type(s1)[0] == int)
assert(term_type(s1)[1] == {s1: int})

assert(term_type(s4)[0] == None)
assert(term_type(s4)[1] == {})



assert(term_type(Term("max", [s1, z]))[0] == int)
assert(term_type(Term("max", [s1, z]))[1] == {s1: int})

assert(term_type(Term("max", [s1, Const(False)]))[0] is False)
assert(term_type(Term("max", [s1, Const(False)]))[1] == {})

assert(term_type(Term("IC", [a0b, Term("+", [s1, Const(1)]), Const(0)]))[0] == int)
assert(term_type(Term("IC", [a0b, Term("+", [s1, Const(1)]), Const(0)]))[1] == {s1: int, a0b:bool})

assert(term_type(Term("&", [s3, a0b]))[0] == bool)
assert(term_type(Term("&", [s3, a0b]))[1] == {s3: bool, a0b:bool})
"""
"""
assert(term_type(Term("&", [s4, a0b]))[0] == bool)
assert(term_type(Term("&", [s4, a0b]))[1] == {s4: bool, a0b:bool})

#s4 cannot be both int and bool
assert(term_type(Term("IC", [s4, s4, Const(0)]))[0] is False)
assert(term_type(Term("IC", [s4, s4, Const(0)]))[1] == {})
"""
