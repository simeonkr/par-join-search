from copy import deepcopy


class Const:

    def __init__(self, value):
        self.value = value
        self.type = type(self.value)

    def __eq__(self, other):
        if type(other) != Const or type(self.value) != type(other.value):
            return False
        return self.value == other.value

    def __lt__(self, other):
        if type(other) == Const:
            if type(self.value) == type(other.value):
                return self.value < other.value
            else: return self.value # TODO: do something smarter
        elif type(other) == Var:
            return False
        elif type(other) == Term:
            return True

    def __hash__(self):
        return hash(self.value)

    def __deepcopy__(self, memo=None):
        return Const(self.value)

    def __str__(self):
        return self.get_str()

    def get_str(self, for_ev=False):
        if not for_ev and isinstance(self.value, bool):
            return str(self.value)[0]
        return str(self.value)

    def __repr__(self):
        return self.__str__()

    def __contains__(self, other):
        return self == other

    def length(self):
        return 1

    def get_vars(self):
        return set()

    def get_subterm_index(self, subterm):
        if self == subterm:
            return []
        else:
            return None

    def apply_subst(self, subst):
        return Const(self.value)

    def offset(self, i, vclass = "IV"):
        return Const(self.value)

    def rename(self, old_vclass, new_vclass):
        return Const(self.value)

    def reindex(self, var, i):
        return Const(self.value)

    def state_free(self, vclass = "SV"):
        return True

    def match(self, other, subst = None):
        if subst == None:
            subst = {}
        if type(other) == Var:
            if other in subst:
                if subst[other] == self:
                    return subst
                return None
            else:
                subst[other] = Const(self.value)
                return subst
        return None

    def rewrite(self, pat, obj):
        subst = self.match(pat)
        if subst:
            return obj.applySubst(subst)
        else:
            return None

    def subterm_rewrites(self, rule):
        rew = self.rewrite(rule)
        if rew:
            return [rew]
        else:
            return []

    def demaxify(self):
        return Const(self.value)

    def negate(self):
        return Const(False) if self.value == True else Const(True)

    '''
    def minus(self):
        return Const(-self.value);

    def normalize(self):
        return Const(self.value)
    '''


class Var(Const):

    def __init__(self, vclass, name, index, type_=None):
        self.vclass = vclass
        self.name = name
        self.index = index
        self.type = type_

    def __eq__(self, other):
        if type(other) != Var:
            return False
        return self.vclass == other.vclass and \
            self.name == other.name and \
            self.index == other.index

    def __lt__(self, other):
        if type(other) == Var:
            if self.vclass != other.vclass:
                return self.vclass == 'SV'
            if self.name == other.name:
                return self.index < other.index
            else:
                return self.name < other.name
        elif type(other) == Const:
            return True
        elif type(other) == Term:
            return True

    def __hash__(self):
        return hash((self.vclass, self.name, self.index))

    def __deepcopy__(self, memo=None):
        return Var(self.vclass, self.name, self.index, self.type)

    def __str__(self):
        if self.vclass == "LSV": sub = "l"
        elif self.vclass == "RSV": sub = "r"
        else: sub = ""
        return self.name + sub + str(self.index)

    def get_str(self, for_ev=False):
        if for_ev and self.type == bool:
            return self.__str__() + 'b'
        return self.__str__()

    def __repr__(self):
        return self.__str__()

    def __contains__(self, other):
        return self == other

    def length(self):
        return 1

    def get_vars(self):
        return set(self.__deepcopy__())

    def get_subterm_index(self, subterm):
        if self == subterm:
            return []
        else:
            return None

    def apply_subst(self, subst):
        if self in subst.keys():
            return subst[self]
        else:
            return self.__deepcopy__()

    def offset(self, i, vclass = "IV"):
        if self.vclass == vclass:
            return Var(vclass, self.name, self.index + i, self.type)
        else:
            return self.__deepcopy__()

    def rename(self, old_vclass, new_vclass):
        if self.vclass == old_vclass:
            return Var(new_vclass, self.name, self.index, self.type)
        else:
            return self.__deepcopy__()

    def reindex(self, var, i):
        if self == var:
            return Var(self.vclass, self.name, i, self.type)
        else:
            return self.__deepcopy__()

    def state_free(self, vclass = "SV"):
        return self.vclass != vclass

    def match(self, other, subst = None):
        if subst == None:
            subst = {}
        if type(other) == Var:
            if other in subst:
                if subst[other] == self:
                    return subst
                return None
            else:
                subst[other] = self.__deepcopy__()
                return subst
        return None

    def demaxify(self):
        return self.__deepcopy__()

    def negate(self):
        return Term('~', [self.__deepcopy__()])

    '''
    def negate(self):
        return Term('~', [self.__deepcopy__()])

    def minus(self):
        return Term('-', [self.__deepcopy__())

    def normalize(self):
        return self.__deepcopy__()
    '''


