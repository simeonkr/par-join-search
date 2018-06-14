from terms import Const, Var, Term
from loop import Loop
from rules import *


s1 = Var("SV", "s", 1, int)
s2 = Var("SV", "s", 2, int)
a0 = Var("IV", "a", 0, int)
a1 = Var("IV", "a", 1, int)
a2 = Var("IV", "a", 2, int)
a3 = Var("IV", "a", 3, int)
a4 = Var("IV", "a", 4, int)
a0b = Var("IV", "a", 0, bool)
a1b = Var("IV", "a", 1, bool)
a2b = Var("IV", "a", 2, bool)
a3b = Var("IV", "a", 3, bool)
a4b = Var("IV", "a", 4, bool)


flattenRule = Rule(0, flatten)
unflattenRule = Rule(float('inf'), unflatten)
allUnflattenRule = Rule(float('inf'), all_unflatten)

zeroIntroduceRule = IdentIntroRule(40, '+', Const(0))
zeroElimRule = IdentElimRule(5, '+', Const(0))

andIntroduceRule = IdentIntroRule(40, '&', Const(True))
andElimRule = IdentElimRule(5, '&', Const(True))

orIntroduceRule = IdentIntroRule(40, '|', Const(False))
orElimRule = IdentElimRule(5, '|', Const(False))

maxDistRule = DistInRule(20, ['+'], ['max'])
maxDistRevRule = DistOutRule(1, ['+'], ['max'])
maxIntroduceRule = DupIntroRule(60, 'max')
maxElimRule = DupElimRule(5, 'max')

bCondDistRule = DistInRule(20, ['&', '|'], ['BC'], [1,2])
bCondDistRevRule = DistOutRule(1, ['&', '|'], ['BC'], [1,2])
iCondDistRule = DistInRule(20, ['+', 'max'], ['IC'], [1,2])
iCondDistRevRule = DistOutRule(1, ['+', 'max'], ['IC'], [1,2])


max_sum_rules = [maxDistRule, maxDistRevRule, maxIntroduceRule,
                 maxElimRule, zeroIntroduceRule, zeroElimRule]

cond_max_rules = max_sum_rules + [andIntroduceRule, andElimRule,
                                  iCondDistRule, iCondDistRevRule]


def generate_max_invar_rules(invars):
    rules = []
    for invar in invars:
        rules.append(MaxStrengthenRule(60, invar))
        rules.append(MaxWeakenRule(60, invar))
    return rules


mts = Loop([Const(0)], [Term("max", [Term("+", [s1, a0]), Const(0)])])
mts_invars = [Term('>=', [s1, Const(0)])]
mts_invar_rules = generate_max_invar_rules(mts_invars)

mss = Loop([Const(0), Const(0)],
           [Term("max", [Term("+", [s1, a0]), a0]),
            Term("max", [s2, Term("max", [Term("+", [s1, a0]), a0])])])
mss_invars = [Term('>=', [s1, Const(0)]),
              Term('>=', [s2, Const(0)]),
              Term('>=', [s2, s1])]
mss_invar_rules = generate_max_invar_rules(mss_invars)

mbo = Loop([Const(0), Const(0)],
           [Term("IC", [a0b, Term("+", [s1, Const(1)]), Const(0)]),
            Term("max", [s2, Term("IC", [a0b, Term("+", [s1, Const(1)]), Const(0)])])])
mbo_invars = [Term('>=', [s1, Const(0)]),
              Term('>=', [s2, Const(0)]),
              Term('>=', [s2, s1]),
              Term('>=', [Const(1), Const(0)]),
              Term('>=', [Term('+', [s1, Const(1)]), s1])] # TODO: have a rule that covers cases like last two
mbo_invar_rules = generate_max_invar_rules(mbo_invars)

"""mtspos = Loop([Const(0), Const(0)],
              [Term("IC",
                        [Term(">",
                                [ Term("+", [s1, a0]), Const(0) ]),
                         Term("+", [s1,a0]),
                         0 ])],
                 Term("IC",
                        [Term(">",
                                [Term("+", [s1, a0]), Const(0)]),
                         i,
                         s2]))"""
#mtsposinit  = IC(s1+a0 > 0, i, s2)
#mtsposfinal in string is IC( s1<IC(0+a0>0,0+a0,0),   IC(0+a0>0, i, 0), s2)
# i.e. IC( s1<max(0+a0, 0),   IC(0+a0>0, i, 0), s2)

mps = Loop([Const(0), Const(0)],
           [Term("+", [s1, a0]),
            Term("max", [s2, Term("+", [s1, a0])])])
mps_invars = [Term('>=', [s1, Const(0)]),
              Term('>=', [s2, Const(0)]),
              Term('>=', [s2, s1])]
mps_invar_rules = generate_max_invar_rules(mps_invars)
#mps init max(s2, s1+a0)
#mps goal max(s2L, s1L + s2R) i.e. max(s2, s1 + max(0, 0+a0))

"""bal = Loop([Const(0), Const(True)],
           [Term("+", [s1, Term("IC", [a0b, Const(1), Const(-1)])]),
           Term("&", [s2, Term(">=", [Term("+", [s1, Term("IC", [a0b, 1, -1])]), Const(0)])])])"""
# bal init: s2 & (s1 + IC(a0b, 1, -1) >= 0)
# bal goal: balL & countL + mincountR >= 0 (mincount is just minpresum i.e. min(mincount, count+a0))
# i.e. bal & count + min(0,0+a0)

oz = Loop([Const(True), Const(True)],
          [Term("&", [a0b, s1]),
           Term("&", [Term("|", [Term("~", [a0b]), Term("&", [a0b, s1])]), s2])])
oz_invars = [Term("=", [Term("&", [a0b, Term("~", [a0b])]), Const(True)])
            #
            ]
