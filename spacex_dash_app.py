"""
Plotly Dash Lab — SpaceX Launch Records Dashboard

Este script implementa las TAREAS 1–4 del instructivo:
- Dropdown para seleccionar sitio de lanzamiento (site-dropdown)
- Callback para gráfico de pastel (success-pie-chart)
- RangeSlider para rango de carga útil (payload-slider)
- Callback para scatter plot (success-payload-scatter-chart)

Ejecución (terminal):
    python3.11 -m pip install pandas dash plotly
    python3.11 spacex_dash_app.py

Asegúrate de tener el archivo:
    spacex_launch_dash.csv
en el mismo directorio que este script.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output


DATA_PATH = Path(__file__).with_name("spacex_launch_dash.csv")


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset en: {path}\n"
            "Descárgalo como 'spacex_launch_dash.csv' y colócalo en el mismo directorio que este script."
        )
    df = pd.read_csv(path)
    required_cols = {"Launch Site", "class", "Payload Mass (kg)", "Booster Version Category"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el CSV: {sorted(missing)}")
    return df


spacex_df = load_data(DATA_PATH)

# Valores para el slider
min_payload = float(spacex_df["Payload Mass (kg)"].min())
max_payload = float(spacex_df["Payload Mass (kg)"].max())

# Opciones del dropdown
launch_sites = sorted(spacex_df["Launch Site"].dropna().unique().tolist())
dropdown_options = [{"label": "All Sites", "value": "ALL"}] + [
    {"label": site, "value": site} for site in launch_sites
]

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1("SpaceX Launch Records Dashboard", style={"textAlign": "center"}),
        dcc.Dropdown(
            id="site-dropdown",
            options=dropdown_options,
            value="ALL",
            placeholder="Select a Launch Site here",
            searchable=True,
            style={"width": "80%", "margin": "0 auto"},
        ),
        html.Br(),
        dcc.Graph(id="success-pie-chart"),
        html.Br(),
        html.P("Payload range (Kg):", style={"width": "80%", "margin": "0 auto"}),
        dcc.RangeSlider(
            id="payload-slider",
            min=0,
            max=10000,
            step=1000,
            marks={0: "0", 2500: "2500", 5000: "5000", 7500: "7500", 10000: "10000"},
            value=[min_payload, max_payload],
            tooltip={"placement": "bottom", "always_visible": False},
        ),
        html.Br(),
        dcc.Graph(id="success-payload-scatter-chart"),
    ]
)


@app.callback(
    Output(component_id="success-pie-chart", component_property="figure"),
    Input(component_id="site-dropdown", component_property="value"),
)
def get_pie_chart(entered_site: str):
    """
    - Si ALL: muestra el total de lanzamientos exitosos por sitio (suma de class).
    - Si sitio específico: muestra conteo de éxitos (1) vs fracasos (0) en ese sitio.
    """
    if entered_site == "ALL":
        fig = px.pie(
            spacex_df,
            values="class",
            names="Launch Site",
            title="Total Successful Launches by Site",
        )
        return fig

    filtered_df = spacex_df[spacex_df["Launch Site"] == entered_site]

    outcome_counts = (
        filtered_df["class"]
        .value_counts()
        .rename_axis("class")
        .reset_index(name="count")
        .sort_values("class")
    )
    # Mapear 0/1 a etiquetas más claras
    outcome_counts["Outcome"] = outcome_counts["class"].map({0: "Failure", 1: "Success"}).fillna(
        outcome_counts["class"].astype(str)
    )

    fig = px.pie(
        outcome_counts,
        values="count",
        names="Outcome",
        title=f"Total Launch Outcomes for site {entered_site}",
    )
    return fig


@app.callback(
    Output(component_id="success-payload-scatter-chart", component_property="figure"),
    [
        Input(component_id="site-dropdown", component_property="value"),
        Input(component_id="payload-slider", component_property="value"),
    ],
)
def get_scatter_plot(entered_site: str, payload_range: list[float]):
    """
    - Filtra por rango de Payload Mass (kg)
    - Si ALL: usa todos los sitios; si no, filtra por sitio.
    - Colorea por Booster Version Category.
    """
    low, high = payload_range
    df = spacex_df[
        (spacex_df["Payload Mass (kg)"] >= low) & (spacex_df["Payload Mass (kg)"] <= high)
    ]

    if entered_site != "ALL":
        df = df[df["Launch Site"] == entered_site]
        title = f"Correlation between Payload and Success for site {entered_site}"
    else:
        title = "Correlation between Payload and Success for all Sites"

    fig = px.scatter(
        df,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        title=title,
    )
    return fig


if __name__ == "__main__":
    # En entornos tipo Skills Network suele ser útil 0.0.0.0 y puerto 8050.
    app.run_server(host="0.0.0.0", port=8050, debug=False)
