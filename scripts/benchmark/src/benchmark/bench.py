import pickle
import timeit

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from benchmark import BENCHMARKS

LIGHT_MODE = True

FONT_COLOR = "dimgrey" if LIGHT_MODE else "darkgray"

custom_params = {
    "text.color": FONT_COLOR,
    "axes.labelcolor": FONT_COLOR,
    "xtick.labelcolor": FONT_COLOR,
    "ytick.labelcolor": FONT_COLOR,
    "patch.edgecolor": "none",
}
sns.set_theme(style="whitegrid", font_scale=1.5, rc=custom_params)


def argsort(seq):
    return sorted(range(len(seq)), key=seq.__getitem__)


def plot_bench(results: list[tuple[float, str]], filename: str) -> None:
    times, labels = zip(*results)
    sorted_index = argsort(times)

    times = [times[i] for i in sorted_index]
    labels = [labels[i] for i in sorted_index]

    fig, ax = plt.subplots(figsize=(8, 2))

    sns.barplot(x=times, y=labels, ax=ax)
    ax.bar_label(ax.containers[0], [f" {1000 * t:.0f}ms" for t in times], fontsize=16)

    for patch in ax.patches:
        current_width = patch.get_height()
        diff = current_width - 0.7

        patch.set_height(0.7)
        patch.set_y(patch.get_y() + diff * 0.5)

    ax.set_xticks([0.0, 0.05, 0.10, 0.15])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda t, p: f"{1000 * t:.0f}ms"))

    sns.despine(left=True, bottom=True)
    plt.tight_layout()
    plt.savefig(f"{filename}.svg", transparent=True)
    plt.show()


def eps_search(
    poly, method, target: int, eps_range: tuple[float, float] = (0.0, 1.0)
) -> float:
    min, max = eps_range

    while True:
        eps = (min + max) / 2
        red_len = len(method(poly, eps))

        if eps == min or eps == max:
            raise ValueError("Failed to converge")

        if red_len == target:
            return eps
        elif red_len < target:
            max = eps
        else:
            min = eps


def verify_bench(poly, benches, target) -> bool:
    red_lengths = []
    for method, eps, label in benches:
        length = len(method(poly, eps))
        red_lengths.append(length)
        print(f"{label}: {length} / {len(poly)}")

    return all([length == target for length in red_lengths])


def benchmark(poly, method, eps, count=1) -> float:
    runner = lambda: method(poly, eps)
    return timeit.timeit(runner, number=count) / count


if __name__ == "__main__":
    with open("../../tests/data/sea/ionian_sea.pkl", "rb") as f:
        poly = pickle.load(f)
    target = 10570  # 90% reduction

    eps_vals = [eps_search(poly, method, target) for method, _ in BENCHMARKS]
    bench = [(method, eps, label) for (method, label), eps in zip(BENCHMARKS, eps_vals)]
    assert verify_bench(poly, bench, target)

    results = [(benchmark(poly, method, eps), label) for method, eps, label in bench]
    plot_bench(results, filename="bench")
