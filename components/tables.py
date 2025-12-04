from dash import dash_table, html
import pandas as pd

def flights_table(df: pd.DataFrame, page_size:int=10):
    if df is None:
        df = pd.DataFrame()
    df_display = df.copy()
    # garantir colunas com nomes amigáveis
    df_display = df_display.rename(columns={
        "Diario_de_Bordo":"Diário de Bordo",
        "Horas_Voadas":"Horas Voadas",
        "Orgao":"Órgão"
    })
    columns = [{"name": c, "id": c} for c in df_display.columns]
    table = dash_table.DataTable(
        id="table-flights",
        columns=columns,
        data=df_display.to_dict("records"),
        page_size=page_size,
        style_table={"overflowX":"auto"},
        style_cell={"textAlign":"left","padding":"6px"},
        style_header={
            "backgroundColor":"#29435A",
            "color":"white",
            "fontWeight":"600"
        }
    )
    return html.Div(className="dash-table", children=[table])

