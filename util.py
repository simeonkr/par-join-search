from itertools import *
import heapq


class PriorityQueue:

    def __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def is_empty(self):
        return len(self.heap) == 0

    def update(self, item, priority):
        for index, (p, c, i) in enumerate(self.heap):
            if i == item:
                if p <= priority:
                    break
                del self.heap[index]
                self.heap.append((priority, c, item))
                heapq.heapify(self.heap)
                break
        else:
            self.push(item, priority)


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
