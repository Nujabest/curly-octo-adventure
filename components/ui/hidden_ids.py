from dash import html, dcc

_HIDDEN = {"display": "none"}


def _hidden_button(id_):
    return html.Button(id=id_, n_clicks=0, style=_HIDDEN)


def hidden_callback_placeholders(include_nav=True, include_driver_checklist=False):
    nav_ids = (
        [
            "btn-go-telemetry",
            "btn-go-championship",
            "btn-back-from-champ",
            "btn-back-from-dash",
        ]
        if include_nav
        else ["btn-back-from-champ", "btn-back-from-dash"]
    )

    nodes = [_hidden_button(i) for i in nav_ids]
    nodes += [
        _hidden_button(i) for i in ["quali-seg-Q1", "quali-seg-Q2", "quali-seg-Q3"]
    ]
    nodes.append(html.Div(id="quali-timeline-chart", style=_HIDDEN))

    if include_driver_checklist:
        nodes.append(
            dcc.Checklist(id="driver-checklist", options=[], value=[], style=_HIDDEN)
        )

    return nodes
