# coding=utf-8
from datetime import datetime
import random
import time
import math
import itertools




def gen_population(count: 'Int', dims: 'Int') -> '[[Float]]':
    return [[random.uniform(from_range, to_range) for from_range, to_range in dims]
            for _ in range(count)]


def condition_count(cnt=100):
    for r in range(cnt):
        yield True


def condition_time(t=60.0):
    start = time.time()
    while (time.time() - start) < t:
        yield True


def euclid_sqr_distance(xs, ys):
    return sum((x - y) ** 2 for x, y in zip(xs, ys))


def euclid_distance(xs, ys):
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) == 0:
        return 9999999
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(xs, ys)))


def dominates(xs, ys) -> 'Bool':
    """
    :param xs: Wektor wyników A.
    :param ys: Wektor wyników B.
    :return: Zwraca True <=> A dominuje B.
    """
    return domination_cmp(xs, ys) > 0


def domination_cmp(xs, ys) -> 'Int':
    """
    :param xs: Wektor wyników A.
    :param ys: Wektor wyników B.
    :return: Zwraca 1 gdy A dominuje B, -1 gdy B dominuje A oraz 0 wpp.
    """
    direction = 0
    for i, j in zip(xs, ys):
        ndir = (-1, 0, 1)[(i <= j) + (i < j)]  # hacky!
        if ndir != 0:
            if direction != 0 and ndir != direction:
                return 0
            direction = ndir
    return direction


def paretofront_layers(lst, fitfun_res) -> '[[Individual]]':
    """
    :param lst: Lista indywiduów.
    :param fitfun_res: Funkcja zwracająca wynik funkcji fitness indywiduów.
    :return: Lista list [A1, A2, ...] taka, że i<j gddy wszystkie elementy Ai dominują wszystkie z Aj.
    """

    lst_f_doms = [[indiv, fitfun_res(indiv), 0] for indiv in lst]

    while len(lst_f_doms) > 0:
        for i, j in itertools.permutations(lst_f_doms, 2):
            if dominates(i[1], j[1]):
                j[2] += 1
        yield [ind
               for ind, f_ind, domtd in lst_f_doms
               if domtd == 0]
        lst_f_doms = [[ind, f_ind, 0]
                      for ind, f_ind, domtd in lst_f_doms
                      if domtd > 0]

        # No dobra, ten algo jest słaby: jego czas działania to O(k d n^2) dla k-ilości "warstw", n-ilości indywiduów.
        # Da się lepiej, ale ten margines jest zbyt mały, by... AW FCUK IT!
        #
        # Dla d=1 (jednowymiarowego przypadku): po prostu minimum.
        # Czas: O(n)
        # Dla d=2:
        #   1. A_1, ..., A_n posortuj w kolejności leksykograficznej (tj. [1,2] < [1,3] < [2,0] < [2,2] )
        #   2. i=1
        #   3. A_i należy do frontu Pareto
        #   4. znajdź j>i takie, że A_j[2] < A_i[2] (tj. pierwszy następny, którego wartość na indeksie 2 jest lepsza)
        #   5. jeśli j istnieje: i=j, GOTO 3
        #   Czas: O(n log n)
        # Dla d=3,4,5...
        #   1. A_1, ..., A_n posortuj w kolejności leksykograficznej
        #   2. Wybierz wszystkie wierzchołki, których pierwsza współrzędna jest najmniejsza
        #   3. Rekurencyjnie wywołaj się dla tych wierzchołków (przypadek d-1)
        #   4. Wynik dodaj do frontu pareto.
        #   5. Dodaj informację o dominacji do d-wymiarowego drzewa przedziałowego   <-- koszt budowy drzewa: O(n (log n)^d)
        #   6. Znajdź następny, niezdominowany wierzchołek (niezdominowane wierzchołki), GOTO 3
        #   Czas: O(n (log n)^d) przy założeniu, że k <= (log n)^(d-1) o ile krok 5, tj. jest (d n / log n)
        #     czyli DUŻO ale nie na tyle, by mi się chciało to pisać.


def distance_from_pareto(solution, pareto):
    return sum([min([euclid_distance(x, y)
                     for y in pareto])
                for x in solution]) / len(solution)


def distribution(solution, sigma):
    return sum(len( y
                    for y in solution
                    if euclid_distance(x, y) > sigma
                   ) / (len(solution) - 1)
                for x in solution
              ) / len(solution)


def extent(solution):
    return math.sqrt(sum( max( math.fabs(x[i] - y[i])
                               for x, y
                               in itertools.product(solution, solution)
                              )
                          for i
                          in range( len(solution[0]) )
                        )
                    )


def weighted_choice(choices):
    # http://stackoverflow.com/a/3679747/547223
    choices = list(choices)
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w

    assert False, "Shouldn't get here"


def get_current_time():
    return datetime.today().strftime("%Y-%m-%d.%H%M%S.%f")


def split_front(pareto_front, epsilon):
    groups = []
    group = []
    prev_x = 0

    for x, y in pareto_front:
        if x - prev_x > epsilon:
            groups.append(group)
            group = [(x, y)]
        else:
            group.append((x, y))
        prev_x = x

    if groups[-1] != group:
        groups.append(group)

    return groups
