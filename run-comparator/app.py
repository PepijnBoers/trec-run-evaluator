import logging

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from scipy.stats import ttest_rel

import layout
from evaluator import trec_eval
from utils import (files_in_folder, find_relevance, fuse_runs,
                   mark_current_runs, mark_new, mark_new_text, new_percentage,
                   read_qrels, read_run, write_to_file)

pd.options.plotting.backend = "plotly"

# temporary
qrels_dict = read_qrels("qrels/qrels.backgroundlinking19.txt")
pretty_metric = {"ndcg_cut_5": "NDCG@5", "ndcg_cut_10": "NDCG@10"}

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
style_block = {"display": "inline-block", "float": "left", "margin-right": 20}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Run Comparator"

app.layout = html.Div(
    [
        html.Div(
            [
                html.P(id="placeholder"),
                html.Div(
                    [html.H3("TREC Run Comparator", style={"text_align": "center"})],
                    style={
                        "text-align": "center",
                        "font-family": "courier,arial,helvetica",
                    },
                ),
                html.Div(
                    [
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Runs")]
                            ),
                            style={
                                "width": "100%",
                                "height": "60px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "text-align": "center",
                                "margin": "10px",
                            },
                            # Allow multiple files to be uploaded
                            multiple=True,
                        ),
                        html.Div(
                            id="output-data-upload",
                            style={"display": "flex", "justify-content": "center"},
                        ),
                    ],
                    style={"display": "flex", "justify-content": "center"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.P("base"),
                                dcc.Dropdown(
                                    id="dropdown-run-1",
                                    options=[
                                        {"label": file, "value": file}
                                        for file in files_in_folder("runs")
                                    ],
                                    value=files_in_folder("runs")[0],
                                    style={"width": 180},
                                ),
                            ],
                            style=style_block,
                        ),
                        html.Div(
                            [
                                html.P("alternative"),
                                dcc.Dropdown(
                                    id="dropdown-run-2",
                                    options=[
                                        {"label": file, "value": file}
                                        for file in files_in_folder("runs")
                                    ],
                                    value=files_in_folder("runs")[1],
                                    style={"width": 180},
                                ),
                            ],
                            style=style_block,
                        ),
                        html.Div(
                            [
                                html.P("create new run"),
                                html.Button("fuse", id="merge-runs", n_clicks=0),
                            ],
                            style=style_block,
                        ),
                        html.Div(
                            [
                                html.P("qrels"),
                                dcc.Dropdown(
                                    id="dropdown-qrels",
                                    options=[
                                        {"label": file, "value": file}
                                        for file in files_in_folder("qrels")
                                    ],
                                    value=files_in_folder("qrels")[0],
                                    style={"width": 300},
                                ),
                            ],
                            style=style_block,
                        ),
                        html.Div(
                            [
                                html.P("metric"),
                                dcc.Dropdown(
                                    id="dropdown-metric",
                                    options=[
                                        {"label": "NDCG@5", "value": "ndcg_cut_5"},
                                        {"label": "NDCG@10", "value": "ndcg_cut_10"},
                                    ],
                                    value="ndcg_cut_5",
                                    style={"width": 180},
                                ),
                            ],
                            style=style_block,
                        ),
                        html.Div(
                            [
                                html.P("topic"),
                                dcc.Dropdown(
                                    id="dropdown-topic",
                                    options=[
                                        {"label": topic, "value": topic}
                                        for topic in qrels_dict.keys()
                                    ],
                                    value=list(qrels_dict.keys())[0],
                                    style={"width": 180},
                                ),
                            ],
                            style=style_block,
                        ),
                    ],
                    style={
                        "width": "100%",
                        "display": "flex",
                        "align-items": "center",
                        "justify-content": "center",
                    },
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="graph",
                            config={"displayModeBar": False, "displaylogo": False},
                        ),
                        dcc.Graph(
                            id="ranking",
                            config={"displayModeBar": False, "displaylogo": False},
                        ),
                    ],
                    style={"display": "flex", "justify-content": "center"},
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="graph-boxplot",
                            config={"displayModeBar": False, "displaylogo": False},
                        ),
                        dcc.Graph(
                            id="table",
                            config={"displayModeBar": False, "displaylogo": False},
                        ),
                    ],
                    style={"display": "flex", "justify-content": "center"},
                ),
            ],
        )
    ],
    style={"height": "100%"},
)


