#!/usr/bin/env python3
"""EvoGIL helper.

Usage:
  evogil.py -h | --help
  evogil.py list
  evogil.py run budget <budget> [options]
  evogil.py run time [(--timeout | -t) <timeout>] [(--step | -s) <step>] [options]
  evogil.py (stats | statistics) [options]
  evogil.py rank
  evogil.py rank_details
  evogil.py table
  evogil.py summary
  evogil.py pictures [options]
  evogil.py pictures_summary [options]
  evogil.py best_fronts [options]
  evogil.py violin [options]

Commands:
  run
    Performs benchmarks. Subcommands:
        budget
            Run with budget constraints. Param: budget(s), list of integers separated by comma.
        time
            Run with timeout constraints. Params: timeout and/or step measured in seconds.
  summary
    Returns number of results for each tuple: algorithm, problem, budget.
  stats
    Generates statistics from benchmarks' results.
  rank
    Generates report with algorithms ranking.
  pictures
    Some pictures?
  violin
    Plots violin plots?

Options:
  -a <algo_name>, --algo <algo_name>       
        Only for selected algorithms(s) separated by comma. You can combine
        meta-algorithms with others by joining them with '+', eg.
            HGS+IBEA
            IMGA+SPEA2
            HGS+IMGS+HGS+IMGA+IMGA+IMGA+SPEA2 (this should work as well)
        Available algorithms (list may be out-of-date):
            NSGAII
            SPEA2
            IBEA
        Available meta-algorithms (list may be out-of-date):
            HGS
            IMGA
  -p <problem_name>, --problem <problem_name>
        Only for selected problem(s) separated by comma.
        Available problems (list may be out-of-date):
            ZDT1
            ZDT2
            ZDT3
            ZDT4
            ZDT6
            ackley
            kursawe
  -b <bootstrap-iter>, --bootstrap <bootstrap-iter>
        Bootstrap iterations.
        [default: 10000]
  -j <jobs>
        Number of processes to spawn.
        [default: 4]
  -N <iterations>
        Repeat N times.
        [default: 1]
  --renice <increment>
        Renice workers. Works on UNIX & derivatives.
  -d <results_dir>, --dir <results_dir>
        Directory where simulation results will be stored. If not specified, serialization.RESULTS_DIR is set.
  -o <plots_dir>
        Directory where generated plots will be stored. If not specified, pictures.PLOTS_DIR is set.
  
Pictures Summary Options:
  --selected <algo_name>
        Select and highlight specified algorithms on plots.
        [default: HGS+SPEA2,HGS+NSGAII,HGS+NSGAIII,HGS+IBEA,HGS+OMOPSO,HGS+SMSEMOA,HGS+JGBL,HGS+NSLS]
"""
import logging
import time

from docopt import docopt

import plots.best_fronts
import plots.pictures
import plots.violin
import simulation.run_parallel
import statistic.ranking
import statistic.stats
import statistic.summary
from plots import pictures
from simulation import run_config, log_helper, factory, serialization
from simulation.timing import system_time, log_time


# noinspection PyUnusedLocal
def all_algos_problems(*args, **kwargs):
    print("MOEAs:")
    for algo in run_config.algorithms:
        print("   ", algo)
    print("Problems:")
    for problem in run_config.problems:
        print("   ", problem)


def main_worker():
    logger = logging.getLogger(__name__)
    logger.debug("Starting the evogil. Parsing arguments.")
    with log_time(system_time, logger, "Parsing done in {time_res}s"):
        argv = docopt(__doc__, version="EvoGIL 3.0")
    logger.debug("Parsing result: %s", argv)

    run_dict = {
        "run": simulation.run_parallel.run_parallel,
        "statistics": statistic.stats.statistics,
        "stats": statistic.stats.statistics,
        "rank": statistic.ranking.rank,
        "table": statistic.ranking.table_rank,
        "rank_details": statistic.ranking.detailed_rank,
        "pictures": plots.pictures.pictures_time,
        "pictures_summary": plots.pictures.pictures_summary,
        "best_fronts": plots.best_fronts.best_fronts,
        "violin": plots.violin.violin,
        "summary": statistic.summary.analyse_results,
        "list": all_algos_problems,
    }
    set_default_options(argv)

    for k, v in run_dict.items():
        logger.debug("run_dict: k,v = %s,%s", k, v)
        if argv[k]:
            logger.debug("run_dict match. argv[k]=%s", argv[k])
            v(argv)
            break


def set_default_options(argv):
    if not argv["--dir"]:
        argv["--dir"] = serialization.RESULTS_DIR
    if not argv["-o"]:
        argv["-o"] = pictures.PLOTS_DIR


if __name__ == "__main__":
    log_helper.init()
    logger = logging.getLogger(__name__)

    t = time.time()
    main_worker()
    logger.debug("Execution time: " + str(time.time() - t))
