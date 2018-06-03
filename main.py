from sys import argv, exit, stdin
from signal import signal, SIGINT, SIGALRM, alarm

from defns import *
from search import *
from loop import *
from join import *
from rules import *
from config import P_STATS

mts_jsp = JoinSearchProblem(mts, max_sum_rules + mts_invar_rules, mts_invars)
mss_jsp = JoinSearchProblem(mss, max_sum_rules + mss_invar_rules, mss_invars)
mbo_jsp = JoinSearchProblem(mbo, cond_max_rules + mbo_invar_rules, mbo_invars)

jsp = globals()['%s_jsp' % argv[2]]

if argv[1] == 'search':
    signal(SIGINT, lambda sig, frame: [jsp.stats.print_summary(), exit(0)])
    join = jsp.search()

if argv[1] == 'timed':
    signal(SIGALRM, lambda sig, frame: [jsp.stats.print_summary(), exit(0)])
    alarm(int(argv[3]))
    join = jsp.search()

if argv[1] == 'benchmark':
    signal(SIGINT, lambda sig, frame: [jsp.stats.print_benchmark_summary(),
                                       exit(0)])
    with open(argv[3]) as seq_file:
        for line in seq_file:
            term = line.split()[0]
            jsp.benchmark_sequence.append(term)
    join = jsp.search()
else:
    if join is not None:
        print("\n### Succesfully found and verified a join ###")
        print(join)
    else:
        print("\n### Rule sequence did not result in success ###")

if P_STATS:
    if argv[1] != 'benchmark':
        jsp.stats.print_summary()
    else:
        jsp.stats.print_benchmark_summary()

