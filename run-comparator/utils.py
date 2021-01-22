import os
from base64 import b64decode
from collections import defaultdict
from io import StringIO
from os import listdir
from os.path import isfile, join

import numpy as np
from trectools import TrecRun, fusion


def fuse_runs(run1, run2):
    # https://dl.acm.org/doi/10.1145/1571941.1572114
    r1 = TrecRun(f"runs/{run1}")
    r2 = TrecRun(f"runs/{run2}")

    # Perform reciprocal rank fusion.
    fused_run = fusion.reciprocal_rank_fusion([r1, r2], max_docs=100)

    # Clear names.
    name1 = run1.replace(".txt", "")
    name2 = run2.replace(".txt", "")

    # Save fused file to disk.
    fused_run.print_subset(
        f"runs/fuse_{name1}_{name2}.txt", topics=fused_run.topics()
    )


def make_folder(name):
    if not os.path.exists(name):
        os.makedirs(name)


def files_in_folder(mypath):
    make_folder(mypath)
    return [
        f for f in listdir(mypath) if isfile(join(mypath, f)) and not f.startswith(".")
    ]


def write_to_file(list_of_contents, list_of_names):
    for contents, name in zip(list_of_contents, list_of_names):
        # decode input
        content_type, content_string = contents.split(",")
        decoded = b64decode(content_string)
        content = StringIO(decoded.decode("utf-8"))

        # write content to file
        f = open(f"runs/{name}", "w")
        f.write(content.read())
        f.close()
    return True


def read_qrels(mypath):
    # 886 0 00183d98-741b-11e5-8248-98e0f5a2e830 0
    relevance_dict = defaultdict(dict)  # {topic: {docid: relevance, }}
    with open(mypath) as f:
        content = f.readlines()
        for line in content:
            row = line.split()
            relevance_dict[row[0]][row[2]] = int(row[3])
    return relevance_dict


def read_run(mypath):
    # 886 Q0 39fff39a71e2e8e0aeaf1666f7d78697 1 1.0 run1
    run = defaultdict(list)  # {topic: {docid: relevance, }}
    with open(mypath) as f:
        content = f.readlines()
        for line in content:
            row = line.split()
            run[row[0]].append(row[2])
    return run


def find_relevance(docid, qrels):
    if docid in qrels.keys():
        return qrels[docid]
    else:
        return 0.0


def mark_new(docid, docids):
    if docid in docids.values:
        return "grey"
    else:
        return "green"


def mark_new_text(docid, docids):
    if docid in docids.values:
        return docid
    else:
        return docid + " <b>(new)</b>"


def mark_current_runs(base, alt, selected):
    if selected == base:
        return "rgba(99, 110, 250, 0.7)"
    if selected == alt:
        return "rgba(239, 85, 59, 0.7)"
    else:
        return "white"


def new_percentage(run1, run2, n):
    # number of new docids in run2:
    new = []
    for topic in run2:
        n_new = np.sum([1 for docid in run2[topic][:n] if docid not in run1[topic][:n]])
        new.append((100 / n) * n_new)
    return np.mean(new)
