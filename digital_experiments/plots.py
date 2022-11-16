import base64
import io

import imageio.v2 as imageio
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import HTML

from .core import all_experiments_matching


def get_blocks(arr):
    blocks = []
    start_idx = 0
    for idx in range(len(arr) - 1):
        a, b = arr[idx], arr[idx + 1]
        if a != b:
            blocks.append((arr[idx], (start_idx, idx)))
            start_idx = idx + 1
    blocks.append((arr[-1], (start_idx, len(arr) - 1)))
    return blocks


_colours = {
    "manual": "k",
    "random-search": "b",
    "bayesian-optimization": "r",
}


def track_minimization(root, loss):
    df, experiments = all_experiments_matching(root)
    results = [loss(e.result) for e in experiments]

    plt.plot(df.experiment_number + 1, results, "-k+", alpha=0.5)
    contexts = [e.metadata["_context"] for e in experiments]
    blocks = get_blocks(contexts)
    in_legend = {}
    for context, (start, end) in blocks:
        if context not in in_legend:
            in_legend[context] = True
            label = context.replace("-", " ").title()
        else:
            label = None

        plt.axvspan(
            start + 0.5,
            end + 1.5,
            alpha=0.2,
            label=label,
            color=_colours[context],
            linewidth=0,
        )
    plt.xlim(0.5, len(results) + 0.5)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=3)
    plt.plot(
        df.experiment_number + 1,
        pd.Series(results).cummin(),
        "-ok",
        markersize=4,
        label="Best So Far",
    )
    plt.xlabel("Iteration")


def legend_outside(ax):
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))


def track_trials(x, y, root, callback=None, **kwargs):
    df, experiments = all_experiments_matching(root)
    df["contexts"] = [e.metadata["_context"] for e in experiments]
    df["colors"] = df["contexts"].map(_colours)

    def _plot(i):
        plt.scatter(
            df[x][:i], df[y][:i], c=df.colors[:i], s=20, linewidths=0, alpha=0.5
        )
        for c in _colours:
            plt.scatter([], [], c=_colours[c], label=c.replace("-", " ").title())
        plt.xlabel(x)
        plt.ylabel(y)
        if callback is not None:
            callback(i)
        legend_outside(plt.gca())

    return gif(_plot, range(len(df) + 1), **kwargs)


def gif(plot_func, frames, name="mygif.gif", **kwargs):
    with imageio.get_writer(name, mode="I", **kwargs) as writer:
        for i in frames:
            plot_func(i)

            tmp_file = io.BytesIO()
            plt.savefig(tmp_file, bbox_inches="tight")
            plt.clf()

            tmp_file.seek(0)
            image = imageio.imread(tmp_file)
            writer.append_data(image)

    with open(name, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return HTML(f'<img src="data:image/gif;base64,{b64}" width=480px/>')
