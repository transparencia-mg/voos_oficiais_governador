from dash import html

def summary_cards_row():
    def card(title, value, sub):
        return html.Div(className="col-md-3", children=[
            html.Div(className="summary-card", children=[
                html.H3(value),
                html.P(title),
                html.Div(html.Span(sub, className="badge-primary"))
            ])
        ])
    row = html.Div(className="row", id="summary-row", children=[
        card("Voos Registrados", "—", "—"),
        card("Total de Horas Voadas", "—", "—"),
        card("Passageiros Transportados", "—", "—"),
        card("Destinos Diferentes", "—", "—"),
    ])
    return row