ops = ["max", "min", "+", "*", "-", "&", "|", "IC", "BC", "=", "~", "~=", ">", ">="]
unary_ops = ['~', '-']
infix_ops = ['+', '*', '&', '|', '=', '~=', '>', '>=']
assoc_ops = ['+', '*', '&', '|', 'max', 'min']
comm_ops = ['+', '*', '&', '|', '=', '~=', 'max', 'min']


class TermType():

    def __init__(self, arg_type, ret_type, fixed_args=True):
        self.arg_type = arg_type # list if fixed_args else single type
        self.ret_type = ret_type
        self.fixed_args = fixed_args

    def get_arg_type(self, n):
        if self.fixed_args:
            return self.arg_type
        return self.arg_type[n]

    def get_ret_type(self):
        return self.ret_type


term_types = {}
term_types['+'] = TermType(int, int)
term_types['*'] = TermType(int, int)
term_types['-'] = TermType([int], int, False)
term_types['>'] = TermType([int, int], bool, False)
term_types['>='] = TermType([int, int], bool, False)
term_types['max'] = TermType(int, int)
term_types['min'] = TermType(int, int)
term_types['&'] = TermType(bool, bool)
term_types['|'] = TermType(bool, bool)
term_types['~'] = TermType([bool], bool, False)
term_types['BC'] = TermType([bool, bool, bool], bool, False)
term_types['IC'] = TermType([bool, int, int], int, False)
term_types['~'] = TermType([bool], bool, False)

