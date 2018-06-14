from itertools import *


def all_injective(xs, ys):
    out = []
    for x in xs:
        for y in ys + [None]:
            if len(xs) == 1:
                out.append([(x,y)])
            else:
                for tuples in all_injective([x_ for x_ in xs if x_ != x],
                                            [y_ for y_ in ys if y_ != y]):
                    out.append([(x,y)] + tuples)
    return out

    
def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


# TODO: wrap around iterables instead of lists
def loopthru(lst, i_mode, msg):
    if not i_mode:
        for i in range(len(lst)):
            yield (i, lst[i])
    else:
        if len(lst) == 0:
            return
        print('\nInteractive mode --', msg)
        sorted_lst = sorted(lst)
        if len(lst) == 1:
            print('Automatically selecting sole choice: %s\n' % lst[0])
            choice = 0
        else:
            for i in range(len(lst)):
                print('%-3s %s' % ('%d.' % (i + 1), sorted_lst[i]))
            choice = int(input('Select [%d - %d]: ' % (1, len(lst)))) - 1
        yield (choice, sorted_lst[choice])


def vprint(msg_type, *msg):
    if msg_type:
        print(*msg)
