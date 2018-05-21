from defns import *
from search import *
from loop import *
from join import *
from rules import *

mts_jsp = JoinSearchProblem(mts, max_sum_rules + mts_invar_rules, mts_invars)
mss_jsp = JoinSearchProblem(mss, max_sum_rules + mss_invar_rules, mss_invars)
mbo_jsp = JoinSearchProblem(mbo, cond_max_rules + mbo_invar_rules, mbo_invars)

from sys import argv
jsp = globals()['%s_jsp' % argv[2]]

if argv[1] == 'search':
    join = jsp.search()

if join is not None:
    print("\n### Succesfully found and verified a join ###")
    print(join)
else:
    print("\n### Rule sequence did not result in success ###")

