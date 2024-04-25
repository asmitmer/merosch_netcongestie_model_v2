# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 19:54:04 2024

@author: a.smit
"""

from dash import Dash, html, dcc
import dash
from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import logging

app = Dash(__name__, pages_folder='pages', use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Define styles
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa"
}

# Sidebar
sidebar = html.Div(
    [
        html.H2("Navigatie", className="display-4"),
        html.Hr(),
        html.Div(
            [dcc.Link(page['name'], href=page["relative_path"], style={"color": "black", "text-decoration": "none", "font-family": "Arial", "font-size": "20px"}, className="nav-link")
             for page in dash.page_registry.values()],
            className="nav-item"
        )
    ],
    style=SIDEBAR_STYLE,
)

# Content area next to the sidebar
content = html.Div(id='page-content', style={"margin-left": "0rem", "margin-right": "0rem", "padding": "0rem 0rem"})

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id='data-store-warmte-ventilatie'),
    dcc.Store(id='data-store-gb'),
    dbc.Row(
        [
            dbc.Col(sidebar, md=2, className="mt-5", style={'position': 'fixed'}),
            dbc.Col(content, md={'size': 10, 'offset': 2}),  # Content area
            dbc.Col(dash.page_container, md={'size': 10, 'offset': 2})  # This is automatically filled by Dash based on URL
        ]
    )
])

@app.callback(Output('page-content', 'children'),
              [Input("url", "pathname")])
def display_page(pathname):
    # Only show a message when on the home page
    if pathname == "/":
        return html.Div(className = "app-div", children=[
            dbc.Row([
                dbc.Col(
                html.H1("Merosch Netcongestie Model - versie 0.1", style={'text-align': 'center', 'margin': 'auto'}), width=9),
                dbc.Col(html.Img(src='assets/Logo-Merosch_liggend_RGB.png', alt='image', style={'height':'75%', 'width':'75%'}))
                    ]),
            html.Hr(),
            html.Div([
                    html.H4("Instructie speciaal voor Bart 😅"),
                    html.P("Het profiel bestaat uit het gebruikersgebonden elektriciteitsverbruik en warmte en ventilatie. In het menu hier links kan je naar de pagina's navigeren. Vul alles in en bekijk dan het profiel voor de dag met de piekvraag op de pagina Elektriciteitsprofiel. Mocht je niet weten wat je ergens moet invullen, dan weet je mij te vinden. Goed om te weten: bij simulatieduur op de pagina Warmte en ventialtie kan je geen maand of jaar invullen, anders crasht het model. Ook onthoud het model nog niet wat je hebt ingevuld als je naar een andere pagina swicht. Alles in een keer invullen dus. Succes!!")
                ])
        ])
    # No need to handle other paths, dash.page_container takes care of it
    return None

if __name__ == '__main__':
    app.run_server(debug=False)