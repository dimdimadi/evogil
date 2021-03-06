import copy
import logging
import random
import numpy as np
import math

from algorithms.base.driver import Driver


class SMPSO(Driver):
    ETA = 0.0075
     

    def __init__(
        self,
        population,
        fitnesses,
        dims,
        mutation_eta,
        mutation_rate,
        crossover_eta,
        crossover_rate,
        mutation_perturbation=0.5,
        mutation_probability=0.05,
        trim_function=lambda x: x,
        fitness_archive=None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.c1_min = 1.5
        self.c1_max = 2.5
        self.c2_min = 1.5
        self.c2_max = 2.5
        self.r1_min = 0.0
        self.r1_max = 1.0
        self.r2_min = 0.0
        self.r2_max = 1.0

        self.fitnesses = fitnesses
        self.dims = dims
        self.individuals = [Individual(trim_function(x)) for x in population]
        self.mutation_probability = mutation_probability

        self.leaders_size = len(population)  # parameter?
        self.mutation_perturbation = mutation_perturbation
        self.crowding_selector = CrowdingTournament()

        self.trim_function = trim_function

        self.archive = Archive(self.ETA)
        self.leader_archive = LeaderArchive(self.leaders_size)
        self.fitness_archive = fitness_archive

        self.init()

       

    @property
    def population(self):
        return [x.value for x in self.individuals]

    @population.setter
    def population(self, pop):
        self.individuals = [Individual(x) for x in pop]

    def init_personal_best(self):
        for p in self.individuals:
            p.best_val = copy.deepcopy(p)

    def init(self):
        self.logger = logging.getLogger(__name__)
        self.cost = 0
        self.gen_no = 0
        self.cost += self.calculate_objectives()
        self.init_leaders()
        self.init_personal_best()
        self.leader_archive.crowding()

    def init_leaders(self):
        for p in self.individuals:
            if self.leader_archive.add(copy.deepcopy(p)):
                self.archive.add(copy.deepcopy(p))

    def finalized_population(self):
        return [x.value for x in self.archive]

    def step(self):
        # print("{}: {} : {}".format(gen_no, len(self.leader_archive.archive), len(self.archive.archive)))

        self.compute_speed()
        self.move()

        # dirty hack for unknown evolution length

        progress = min(1.0, self.cost / self.max_budget) if self.max_budget else None
        self.smpso_mutation(progress)

        for x in self.individuals:
            x.value = self.trim_function(x.value)

        self.cost += self.calculate_objectives()

        self.update_leaders()
        self.update_personal_best()

        self.leader_archive.crowding()

        self.logger.debug(
            "{}: {} : {}".format(
                self.gen_no, len(self.leader_archive.archive), len(self.archive.archive)
            )
        )
        self.gen_no += 1

    def update_personal_best(self):
        for p in self.individuals:
            # print("new: {}, best: {}".format(p.objectives, p.best_val.objectives))
            if p.dominates(p.best_val):
                # print("new best: {}".format(p.objectives))
                p.best_val = copy.deepcopy(p)

    def update_leaders(self):
        for p in self.individuals:
            new_ind = copy.deepcopy(p)
            if self.leader_archive.add(new_ind):
                self.archive.add(copy.deepcopy(p))

    def calculate_objectives(self):
        objectives_cost = 0
        for p in self.individuals:
            if (self.fitness_archive is not None) and (p.value in self.fitness_archive):
                p.objectives = self.fitness_archive[p.value]
                objectives_cost = 0
            else:
                p.objectives = [o(p.value) for o in self.fitnesses]
                objectives_cost = len(self.individuals)
        return objectives_cost

    def move(self):
        for p in self.individuals:
            for i in range(len(self.dims)):
                new_x = p.value[i] + p.speed[i]
                bounded_x = max(new_x, self.dims[i][0])
                bounded_x = min(bounded_x, self.dims[i][1])

                if bounded_x != new_x:
                    p.speed[i] *= -1

                p.value[i] = bounded_x


    def compute_speed(self):
        for p in self.individuals:
            W = 0.1

            # Most of the Test Problems have the UpperBound and Lower Bound between 0 and 1, however this upperbound and lower bound should be tuned more for ZDT5 problem.
            upB = 1
            lowB = 0

            delta = (upB - lowB)/2

            best_global = (
                self.crowding_selector(self.leader_archive)
                if len(self.leader_archive.archive) > 1
                else self.leader_archive.archive[0]
            )
            r1 = round(random.uniform(self.r1_min, self.r1_max), 1)
            r2 = round(random.uniform(self.r2_min, self.r2_max), 1)
            c1 = round(random.uniform(self.c1_min, self.c1_max), 1)
            c2 = round(random.uniform(self.c2_min, self.c2_max), 1)
            rho = c1 + c2

            if rho <= 4:
                constriction_coeficient = 1.0
            else:
                constriction_coeficient = 2.0 / (2.0 - rho - math.sqrt(math.pow(rho, 2.0) - 4.0 * rho))



            for j in range(len(self.dims)):
                p.speed[j] = W * p.speed[j] + c1 * r1 * (p.best_val.value[j] - p.value[j]) + c2 * r2 * (best_global.value[j] - p.value[j])
                p.speed[j] = constriction_coeficient * p.speed[j]

                if p.speed[j] > delta:
                    p.speed[j] = delta
                elif p.speed[j] < delta:
                    p.speed[j] = -delta
                

                # #Check that the particles do not run out of the search space
                # p.value[j, p.value[j:] < lowB] = lowB[p.value[j,:] < lowB]
                # p.value[j, p.value[j:] > upB] = upB[p.value[j,:] > upB]
                # #Change the velocity direction 
                # p.speed[j, p.value[j,:] < lowB] = -p.speed[j,p.value[j,:] < lowB]
                # p.speed[j, p.value[j,:] > upB] = -p.speed[j,p.value[j,:] > upB]
                # #Constrain the velocity
                # p.speed[j, p.speed[j,:] > vmax] = vmax[p.speed[j,:] > vmax]
                # p.speed[j, p.speed[j,:] < -vmax] = vmax[p.speed[j,:] < -vmax]




    def smpso_mutation(self, evolution_progress):
        pop_len = len(self.individuals)
        pop_part = int(pop_len / 3)
        uniform_mutation = UniformMutation(
            self.mutation_probability, self.mutation_perturbation, self.dims
        )
        map(uniform_mutation, self.individuals[0:pop_part])

        if evolution_progress:
            non_uniform_mutation = NonUniformMutation(
                evolution_progress,
                self.mutation_probability,
                self.mutation_perturbation,
                self.dims,
            )
            map(non_uniform_mutation, self.individuals[pop_part : 2 * pop_part])


class Mutation(object):
    def __init__(self, mutation_probability, mutation_perturbation, dims):
        self.dims = dims
        self.mutation_perturbation = mutation_perturbation
        self.mutation_probability = mutation_probability

    def do_mutation(self, p, index):
        return 0

    def __call__(self, p):
        for i in range(len(self.dims)):
            if random.random() < self.mutation_probability:
                mutation = self.do_mutation(p, i)

                p.value[i] += mutation
                p.value[i] = max(p.value[i], self.dims[i][0])
                p.value[i] = min(p.value[i], self.dims[i][1])


class UniformMutation(Mutation):
    def __init__(self, mutation_probability, mutation_perturbation, dims):
        super().__init__(mutation_probability, mutation_perturbation, dims)

    def do_mutation(self, p, index):
        return (random.random() - 0.5) * self.mutation_perturbation


class NonUniformMutation(Mutation):
    def __init__(
        self, evolution_progress, mutation_probability, mutation_perturbation, dims
    ):
        super().__init__(mutation_probability, mutation_perturbation, dims)
        self.evolution_progress = evolution_progress

    def do_mutation(self, p, index):
        return (
            self.delta(self.dims[index][1] - p.value[index])
            if random.random() < 0.5
            else self.delta(self.dims[index][0] - p.value[index])
        )

    def delta(self, y):
        rand = random.random()
        prog = 1.0 - self.evolution_progress
        perturbation = prog ** self.mutation_perturbation
        return y * (1.0 - rand ** perturbation)


class CrowdingTournament:
    def __init__(self, tournament_size=2):
        self.tournament_size = tournament_size

    def __call__(self, pool):
        sub_pool = random.sample(pool.archive, self.tournament_size)
        return min(sub_pool, key=lambda x: x.crowd_val)


class Individual:
    def __init__(self, value):
        self.value = value
        self.best_val = None
        self.crowd_val = 0
        self.objectives = []
        self.reset_speed()

    def __deepcopy__(self, memo):
        dup = Individual(copy.deepcopy(self.value, memo))
        dup.best_val = copy.deepcopy(self.best_val, memo)
        dup.speed = copy.deepcopy(self.speed, memo)
        dup.crowd_val = self.crowd_val
        dup.objectives = copy.deepcopy(self.objectives, memo)
        return dup

    def dominates(self, p2, eta=0):
        at_least_one = False
        for i in range(len(self.objectives)):
            if p2.objectives[i] < self.objectives[i] / (1 + eta):
                return False
            elif p2.objectives[i] > self.objectives[i] / (1 + eta):
                at_least_one = True

        return at_least_one

    def reset_speed(self):
        self.speed = [0] * len(self.value)

    def equal_obj(self, p):
        for i in range(len(self.objectives)):
            if self.objectives[i] != p.objectives[i]:
                return False
        return True


class Archive(object):
    def __init__(self, eta=0.0):
        self.archive = []
        self.eta = eta

    def __iter__(self):
        return self.archive.__iter__()

    def add(self, p):

        for l in self.archive:
            if l.dominates(p, self.eta):
                return False
            elif p.dominates(l, self.eta):
                self.archive.remove(l)
            elif l.equal_obj(p):
                return False

        self.archive.append(p)
        return True


class LeaderArchive(Archive):
    def __init__(self, size):
        super().__init__()
        self.size = size

    def add(self, p):
        added = super().add(p)
        if added and len(self.archive) > self.size:
            self.prune()
        return added

    def prune(self):
        self.crowding()
        worst_res = max(self.archive, key=lambda x: x.crowd_val)
        self.archive.remove(worst_res)

    def crowding(self):
        for p in self.archive:
            p.crowd_val = 0

        obj_n = len(self.archive[0].objectives)

        archive_len = len(self.archive)
        for i in range(obj_n):
            self.archive.sort(key=lambda x: x.objectives[i])
            obj_min = self.archive[0].objectives[i]
            obj_max = self.archive[archive_len - 1].objectives[i]

            self.archive[0].crowd_val = float("inf")
            self.archive[archive_len - 1].crowd_val = float("inf")

            for j in range(1, archive_len - 1):
                if obj_max - obj_min > 0:
                    dist = (
                        self.archive[j].objectives[i]
                        - self.archive[j - 1].objectives[i]
                    )
                    dist /= obj_max - obj_min
                    self.archive[j].crowd_val += dist
                else:
                    self.archive[j].crowd_val = float("inf")
