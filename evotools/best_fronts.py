from pathlib import Path
from contextlib import suppress

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from evotools import ea_utils

from evotools import config
from evotools.pictures import algos, algos_order
from evotools.serialization import RunResult


PLOTS_DIR = Path('plots')
RESULTS_DIR = Path('pareto_results')

metrics_name_long = "distance_from_pareto"

algo_names = [algos[a][0] for a in algos_order]


def plot_problem_front(original_front, multimodal=False, scatter=False):
    f = plt.figure(num=None, facecolor='w', edgecolor='k', figsize=(15, 7))
    ax = Axes3D(f) if len(original_front[0]) > 2 else plt.subplot(111)
    plt.tight_layout()
    plt.xlabel('1st objective', fontsize=25)
    plt.ylabel("2nd objective", fontsize=30)

    plt.tick_params(axis='both', labelsize=25)

    plt.axhline(linestyle='--', lw=0.9, c='#7F7F7F')
    plt.axvline(linestyle='--', lw=0.9, c='#7F7F7F')

    if len(original_front[0]) == 2:
        plt.margins(y=.1, x=.1)

    if multimodal:
        subfronts = ea_utils.split_front(original_front, 0.05)
        for front in subfronts:
            plot_front(ax, front, scatter)
    else:
        plot_front(ax, original_front, scatter)

    return ax, f


def plot_front(f, series, scatter=False):
    x = [x[0] for x in series]
    y = [x[1] for x in series]

    if len(series[0]) > 2:
        z = [x[2] for x in series]
        f.azim = 60
        f.scatter(x, y, z, c='0.6', s=60, zorder=1)
    f.plot(x, y, c='0.6', lw=6, zorder=1)


def plot_results(f, best_result, best_result_name):
    name, _, markers, color = algos[best_result_name]

    res_x = [x[0] for x in best_result.fitnesses]
    res_y = [x[1] for x in best_result.fitnesses]


    if len(best_result.fitnesses[0]) > 2:
        res_z = [x[2] for x in best_result.fitnesses]
        f.scatter(res_x, res_y, res_z, marker=markers, s=60, color=color, label=name, zorder=2)
    else:
        f.scatter(res_x, res_y, marker=markers, s=60, color=color, label=name, zorder=2)
    # f.scatter(res_x, res_y, marker=markers, s=60, edgecolors=color, facecolors='none', label=name, zorder=2)


def save_plot(ax, f, d_problem):
    box = ax.get_position()
    # ax.set_position([box.x0, box.y0, box.width * 0.80, box.height])
    handles, labels = ax.get_legend_handles_labels()

    handle_d = dict(zip(labels, handles))
    handles_order = [handle_d[l] for l in algo_names if l in handle_d]

    # plt.legend(handles_order, algo_names, loc='center left', bbox_to_anchor=(1, 0.5), prop={'size': 20}, frameon=False)

    path = Path(PLOTS_DIR) / RESULTS_DIR / '{}.pdf'.format(d_problem.name.replace('emoa', 'moea'))
    with suppress(FileExistsError):
        path.parent.mkdir(parents=True)

    plt.savefig(str(path))
    plt.close(f)


def main(*args, **kwargs):
    for problem_name, problem_mod, algorithms in RunResult.each_result(config.RESULTS_DIR):
        original_front = problem_mod.pareto_front
        ax, f = plot_problem_front(original_front, multimodal=problem_name == 'ZDT3')

        for algo_name, budgets in algorithms:
            best_result, best_result_name, best_result_metric = None, None, None
            """:type: RunResultBudget """

            for result in budgets:
                # print(result)
                for metrics_name, _, precomp in result["analysis"]:
                    if metrics_name == "igd":
                        precomp = [x() for x in precomp]
                        for runresbud, metric_val in zip(result["results"], precomp):
                            print(problem_name, algo_name, result["budget"], metrics_name, runresbud, metric_val)

                            if best_result_metric is None or metric_val < best_result_metric:
                                best_result, best_result_name, best_result_metric = runresbud, algo_name, metric_val

            plot_results(ax, best_result, best_result_name)
        save_plot(ax, f, problem_mod)


