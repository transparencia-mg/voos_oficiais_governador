from dash import html, dcc

def filters_layout():
    return html.Div(className="card-dash", children=[
        html.Div(style={"display":"flex","gap":"16px","flexWrap":"wrap"}, children=[
            html.Div(children=[
                html.Label("Ano", className="filter-label"),
                dcc.Dropdown(id="filter-ano", options=[{"label":"Todos","value":"all"}], value="all"),
            ], style={"minWidth":"160px","flex":"1"}),
            html.Div(children=[
                html.Label("Mês", className="filter-label"),
                dcc.Dropdown(id="filter-mes", options=[{"label":"Todos","value":"all"}] + [{"label":m,"value":i} for i,m in enumerate(
                    ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"], start=1)], value="all"),
            ], style={"minWidth":"160px","flex":"1"}),
            html.Div(children=[
                html.Label("Período", className="filter-label"),
                dcc.Dropdown(id="filter-periodo", options=[
                    {"label":"Todos os Períodos","value":"all"},
                    {"label":"Últimos 7 dias","value":"7d"},
                    {"label":"Últimos 30 dias","value":"30d"},
                    {"label":"Este ano","value":"this_year"},
                    {"label":"Ano anterior","value":"last_year"},
                ], value="all"),
            ], style={"minWidth":"190px","flex":"1"}),
            html.Div(children=[
                html.Label("Origem", className="filter-label"),
                dcc.Dropdown(id="filter-origem", options=[{"label":"Todas","value":"all"}], value="all"),
            ], style={"minWidth":"220px","flex":"1"}),
            html.Div(children=[
                html.Label("Destino", className="filter-label"),
                dcc.Dropdown(id="filter-destino", options=[{"label":"Todos","value":"all"}], value="all"),
            ], style={"minWidth":"220px","flex":"1"}),
            html.Div(children=[
                html.Label("Órgão", className="filter-label"),
                dcc.Dropdown(id="filter-orgao", options=[{"label":"Todos","value":"all"}], value="all"),
            ], style={"minWidth":"220px","flex":"1"}),
            html.Div(children=[
                html.Label("Situação", className="filter-label"),
                dcc.Dropdown(id="filter-situacao", options=[
                    {"label":"Todas","value":"all"},
                    {"label":"REALIZADO","value":"REALIZADO"},
                    {"label":"PLANEJADA","value":"PLANEJADA"},
                    {"label":"CANCELADA","value":"CANCELADA"},
                ], value="all"),
            ], style={"minWidth":"220px","flex":"1"}),
        ]),
        html.Div(style={"marginTop":"12px","display":"flex","gap":"8px"}, children=[
            html.Button("Aplicar Filtros", id="btn-apply", className="btn-primary-dash"),
            html.Button("Limpar Filtros", id="btn-clear", n_clicks=0),
            html.Button("Atualizar Dados", id="btn-refresh", n_clicks=0),
        ])
    ])
