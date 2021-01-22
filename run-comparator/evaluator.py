import os

import pandas as pd


def load_metrics(file):
    # from anserini project.
    metrics = {}
    with open(file, "r") as f:
        for line in f:
            metric, qid, score = line.split("\t")
            metric = metric.strip()
            qid = qid.strip()
            score = score.strip()
            if qid == "all":
                continue
            if metric not in metrics:
                metrics[metric] = {}
            metrics[metric][qid] = float(score)

    return metrics


def trec_eval(metric, qrels, run):
    # TREC eval for evaluation.
    os.system(
        "./trec_eval/trec_eval -q -M1000 -m "
        f"{metric[:8]} {qrels} runs/{run} > .{run}"
    )

    # Store results in dictionary & clean up.
    run_metrics = load_metrics(f".{run}")
    os.remove(f".{run}")

    # Store results in DataFrame.
    run_metrics_df = pd.DataFrame.from_dict(
        run_metrics[metric], orient="index", columns=[run]
    )

    return run_metrics_df
