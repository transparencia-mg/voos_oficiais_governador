import os
import io
import pandas as pd
from dash import Dash, html, dcc, Output, Input, State, ctx, callback
import dash
from components.filters import filters_layout
from components.cards import summary_cards_row
from components.charts import destinos_bar_figure, horas_line_figure
from components.tables import flights_table

# Inicialização do app
external_stylesheets = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
]
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

# Carregar dados (tenta CSV em data/voos.csv, senão usa CSV embutido)
# ================================
# CARREGAMENTO DOS CSV NORMALIZADOS
# ================================

import os
import glob
import pandas as pd

# carregar todos os CSVs normalizados
FILES = glob.glob(os.path.join("data", "normalized", "voos_*.csv"))

if not FILES:
    raise FileNotFoundError("Nenhum arquivo encontrado em data/normalized/*.csv. Rode normalize_voos.py primeiro.")

df_list = []
for f in FILES:
    try:
        df_list.append(pd.read_csv(f, dtype=str))
    except Exception as e:
        print(f"Erro ao ler {f}: {e}")

df_all = pd.concat(df_list, ignore_index=True).fillna("")

# garantir nomes consistentes
df_all.columns = [c.strip().replace(" ", "_") for c in df_all.columns]

# ================================
# FUNÇÃO: AGRUPAR PASSAGEIROS POR VOO
# ================================

def compute_voos_dataframe(df):
    df_grouped = (
        df.groupby(
            [
                "Data",
                "Diario_de_Bordo",
                "Origem",
                "Destino",
                "Horas_Voadas",
                "Aeronave",
                "Orgao",
                "Situacao",
                "Ano",
            ],
            dropna=False,
        )
        .agg({"Passageiros": "count"})
        .reset_index()
    )

    df_grouped = df_grouped.rename(columns={"Passageiros": "Total_Passageiros"})
    return df_grouped

# Layout
app.layout = html.Div(children=[
    html.Div(className="dashboard-header", children=[
        html.Div(className="container d-flex justify-content-between align-items-center", children=[
            html.Div(className="d-flex align-items-center gap-3", children=[
                html.Div(className="logo", children="MG"),
                html.Div(children=[
                    html.H3("Voos Oficiais - Governo do Estado de Minas Gerais", style={"margin":"0","color":"white"}),
                    html.Div("Relatório de Voos de Autoridade - Dados Atualizados", style={"color":"white","opacity":"0.9","fontSize":"14px"})
                ])
            ]),
            html.Div(className="d-flex gap-3", children=[
                html.A(html.Span(className="icon-top", children=[html.I(className="fas fa-chart-pie"), html.Span("Visão Geral")]), href="#"),
                html.Button(id="btn-download-csv-top", className="btn-primary-dash", children=html.Span([html.I(className="fas fa-file-csv"), html.Span(" Download Base", style={"marginLeft":"8px"})])),
                html.A(html.Span(className="icon-top", children=[html.I(className="fas fa-database"), html.Span("Dados Abertos / CKAN")]), href="#")
            ])
        ])
    ]),
    html.Div(className="container", style={"marginTop":"20px"}, children=[
        # Data status + actions
        html.Div(id="data-status", children=[
            html.Div(id="data-info", children="Dados carregados: {} registros".format(len(df_all)))
        ]),

        # filtros
        filters_layout(),

        # summary cards
        summary_cards_row(),

        html.Div(className="row", children=[
            html.Div(className="col-md-6", children=[
                html.Div(className="card-dash", children=[
                    dcc.Graph(id="chart-destinos", figure=destinos_bar_figure(df_all))
                ])
            ]),
            html.Div(className="col-md-6", children=[
                html.Div(className="card-dash", children=[
                    dcc.Graph(id="chart-horas", figure=horas_line_figure(df_all))
                ])
            ])
        ]),

        # action buttons and downloads
        html.Div(style={"marginTop":"10px","display":"flex","justifyContent":"space-between","alignItems":"center"}, children=[
            html.Div(children=[
                html.Button("Exportar CSV", id="btn-export-csv", className="btn-primary-dash"),
                html.Button("Exportar Excel", id="btn-export-xlsx", style={"marginLeft":"8px"}),
                html.Button("Exportar PDF (Print)", id="btn-print", style={"marginLeft":"8px"}),
            ]),
            html.Div(children=[
                dcc.Download(id="download-data"),
                html.Span(id="info-selection", style={"marginLeft":"8px"})
            ])
        ]),

        # table
        html.Div(style={"marginTop":"12px"}, children=[
            html.H5("Detalhamento de Voos"),
            html.Div(id="table-container", children=[flights_table(df_all)])
        ])
    ]),
    # store filtered df in browser
    dcc.Store(id="store-full", data=df_all.to_dict("records")),
    dcc.Store(id="store-filtered", data=df_all.to_dict("records")),
    # clientside callback for print
    dcc.Store(id="trigger-print", data=0)
])

