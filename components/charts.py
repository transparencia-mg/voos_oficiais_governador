import plotly.express as px
import pandas as pd

def destinos_bar_figure(df: pd.DataFrame, top_n: int = 8):
    if df.empty:
        return px.bar(title="Destinos Mais Frequentes")
    # extrair nome simples de destino
    df = df.copy()
    df['dest_simple'] = df['Destino'].fillna('Desconhecido').apply(lambda s: s.split('(')[0].strip())
    s = df['dest_simple'].value_counts().nlargest(top_n).reset_index()
    s.columns = ['destino','count']
    fig = px.bar(s, x='destino', y='count', title='Destinos Mais Frequentes')
    fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="white")
    return fig

def horas_line_figure(df: pd.DataFrame):
    if df.empty:
        return px.line(title="Horas Voadas por Ano")
    df = df.copy()
    df['Horas_Voadas'] = pd.to_numeric(df['Horas_Voadas'], errors='coerce').fillna(0)
    s = df.groupby('Ano')['Horas_Voadas'].sum().reset_index().sort_values('Ano')
    fig = px.line(s, x='Ano', y='Horas_Voadas', markers=True, title='Horas Voadas por Ano')
    fig.update_layout(margin=dict(l=10,r=10,t=40,b=10), plot_bgcolor="white")
    return fig