class Term(Const):

    def __init__(self, op, terms):
        self.op = op
        self.terms = [term.__deepcopy__() for term in terms]

    def __eq__(self, other):
        if type(other) != Term:
            return False
        return self.op == other.op and len(self.terms) == len(other.terms) \
            and sorted(self.terms) == sorted(other.terms)
        '''
        # syntactic equality
        return self.op == other.op and len(self.terms) == len(other.terms) \
            and all([self.terms[i] == other.terms[i] for i in range(len(self.terms))])
        '''

    def comm_eq(self, other):
        if type(other != Term):
            return self.op == other.op and len(self.terms) == len(other.terms) \
                and set(self.terms) == set(other.terms)

    def __lt__(self, other):
        if type(other) == Const or type(other) == Var:
            return False
        if self.op == other.op:
            return self.terms < other.terms
        return self.op < other.op

    def __hash__(self):
        return hash((self.op, tuple(sorted(self.terms))))
        #return hash(self.__str__())

    def __deepcopy__(self, memo=None):
        return Term(self.op, self.terms)

    def __str__(self):
        return self.get_str()

    def get_str(self, for_ev=False):
        sorted_subterms = sorted(self.terms) if self.op in comm_ops else self.terms
        if for_ev and self.op == '~':
            return 'Not({})'.format(sorted_subterms[0].get_str(for_ev))
        if self.op in unary_ops and type(sorted_subterms[0]) != Term:
            return self.op + sorted_subterms[0].get_str(for_ev)
        if self.op == '+':
            out_str = '(' + sorted_subterms[0].get_str(for_ev)
            for term in sorted_subterms[1:]:
                out_str += term.get_str(for_ev) if type(term) == Term and term.op == '-' \
                    else '+' + term.get_str(for_ev)
            out_str += ')'
            return out_str

        # format for solver (TODO: do something cleaner)
        if for_ev and self.op == '&':
            return 'And({},{})'.format(sorted_subterms[0].get_str(for_ev),
                                       sorted_subterms[1].get_str(for_ev))
        if for_ev and self.op == '|':
            return 'Or({},{})'.format(sorted_subterms[0].get_str(for_ev),
                                      sorted_subterms[1].get_str(for_ev))
        if for_ev and self.op == '~':
            return 'Not({})'.format(sorted_subterms[0].get_str(for_ev))

        if self.op in infix_ops:
            return '(' + self.op.join([term.get_str(for_ev) for term in sorted_subterms]) + ')'
        return self.op + '(' + ','.join([term.get_str(for_ev) for term in sorted_subterms]) + ')'

    def __repr__(self):
        return self.__str__()

    def __contains__(self, other):
        if any((other in subterm) for subterm in self.terms):
            return True
        if not term_types[self.op].fixed_args:
            return self == other

        #TODO. both comm/assoc?
        if type(other) == Term and self.op == other.op and self.op in assoc_ops and self.op in comm_ops:
            return set(other.terms).issubset(self.terms)

        return False

    def length(self):
        return sum([term.length() for term in self.terms]) + 1

    def get_arg_type(self, n):
        return term_types[self.op].get_arg_type(n)

    def get_ret_type(self):
        return term_types[self.op].get_ret_type()

    def get_vars(self):
        vars = set()
        for term in self.terms:
            vars = vars.union(term.get_vars())
        return vars

    def num_vars(self):
        return len(self.get_vars())

    def get_term_at(self, index):
        if len(index) == 0:
            return self.__deepcopy__()
        elif len(index) == 1:
            return self.terms[index[0]]
        return self.terms[index[0]].get_term_at(index[1:])

    def set_term_at(self, index, term):
        if len(index) == 1:
            if type(term) == Const:
                self.terms[index[0]] = Const(term.value)
            elif type(term) == Var:
                self.terms[index[0]] = Var(term.vclass, term.name, term.index, term.type)
            else:
                self.terms[index[0]] = term.__deepcopy__()
        elif len(index) > 1:
            self.terms[index[0]].set_term_at(index[1:], term)

    # finds only first occurence
    def get_subterm_index(self, subterm):
        if self == subterm:
            return []
        else:
            for i in range(len(self.terms)):
                si = self.terms[i].get_subterm_index(subterm)
                if si != None:
                    return [i] + si
            return None

    def apply_subst(self, subst):
        if self in subst.keys():
            return subst[self].apply_subst(subst)
        new_terms = []
        for term in self.terms:
            new_term = term.apply_subst(subst)
            new_terms.append(new_term)
        return Term(self.op, new_terms)

    def apply_subst_multi(self, subst, k):
        out_term = self.__deepcopy__()
        for i in range(k):
            out_term = out_term.offset(1)
            out_term = out_term.apply_subst(subst)
        return out_term

    def offset(self, i, vclass = "IV"):
        return Term(self.op, [term.offset(i, vclass) for term in self.terms])

    def rename(self, old_vclass, new_vclass):
        return Term(self.op, [term.rename(old_vclass, new_vclass) for term in self.terms])

    def reindex(self, var, i):
        return Term(self.op, [term.reindex(var, i) for term in self.terms])

    def state_free(self, vclass = "SV"):
        return all([term.state_free(vclass) for term in self.terms])

    def match(self, other, subst = None):
        if subst == None:
            subst = {}
        if type(other) == Term:
            if self.op == other.op and len(self.terms) == len(other.terms):
                for i in range(len(self.terms)):
                    subst = self.terms[i].match(other.terms[i], subst)
                    if not subst:
                        return None
                return subst
            else:
                return None
        elif type(other) == Var:
            if other in subst:
                if subst[other] == self:
                    return subst
                return None
            else:
                subst[other] = self.__deepcopy__()
                return subst
        else:
            return None

    def demaxify(self):
        new_terms = [term.demaxify() for term in self.terms]
        if self.op == 'max':
            return Term('C', [Term('>=', [new_terms[0], new_terms[1]]), new_terms[0], new_terms[1]])
        elif self.op == 'min':
            return Term('C', [Term('<=', [new_terms[0], new_terms[1]]), new_terms[0], new_terms[1]])
        else:
            return Term(self.op, new_terms)

    def negate(self):
        if self.op == '~': # TODO: maybe not the place to do this as this should be a syntactic operation
            return self.terms[0].__deepcopy__()
        return Term('~', [self.__deepcopy__()])

    '''
    # defined for conditional-free terms only
    # should preserve normality
    def negate(self):
        if self.op == '~':
            return Var(self.terms[0].vclass, self.terms[0].name, self.terms[0].index, self.terms[0].type)
        if self.op == '&':
            return Term('|', [term.negate() for term in self.terms])
        if self.op == '|':
            return Term('&', [term.negate() for term in self.terms])
        if self.op == '=':
            return Term('~=', [self.terms[0], self.terms[1]])
        if self.op == '~=':
            return Term('=', [self.terms[0], self.terms[1]])
        if self.op == '>':
            return Term('>=', [self.terms[0].minus(), self.terms[1].minus()])
        if self.op == '>=':
            return Term('>', [self.terms[0].minus(), self.terms[1].minus()])
        pass # give an error message

    def minus(self):
        if self.op == '-':
            return Var(self.terms[0].vclass, self.terms[0].name, self.terms[0].index, self.terms[0].type)
        if self.op == '+':
            return Term('+', [term.minus() for term in self.terms])
        pass # give an error message

    def normalize(self):
        flat = self.flatten()
        if flat.op == '+':
            simp_terms = sorted([term.normalize() for term in flat.terms])
            for i in range(len(flat.terms)):
                if flat.terms[i] == Const(0) or flat.terms[i] == Term('-', [Const(0)]):
                    simp_terms.remove(flat.terms[i])
                elif flat.terms[i].minus() in simp_terms:
                    simp_terms.remove(flat.terms[i])
                    simp_terms.remove(flat.terms[i].minus())
            if len(simp_terms) == 1:
                return simp_terms[0]
            return Term(flat.op, simp_terms) # change to var if necessary
        if flat.op == '=' or flat.op == '~=' or flat.op == '>' or flat.op == '>=':
            lterm = flat.terms[0]
            rterm = flat.terms[1]
            if (type(lterm) != Term or lterm.op == '+') and (type(rterm) != Term or rterm.op == '+'):
                if type(lterm) == Const or type(lterm) == Var:
                    lterm = Term('+', [lterm, rterm.minus()])
                elif type(lterm) == Term:
                    lterm.terms.append(rterm.minus())
                lterm = lterm.flatten().normalize()
                return Term(flat.op, [lterm, Const(0)])
        if flat.op in comm_ops:
            return Term(flat.op, sorted([term.normalize() for term in flat.terms]))
        return Term(flat.op, [term.normalize() for term in flat.terms])
     '''
