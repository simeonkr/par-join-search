from terms import Const, Var, Term
from loop import Loop
from rules import *
from search import JoinSearchProblem
from parser import parse


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


mts = Loop([parse('0')], [parse('max(0,(s1+a0))')])
mts_invars = [parse('(s1>=0)')]
mts_invar_rules = generate_max_invar_rules(mts_invars)
mts_jsp = JoinSearchProblem(mts, max_sum_rules + mts_invar_rules, mts_invars)


mss = Loop([parse('0'), parse('0')],
           [parse('max(a0,(s1+a0))'),
            parse('max(s2,max(a0,(s1+a0)))')])
mss_invars = [parse('(s1>=0)'),
              parse('(s2>=0)'),
              parse('(s2>=s1)')]
mss_invar_rules = generate_max_invar_rules(mss_invars)
mss_jsp = JoinSearchProblem(mss, max_sum_rules + mss_invar_rules, mss_invars)


mbo = Loop([parse('0'), parse('0')],
           [parse('IC(a0,(s1+1),0)'),
            parse('max(s2,IC(a0,(s1+1),0))')])
mbo_invars = [parse('(s1>=0)'),
              parse('(s2>=0)'),
              parse('(s2>=s1)'),
              parse('(1>=0)'),
              parse('((s1+1)>=s1)')] # TODO: have a rule that covers cases like last two
mbo_invar_rules = generate_max_invar_rules(mbo_invars)
mbo_jsp = JoinSearchProblem(mbo, cond_max_rules + mbo_invar_rules, mbo_invars)