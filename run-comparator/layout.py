import dash_html_components as html
import dash_bootstrap_components as dbc


def succeed_button():
    return html.Div(
        [
            dbc.Alert('Success!', color='success', dismissable=True)
        ],
    )
