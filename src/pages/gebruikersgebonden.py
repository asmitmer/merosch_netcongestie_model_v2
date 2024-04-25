# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 17:15:37 2024

@author: a.smit
"""

import pandas as pd
import dash
from dash import dcc, html, callback
import plotly.express as px
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from pages import ids
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import json


dash.register_page(__name__, path='/gebruikersgebonden', name="Gebruikersgebonden", order=1)

data_gb = pd.read_csv("data/input_netcongestie_model_ontwerp_gebruikersgebonden.csv", sep=';', decimal=',', index_col=0)
data_gb.index = pd.date_range("1/1/2025 00:00:00", freq = '15T', periods = 8760*4)
data_gb["verdeling"] = pd.Series(dtype='float')
data_gb["gb_verbruik"] = pd.Series(dtype='float')

data = pd.read_csv("data/input_netcongestie_model_ontwerp.csv", sep=';', decimal=',', index_col=0)
data.index = pd.date_range("1/1/2025 00:00:00", freq = '15T', periods = 8760*4)

data_gb_copy = data_gb
data_copy = data.copy()

def create_profiel_gb(gebruiksfunctie, gbo, vermogensvraag):
    if gebruiksfunctie == "school":
        data_gb_copy["verdeling"] = data_gb_copy["school_verdeling"]
    else:
        data_gb_copy["verdeling"] = data_gb_copy["kantoor_verdeling"]
    
    #daily_max = data_gb['verdeling'].resample('D').max()
    #daily_workday = daily_max.apply(lambda x: 'warmte_aan' if x > 0.0001 else 'warmte_uit')
    #date_series = pd.Series(data_gb.index.date, index=data_gb.index)
    #data_gb['warmte_of_niet'] = date_series.map(daily_workday.to_dict())
    
    data_gb_copy["gb_verbruik"] = data_gb_copy["verdeling"] * gbo * vermogensvraag / data_gb_copy["verdeling"].max() / 1000
    
    max_value_warmtevraag = round(data_gb_copy["gb_verbruik"].max())
    max_index_warmtevraag = data_gb_copy["gb_verbruik"].idxmax()
    
    laagste_temperatuur = data_gb_copy["gb_verbruik"].idxmax()
    start_date = laagste_temperatuur.normalize()  # This sets the time to 00:00:00, effectively finding the start of the day
    eind_date = start_date + pd.DateOffset(days=1) 
    
    #Kleuren
    blauw = 'rgb(0,80,134)'
    lichtblauw = 'rgb(4,195,238)'
    oranje = 'rgb(236,102,9)'
    groen = 'rgb(82,200,50)'
    
    blauw_l = 'rgb(179,224,255)'
    lichtblauw_l = 'rgb(201,244,254)'
    oranje_l = 'rgb(253,223,204)'
    groen_l = 'rgb(220,244,213)'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x = data_gb_copy.index, y = data_gb_copy["gb_verbruik"], mode = 'lines', line=dict(color='black'), name = 'Gebruikersgebonden energievraag'))
    
    fig.update_layout(
                title = dict(
                    text="Elektriciteitsprofiel gebruikersgebonden energieverbruik",
                    x = 0.5,
                    font=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    ),
                yaxis=dict(
                title="Elektrisch vermogen [kW]",
                titlefont=dict(
                    family="Arial",
                    size=15,
                    color="black"
                ),
                tickfont=dict(
                    family="Arial",
                    size=15,
                    color="black"
                )),
                xaxis=dict(
                    range = [start_date, eind_date],# Focus on the whole day
                    titlefont=dict(
                        family="Arial",
                        size=20,
                        color="black"
                    ),
                    tickfont=dict(
                        family="Arial",
                        size=15,
                        color="black"
                    )
                ),
                paper_bgcolor="#e5ecf6",
                margin=dict(l=70, r=10, t=50, b=10),
                legend=dict(
                    y=0.5,
                    font=dict(
                        family="Arial",
                        size=15,
                        color="black")
                ),
                title_y = 0.97)
    
    fig.add_annotation(
                        text=f'Piekvraag: {max_value_warmtevraag} kW',  # Customize the text displayed
                        x=max_index_warmtevraag,
                        y=max_value_warmtevraag + 1,
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor='red',
                        font=dict(size=12, color='black'),
                       bordercolor='black',
                       borderwidth=2,
                       bgcolor='white',
                       opacity=0.9
                    )
    
    
    fig.show(auto_open = False)
    
    data_json_gb = data_gb_copy.to_json(date_format='iso', orient='split')
    return fig, data_json_gb


button_gb = html.Button(
                        "Klik om een elektriciteitsprofiel voor de warmtevoorziening en ventilatie te genereren",
                        id=ids.BUTTON_FIGUUR_GB,
                        n_clicks=0,
                        className="button",
                        style={'width': '100%', 'display': 'block'} 
                    )

gebruiksfunctie_dropdown_box = html.Div(
        children=[
            html.Div([
                html.H6("Gebruiksfunctie: ", style={"display": "inline-block", "margin-right": "10px", "width": "120px"}),
                dcc.Dropdown(
                    className = "dropdown-box",
                    id=ids.GEBRUIKSFUNCTIE_DROPDOWN,
                    options=[
                        {'label': 'Schoolfunctie', 'value': 'school'},
                        {'label': 'Kantoorfunctie', 'value': 'kantoor'},
                    ],
                    #value = "school",
                    placeholder="Selecteer een optie...",
                    clearable = True,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "190px", "text-align": "left"}  # Adjust alignment and display
                ),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )


gebruiksoppervlakte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Gebruiksoppervlakte (GBO): ", style={"display": "inline-block", "margin-right": "10px", "width": "210px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.GEBRUIKSOPPERVLAKTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=1700,
                    min=100,
                    max=100000,
                    step=10,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

gb_vermogen_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Vermogensvraag: ", style={"display": "inline-block", "margin-right": "10px", "width": "120px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.GB_VERMOGEN_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=30,
                    min=10,
                    max=1000,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" W/m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

#BOX
gb_uitgangspunten_box = dbc.Col(
    [
        html.Div([
            html.Div([
                html.H4("Uitgangspunten gebruikersgebonden energieverbruik", className="mb-2"),
            ],style={'padding': '10px', 'border-radius': '5px', 'margin-bottom': '0px'}),
        ], style={'margin': '0 15px'}),# Heading above the box, added bottom margin for spacing
        html.Div([  # This Div contains the content of the box with borders and styling
            html.Div([
                dbc.Row([
                dbc.Col([gebruiksfunctie_dropdown_box], md = 3),
                dbc.Col([gebruiksoppervlakte_input_box], md = 3),
                dbc.Col([gb_vermogen_input_box], md = 3),
                ])
            ], style={'border': '3px solid #ddd', 'padding': '10px', 'border-radius': '5px'}),
        ], style={'margin-top': '0px', 'margin-bottom': '15px', 'margin-left': '15px', 'margin-right': '15px'}),
    ],
    md=12, 
    className="box-inputs"
)

##Layout
layout = html.Div(className = "app-div", children=[
    dbc.Row([
        dbc.Col(
        html.H1("Merosch Netcongestie Model - versie 0.1", style={'text-align': 'center', 'margin': 'auto'}), width=9),
        dbc.Col(html.Img(src='assets/Logo-Merosch_liggend_RGB.png', alt='image', style={'height':'75%', 'width':'75%'}))
            ]),
    html.Hr(),
    dbc.Row([gb_uitgangspunten_box]),
    html.Hr(),
    button_gb,
    html.Hr(),
    html.Div(id="graph-container-gb", style={'display': 'none'}, children=[
        dcc.Graph(id=ids.ELEKTRICITEITSPROFIEL_GB)
    ])
])

####################### CALLBACKS ################################
@callback(
    [Output(ids.ELEKTRICITEITSPROFIEL_GB, 'figure'),
     Output('data-store-gb', 'data')],
    Input(ids.BUTTON_FIGUUR_GB, 'n_clicks'),
    [State(ids.GEBRUIKSFUNCTIE_DROPDOWN, 'value'),
     State(ids.GEBRUIKSOPPERVLAKTE_INPUT, 'value'),
     State(ids.GB_VERMOGEN_INPUT, 'value'),]
)
def update_profiel_gb(nclicks, gebruiksfunctie, gbo, vermogensvraag):
    if nclicks is None or nclicks == 0:
        raise PreventUpdate
    return create_profiel_gb(gebruiksfunctie, gbo, vermogensvraag)
          
@callback(
    Output('graph-container-gb', 'style'),
    Input(ids.BUTTON_FIGUUR_GB, 'n_clicks'),
    Input(ids.GEBRUIKSFUNCTIE_DROPDOWN, 'value'),
)
def display_graph_gb(n_clicks, gebruiksfunctie):
    if n_clicks and n_clicks > 0 and gebruiksfunctie is not None:
        return {'display': 'block'}  # Makes the graph visible
    return {'display': 'none'}  # Keeps the graph hidden initially