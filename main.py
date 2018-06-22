from sys import argv, exit, stdin
from signal import signal, SIGINT, SIGALRM, alarm

from defns import *
from config import P_STATS
from parser import parse
from search import JoinSearchProblem


def make_jsp(filename):
    state_inits = []
    state_terms = []
    invars = []
    rules = []
    blank_lines = 0
    with open(filename, 'r') as file:
        for line in file.read().splitlines():
            if not line:
                blank_lines += 1
            else:
                if blank_lines == 0: # read in ex. definition
                    state_init, state_term = line.split('; ')
                    state_inits.append(parse(state_init))
                    state_terms.append(parse(state_term))
                elif blank_lines == 1: # read in rules
                    rules.extend(globals()[line])
                elif blank_lines == 2: # read in invars
                    invars.append(parse(line))
    rules.extend(generate_max_invar_rules(invars))
    return JoinSearchProblem(Loop(state_inits, state_terms), rules, invars)


def print_join(join):
    for state_init, state_term in zip(join.loop.state_init, join.loop.state_terms):
        print(', '.join([str(state_init), str(state_term)]))
    print()
    print(join.term)


if __name__ == '__main__':

    jsp = make_jsp('examples/%s.txt' % argv[2])

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
        with open('examples/' + argv[3]) as seq_file:
            for line in seq_file:
                term = line.split()[0]
                jsp.benchmark_sequence.append(term)
        join = jsp.search()
    else:
        if join is not None:
            print("\n### Succesfully found and verified a join ###")
            print()
            print_join(join)
        else:
            print("\n### Rule sequence did not result in success ###")

    if P_STATS:
        if argv[1] != 'benchmark':
            jsp.stats.print_summary()
        else:
            jsp.stats.print_benchmark_summary()