# Helpers
def filter_dataframe(df, filters):
    df2 = df.copy()
    # ano
    ano = filters.get("ano","all")
    if ano and ano != "all":
        df2 = df2[df2["Ano"] == str(ano)]
    mes = filters.get("mes","all")
    if mes and mes != "all":
        # Data expected dd/mm/yyyy
        df2 = df2[df2["Data"].str.split("/").apply(lambda s: s[1] if len(s)>=2 else "").astype(str) == str(mes)]
    origem = filters.get("origem","all")
    if origem and origem != "all":
        df2 = df2[df2["Origem"] == origem]
    destino = filters.get("destino","all")
    if destino and destino != "all":
        df2 = df2[df2["Destino"] == destino]
    orgao = filters.get("orgao","all")
    if orgao and orgao != "all":
        df2 = df2[df2["Orgao"] == orgao]
    situacao = filters.get("situacao","all")
    if situacao and situacao != "all":
        df2 = df2[df2["Situacao"].str.upper() == situacao.upper()]
    # periodo (básico)
    periodo = filters.get("periodo","all")
    if periodo and periodo != "all":
        from datetime import datetime, timedelta
        today = pd.Timestamp.today()
        def parse_date(s):
            try:
                parts = s.split("/")
                return pd.Timestamp(int(parts[2]), int(parts[1]), int(parts[0]))
            except:
                return None
        df2["__date"] = df2["Data"].apply(parse_date)
        if periodo == "7d":
            cutoff = today - pd.Timedelta(days=7)
            df2 = df2[df2["__date"] >= cutoff]
        elif periodo == "30d":
            cutoff = today - pd.Timedelta(days=30)
            df2 = df2[df2["__date"] >= cutoff]
        elif periodo == "this_year":
            df2 = df2[df2["Ano"] == str(today.year)]
        elif periodo == "last_year":
            df2 = df2[df2["Ano"] == str(today.year - 1)]
        if "__date" in df2.columns:
            df2 = df2.drop(columns="__date")
    return df2

# Callbacks --------------------------------------------------------

# 1) preencher opções dos filtros ao iniciar (anos, origens, destinos, orgaos)
@app.callback(
    Output("filter-ano","options"),
    Output("filter-origem","options"),
    Output("filter-destino","options"),
    Output("filter-orgao","options"),
    Input("store-full","data")
)
def populate_filters(data):
    df = pd.DataFrame(data)
    anos = sorted(df["Ano"].dropna().unique().tolist(), reverse=True)
    opt_anos = [{"label":"Todos","value":"all"}] + [{"label":a,"value":a} for a in anos]
    origens = sorted(df["Origem"].dropna().unique().tolist())
    opt_origens = [{"label":"Todas","value":"all"}] + [{"label":o,"value":o} for o in origens]
    destinos = sorted(df["Destino"].dropna().unique().tolist())
    opt_destinos = [{"label":"Todos","value":"all"}] + [{"label":d,"value":d} for d in destinos]
    orgaos = sorted(df["Orgao"].dropna().unique().tolist())
    opt_orgaos = [{"label":"Todos","value":"all"}] + [{"label":o,"value":o} for o in orgaos]
    return opt_anos, opt_origens, opt_destinos, opt_orgaos

# 2) aplicar filtros (botão)
@app.callback(
    Output("store-filtered","data"),
    Output("data-info","children"),
    Input("btn-apply","n_clicks"),
    Input("btn-refresh","n_clicks"),
    Input("btn-clear","n_clicks"),
    State("filter-ano","value"),
    State("filter-mes","value"),
    State("filter-periodo","value"),
    State("filter-origem","value"),
    State("filter-destino","value"),
    State("filter-orgao","value"),
    State("filter-situacao","value"),
    State("store-full","data"),
    prevent_initial_call=True
)
def apply_filters(n_apply, n_refresh, n_clear, ano, mes, periodo, origem, destino, orgao, situacao, data_full):
    triggered = ctx.triggered_id
    df_full = pd.DataFrame(data_full)
    if triggered == "btn-clear":
        # reset
        return df_full.to_dict("records"), html.Div(f"Filtros limpos — {len(df_full)} registros")
    filters = {"ano":ano,"mes":mes,"periodo":periodo,"origem":origem,"destino":destino,"orgao":orgao,"situacao":situacao}
    df_filtered = filter_dataframe(df_full, filters)
    return df_filtered.to_dict("records"), html.Div(f"Filtrado — {len(df_filtered)} registros")

