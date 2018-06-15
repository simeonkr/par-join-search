from rules import *
from terms import *


inner_term = None


def state_depth_diff_feature(state, new_term, rule_num):
    return (max_state_depth(new_term) - max_state_depth(state.term)) * max_state_depth(new_term)


def state_count_diff_feature(state, new_term, rule_num):
    return (state_count(new_term) - state_count(state.term)) * state_count(new_term)


def depth_diff_feature(state, new_term, rule_num):
    return (max_depth(state.term) - max_depth(new_term)) * max_depth(state.term)


def term_length_diff_feature(state, new_term, rule_num):
    return max(0, new_term.length() - state.term.length())


def sq_branching_factor_diff_feature(state, new_term, rule_num):
    return int(sq_branching_factor(new_term) - sq_branching_factor(state.term))


def num_duplicates_feature(state, new_term, rule_num):
    return get_duplicates(new_term)


def rule_history_feature(state, new_term, rule_num):
    return sum([(int(rule_num == rn)) ** 2 for rn in state.get_rule_history()])


def const_only_terms_diff_feature(state, new_term, rule_num):
    return num_const_only_terms(new_term)


def term_similarity_diff_feature(state, new_term, rule_num, init_raw_term):
    max_new_term_similarity = 0
    max_state_term_similarity = 0
    for uterm in all_unflatten(new_term):
        max_new_term_similarity = max(max_new_term_similarity,
                                      term_inner_similarity(uterm, init_raw_term))
    for uterm in all_unflatten(state.term):
        max_state_term_similarity = max(max_state_term_similarity,
                                      term_inner_similarity(uterm, init_raw_term))
    return (1 - max_new_term_similarity) - (1 - max_state_term_similarity)


def state_depth(term, depth=0):
    if type(term) == Const:
        return 0
    if type(term) == Var:
        return depth if term.vclass == "SV" else 0
    return sum([state_depth(subterm, depth + 1) for
                subterm in term.terms])


def state_count(term, count=0):
    if type(term) == Const:
        return 0
    if type(term) == Var:
        return count+1 if term.vclass == "SV" else count
    return sum([state_count(subterm, count) for
                subterm in term.terms])


def _sq_sum_of_lens(term):
    if type(term) == Const or type(term) == Var:
        return 0
    return len(term.terms) + sum([_sq_sum_of_lens(subterm) for
                                       subterm in term.terms])


def sq_branching_factor(term):
    return _sq_sum_of_lens(term) / term.length()


def max_state_depth(term, depth=0):
    if type(term) == Const:
        return 0
    if type(term) == Var:
        return depth if term.vclass == "SV" else 0
    return max([state_depth(subterm, depth + 1) for
                subterm in term.terms])


def max_depth(term, depth=0):
    if type(term) == Const or type(term) == Var:
        return depth
    return max([max_depth(subterm, depth + 1) for
                subterm in term.terms])


def num_const_only_terms(term):
    if type(term) == Const or type(term) == Var:
        return 0
    const_count = 0
    for subterm in term.terms:
        if type(subterm) == Const:
            const_count += 1
    if const_count == 1:
        const_count = 0
    return const_count + sum([num_const_only_terms(subterm) for
                             subterm in term.terms])


# What I'm thinking off seems just to be max_state_depth, w/o SV I think?
def max_length_subterm(term):
    if type(term) == Const:
        return 1
    if type(term) == Var:
        return 1
    return max(len(term.terms), max([max_length_subterm(t) for t in term.terms]))


def get_duplicates(term):
    if type(term) == Const or type(term) == Var:
        return 0
    return number_of_duplicates(term.terms) + sum([get_duplicates(subterm) for subterm in term.terms])


def number_of_duplicates(lst):
    l = lst[:]
    count = 0
    for x in lst:
        subcount = -1
        expcount = -1/2
        while x in l:
            l.remove(x)
            subcount += 1
            # TODO: punish Consts more
            expcount = 2*expcount + 1
        #count += max(0, subcount)
        count += int(expcount)
    return count


def get_diff(term, new_term):
    if type(term) == Const or type(term) == Const:
        return None
    if type(new_term) == Var or type(new_term) == Var:
        return None

    newsubterms = subterm.terms[:]
    changed = []
    for x in term.terms:
        if x in newsubterms:
            newsubterms.remove(x)
        else:
            changed.append(x)

    if len(newsubterms) == 0:
        return None
    elif len(newsubterms) == 1 and len(changed) == 0:
        return (None, newsubterms[0])
    else: # len(newsubterms) == 1 and len(changed) == 1: TODO o/w?
        assert len(newsubterms) == 1 and len(changed) == 1


def term_similarity(term1, term2):
    return 2 * term_similarity_score(term1, term2) / (term1.length() + term2.length())


def term_similarity_score(term1, term2):
    if type(term1) == Const or type(term1) == Var:
        if term1 == term2:
            return 1
        if type(term2) == Term and term1 in term2.terms:
            return 1 / len(term2.terms)
        return 0
    if type(term2) == Const or type(term2) == Var:
        return term_similarity_score(term2, term1)
    score = 0
    if term1.op == term2.op:
        score += 1
        for sub1, sub2 in zip(sorted(term1.terms), sorted(term2.terms)):
            score += term_similarity_score(sub1, sub2)
    return score


def term_inner_similarity(term, inner_term):
    subterms = term.terms if type(term) == Term else []
    return max([term_similarity(term, inner_term)] +
               [term_inner_similarity(subterm, inner_term) for subterm in subterms])