@app.callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    success = False
    if list_of_contents is not None:
        success = write_to_file(list_of_contents, list_of_names)
    if success:
        return layout.succeed_button()


@app.callback(
    Output("graph", "figure"),
    Output("ranking", "figure"),
    Output("graph-boxplot", "figure"),
    Output("table", "figure"),
    [
        Input("dropdown-qrels", "value"),
        Input("dropdown-run-1", "value"),
        Input("dropdown-run-2", "value"),
        Input("dropdown-metric", "value"),
        Input("dropdown-topic", "value"),
    ],
)
def update_graphs(qrels, run1, run2, metric, top):
    global qrels_dict

    df_a = trec_eval(metric, "qrels/" + qrels, run1)
    df_b = trec_eval(metric, "qrels/" + qrels, run2)
    df = pd.concat([df_a, df_b], axis=1)
    df = df.sort_values(run1, ascending=False)

    # ranking
    ranking_1 = read_run("runs/" + run1)
    ranking_2 = read_run("runs/" + run2)

    df_dict_a = {}
    for topic in ranking_1.keys():
        df_dict_a[topic] = pd.DataFrame(ranking_1[topic], columns=["docid"])
        df_dict_a[topic][run1] = df_dict_a[topic]["docid"].apply(
            lambda x: find_relevance(x, qrels_dict[topic])
        )

    df_dict_b = {}
    for topic in ranking_2.keys():
        df_dict_b[topic] = pd.DataFrame(ranking_2[topic], columns=["docid"])
        df_dict_b[topic][run2] = df_dict_b[topic]["docid"].apply(
            lambda x: find_relevance(x, qrels_dict[topic])
        )

    # merge dataframes
    df_dict = {}
    df_dict[top] = df_dict_a[top].merge(
        df_dict_b[top], left_index=True, right_index=True
    )

    # set n to 5 if @5 or 10 if @10:
    total = 1
    n = int("".join(filter(str.isdigit, metric)))
    block_size = total / n

    # ndcg plot
    fig_a = df.plot.bar(barmode="group")
    fig_a.update_layout(
        plot_bgcolor="white",
        yaxis_title=pretty_metric[metric],
        xaxis_title="Topic",
        title=(
            f"{pretty_metric[metric]}: {df_a[run1].mean():.4f}"
            f"({df_a[run1].median():.4f}) & {df_b[run2].mean():.4f}"
            f" ({df_b[run2].median():.4f})"
        ),
        title_x=0.5,
    )

    # ranking annotations docids (should be put in separate function)
    y1 = df_dict[top][run1].values
    y2 = df_dict[top][run2].values

    xcoord = df_dict[top].iloc[0:n].index  # [0,1,2]

    annotations1 = [
        dict(
            x=8,  # xi-0.2,
            y=xi - (total / 5) + (5 / 30),
            text=df_dict[top]["docid_x"].iloc[xi],
            xanchor="auto",
            yanchor="bottom",
            showarrow=False,
            font={"size": block_size * 75, "color": "grey"},
        )
        for xi, yi in zip(xcoord, y1)
    ]

    annotations2 = [
        dict(
            x=8,
            y=xi + (total / 5) + (5 / 30),
            text=mark_new_text(
                df_dict[top]["docid_y"].iloc[xi],
                df_dict[top]["docid_x"].iloc[0:n],
            ),
            xanchor="auto",
            yanchor="bottom",
            showarrow=False,
            font={
                "size": block_size * 75,
                "color": mark_new(
                    df_dict[top]["docid_y"].iloc[xi], df_dict[top]["docid_x"].iloc[0:n]
                ),
            },
        )
        for xi, yi in zip(xcoord, y2)
    ]

    annotations = annotations1 + annotations2

    # ranking plot
    fig_b = df_dict[top].iloc[0:n].plot.barh(x=[run1, run2], barmode="group")
    fig_b.update_layout(
        plot_bgcolor="white",
        yaxis={
            "tickmode": "array",
            "tickvals": np.arange(n),
            "ticktext": np.arange(1, n + 1),
            "autorange": "reversed",
        },
        title=f"{pretty_metric[metric]}: {df_a[run1].loc[top]} & {df_b[run2].loc[top]}",
        title_x=0.5,
        yaxis_title="Rank",
        xaxis={"range": [0, 16], "fixedrange": True},
        xaxis_title="Relevance",
        annotations=annotations,
    )

    df_all = pd.DataFrame()
    for file in files_in_folder("runs"):
        try:
            df_tmp = trec_eval(metric, "qrels/" + qrels, file)
            df_all = pd.concat([df_all, df_tmp], axis=1)
        except Exception as e:
            logging.info(f"{file} is not a TREC run. --> {e}")
            continue

    medians = df_all.median().sort_values()
    medians_desc = df_all.median().sort_values(ascending=False)

    traces = []
    for run_name, run_data in df_all[medians.index].iteritems():
        color = "rgb(0, 0, 0)"
        if run_name == run1:
            color = "rgb(99, 110, 250)"
        if run_name == run2:
            color = "rgb(239, 85, 59)"
        traces.append(
            go.Box(
                y=run_data,
                name=run_name,
                boxpoints="all",
                jitter=0.5,
                whiskerwidth=0.2,
                marker=dict(size=2, color=color),
                line=dict(width=1),
            )
        )

    fig_box = go.Figure(data=traces)
    fig_box.update_layout(
        plot_bgcolor="white",
        title="Overview",
        title_x=0.5,
        yaxis_title=pretty_metric[metric],
        showlegend=False,
    )

    headerColor = "grey"

    fig_table = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=[
                        "<b>run</b>",
                        f"<b>percentage new in top {n} (relative to base)</b>",
                        f"<b>{pretty_metric[metric]} (mean : median)</b>",
                        "<b>p-value (H0: Equal average with base)</b>",
                    ],
                    line_color="darkslategray",
                    fill_color=headerColor,
                    align=["left", "center"],
                    font=dict(color="white", size=12),
                ),
                cells=dict(
                    values=[
                        df_all[medians_desc.index].columns,
                        [
                            "{:.2f}%".format(
                                new_percentage(ranking_1, read_run("runs/" + file), n)
                            )
                            for file in df_all[medians_desc.index].columns
                        ],
                        [
                            (
                                f"{round(np.mean(df_all[run]), 4):.4f} : "
                                f"{round(np.median(df_all[run]), 4):.4f}"
                            )
                            for run in df_all[medians_desc.index].columns
                        ],
                        [
                            f"{ttest_rel(df_a, df_all[col])[1][0]:.4f}"
                            for col in df_all[medians_desc.index].columns
                            if col != run1
                        ],
                    ],
                    line_color="darkslategray",
                    fill_color=[
                        [
                            mark_current_runs(run1, run2, run)
                            for run in df_all[medians_desc.index].columns
                        ]
                    ],
                    align=["left", "center"],
                    font=dict(color="darkslategray", size=11),
                ),
            )
        ]
    )
    fig_table.update_layout(
        plot_bgcolor="white",
        title="Table",
        title_x=0.5,
        yaxis_title=pretty_metric[metric],
    )

    return fig_a, fig_b, fig_box, fig_table


@app.callback(
    Output("placeholder", "children"),
    [Input("merge-runs", "n_clicks")],
    State("dropdown-run-1", "value"),
    State("dropdown-run-2", "value"),
)
def start_fusion(clicks, run1, run2):
    if clicks > 0:
        fuse_runs(run1, run2)


if __name__ == "__main__":
    app.run_server(host="0.0.0.0")
