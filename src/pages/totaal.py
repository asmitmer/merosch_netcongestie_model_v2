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


dash.register_page(__name__, path='/totaal', name="Elektriciteitsprofiel", order=3)

####################### HISTOGRAM ###############################
def create_figuur(data_warmte_ventilatie_stored, data_gb_stored):
    data_wv = data_warmte_ventilatie_stored
    data_gb = data_gb_stored
    data_gb = data_gb_stored.reindex(data_wv.index, method='nearest')
    
    data_totaal = pd.DataFrame(index = data_wv.index)
    data_totaal["elektriciteitsvraag_warmte"] = data_wv["elektriciteitsvraag_warmte"]
    data_totaal["elektriciteitsvraag_ventilatie"] = data_wv["elektriciteitsvraag_ventilatie"]
    data_totaal["elektriciteitsvraag_gb"] = data_gb["gb_verbruik"]
    data_totaal["totaal"] = data_totaal["elektriciteitsvraag_warmte"] + data_totaal["elektriciteitsvraag_ventilatie"] + data_totaal["elektriciteitsvraag_gb"]
    
    piek_warmte_ventilatie_gb = data_totaal["totaal"].idxmax()
    start_date = piek_warmte_ventilatie_gb.normalize()
    eind_date = start_date + pd.DateOffset(days=1) 

    max_value_warmtevraag = round(data_totaal["totaal"].max())
    max_index_warmtevraag = data_totaal["totaal"].idxmax()
    
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
    fig.add_trace(go.Scatter(x = data_totaal.index, y = data_totaal["elektriciteitsvraag_warmte"], fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = blauw, name = 'Warmtevoorziening'))
    fig.add_trace(go.Scatter(x = data_totaal.index, y = data_totaal["elektriciteitsvraag_ventilatie"], fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = lichtblauw, name = 'Ventilatie'))
    fig.add_trace(go.Scatter(x = data_totaal.index, y = data_totaal["elektriciteitsvraag_gb"], fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = oranje, name = 'Gebruikersgebonden'))
    fig.add_trace(go.Scatter(x = data_totaal.index, y = data_totaal["totaal"] , mode = 'lines', line=dict(color='black'), name = 'Totaal'))
    
    fig.update_layout(
                title = dict(
                    text="Elektriciteitsprofiel warmtevoorziening, ventilatie en gebruikersgebonden energieverbruik",
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
    return fig

####################### WIDGETS ################################

####################### PAGE LAYOUT #############################
layout = html.Div(className = "app-div", children=[
    dbc.Row([
        dbc.Col(
        html.H1("Merosch Netcongestie Model - versie 0.1", style={'text-align': 'center', 'margin': 'auto'}), width=9),
        dbc.Col(html.Img(src='assets/Logo-Merosch_liggend_RGB.png', alt='image', style={'height':'75%', 'width':'75%'}))
            ]),
    html.Hr(),
    html.Div(id="graph-container-2", style={'display': 'none'}, children=[
        dcc.Graph(id="figuur_2")
    ])
])

@callback(
    Output('figuur_2', 'figure'),
    [Input('data-store-warmte-ventilatie', 'data'),
     Input('data-store-gb', 'data'),
     ]
)
def update_output(data_warmte_ventilatie, data_gb):
    if data_warmte_ventilatie is None and data_gb is not None:
        raise PreventUpdate
    
    df_json_wv = json.loads(data_warmte_ventilatie) if data_warmte_ventilatie else {}
    df_json_gb = json.loads(data_gb) if data_gb else {}

    # Ensure dictionaries have the required keys to avoid KeyErrors
    if 'data' not in df_json_wv or 'data' not in df_json_gb:
        raise PreventUpdate
    
    #df_json_wv = json.loads(data_warmte_ventilatie)  # Convert JSON string to Python dictionary
    data_wv = pd.DataFrame(data=df_json_wv['data'], index=pd.to_datetime(df_json_wv['index']), columns=df_json_wv['columns'])
    
    #df_json_gb = json.loads(data_gb)  # Convert JSON string to Python dictionary
    data_gb = pd.DataFrame(data=df_json_gb['data'], index=pd.to_datetime(df_json_gb['index']), columns=df_json_gb['columns'])
    
    return create_figuur(data_wv, data_gb)

@callback(
    Output('graph-container-2', 'style'),
    [Input('data-store-warmte-ventilatie', 'data'),
     Input('data-store-gb', 'data'),
     ]
)
def display_graph(data_ventilatie_warmte, data_gb):
    if data_ventilatie_warmte is not None and data_gb is not None:
        return {'display': 'block'}  # Makes the graph visible
    return {'display': 'none'}  # Keeps the graph hidden initially