# 3) atualizar gráficos e tabela quando store-filtered muda
@app.callback(
    Output("chart-destinos","figure"),
    Output("chart-horas","figure"),
    Output("table-container","children"),
    Output("summary-row","children"),
    Input("store-filtered","data")
)
def update_visuals(data):
    df = pd.DataFrame(data)
    # gerar charts
    fig1 = destinos_bar_figure(df)
    fig2 = horas_line_figure(df)
    # table
    tbl = flights_table(df)
    # summary
    total_voos = len(df)
    total_horas = pd.to_numeric(df.get("Horas_Voadas",pd.Series([])), errors='coerce').fillna(0).sum()
    total_pass = pd.to_numeric(df.get("Passageiros",pd.Series([])).fillna(0), errors='coerce').sum()
    destinos_unicos = df["Destino"].nunique()
    # criar cards dinâmicos
    from dash import html
    cards = [
        html.Div(className="col-md-3", children=[html.Div(className="summary-card", children=[html.H3(str(total_voos)), html.P("Voos Registrados"), html.Div(html.Span(f"{df['Ano'].nunique()} anos", className="badge-primary"))])]),
        html.Div(className="col-md-3", children=[html.Div(className="summary-card", children=[html.H3(f"{total_horas:.1f}h"), html.P("Total de Horas Voadas"), html.Div(html.Span(f"Média: {(total_horas/total_voos if total_voos else 0):.1f}h", className="badge-primary"))])]),
        html.Div(className="col-md-3", children=[html.Div(className="summary-card", children=[html.H3(str(int(total_pass))), html.P("Passageiros Transportados"), html.Div(html.Span("Média por voo", className="badge-primary"))])]),
        html.Div(className="col-md-3", children=[html.Div(className="summary-card", children=[html.H3(str(destinos_unicos)), html.P("Destinos Diferentes"), html.Div(html.Span(f"{destinos_unicos} destinos únicos", className="badge-primary"))])])
    ]
    return fig1, fig2, tbl, cards

# 4) export CSV / XLSX
@app.callback(
    Output("download-data","data"),
    Input("btn-export-csv","n_clicks"),
    Input("btn-export-xlsx","n_clicks"),
    State("store-filtered","data"),
    prevent_initial_call=True
)
def export_data(n_csv, n_xlsx, data_filtered):
    triggered = ctx.triggered_id
    df = pd.DataFrame(data_filtered)
    if triggered == "btn-export-csv":
        return dcc.send_data_frame(df.to_csv, f"voos_oficiais_mg_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv", index=False)
    elif triggered == "btn-export-xlsx":
        # gerar xlsx bytes
        def to_xlsx_bytes(df_):
            import io
            with io.BytesIO() as buffer:
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_.to_excel(writer, index=False, sheet_name="Voos")
                return buffer.getvalue()
        return dcc.send_bytes(lambda: to_xlsx_bytes(df), filename=f"voos_oficiais_mg_{pd.Timestamp.now().strftime('%Y-%m-%d')}.xlsx")
    return None

# 5) top download button
@app.callback(
    Output("download-data","data"),
    Input("btn-download-csv-top","n_clicks"),
    State("store-full","data"),
    prevent_initial_call=True
)
def top_download(n_clicks, data_full):
    if not n_clicks:
        return dash.no_update
    df = pd.DataFrame(data_full)
    return dcc.send_data_frame(df.to_csv, f"voos_oficiais_mg_full_{pd.Timestamp.now().strftime('%Y-%m-%d')}.csv", index=False)

# 6) cliente print (browser)
app.clientside_callback(
    """
    function(n_clicks){
        if (!n_clicks) return "";
        window.print();
        return "";
    }
    """,
    Output("trigger-print","data"),
    Input("btn-print","n_clicks")
)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 7860))
    app.run_server(host="0.0.0.0", port=port, debug=False)

