from terms import *
from lark import Lark, InlineTransformer


term_grammar = """
    !const: INT | "True" | "False"
    !var: LETTER INT | "sr" INT
    !op: {}
    term: const | var | prefix_term | infix_term
    prefix_term: op "(" term (("," | ", ") term)* ")"
    infix_term: "(" term (op term)* ")"

    %import common.INT
    %import common.LETTER
""".format(' | '.join(['"%s"' % op for op in ops]))


class TermTransformer(InlineTransformer):

    def const(self, value):
        if value.value == 'True' or value.value == 'False':
            return Const(value.value == 'True')
        else:
            return Const(int(value.value))

    def var(self, name, index):
        var_name_to_vclass = {"s" : "SV", "sr" : "RSV"}
        return Var(var_name_to_vclass[name] if name in var_name_to_vclass else 'IV',
                   name.value[0], int(index.value))

    def op(self, op):
        return op.value

    def prefix_term(self, op, *args):
        return Term(op, list(args))

    def infix_term(self, *args):
        op = args[1]
        args = [arg for arg in args if arg != op]
        return Term(op, list(args))

    def term(self, term):
        return term


def infer_var_types(term):
    if type(term) == Term:
        for i in range(len(term.terms)):
            subterm = term.terms[i]
            infer_var_types(subterm)
            if type(subterm) == Var:
                subterm.type = term_types[term.op].get_arg_type(i)


def parse(str):
    tree = Lark(term_grammar, start='term').parse(str)
    term = TermTransformer().transform(tree)
    infer_var_types(term)
    return term
