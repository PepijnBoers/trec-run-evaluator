import dash_html_components as html


def succeed_button():
    return html.Div(
        [
            html.H5("Success"),
        ],
        style={
            "margin-left": 50,
            "margin-top": 5,
            "color": "white",
            "text-size": 10,
            "width": 150,
            "height": 40,
            "background-color": "green",
            "border-radius": 25,
            "text-align": "center",
        },
    )
