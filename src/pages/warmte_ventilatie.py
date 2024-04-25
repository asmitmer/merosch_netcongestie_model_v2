# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 19:54:36 2024

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

dash.register_page(__name__, path='/warmte_ventilatie', name="Warmte en ventilatie", order=2)

data = pd.read_csv("data/input_netcongestie_model_ontwerp.csv", sep=';', decimal=',', index_col=0)
data.index = pd.date_range("1/1/2025 00:00:00", freq = '15T', periods = 8760*4)

data["transmissieverlies_gevel"] = pd.Series(dtype='float')
data["transmissieverlies_dak"] = pd.Series(dtype='float')
data["transmissieverlies_vloer"] = pd.Series(dtype='float')
data["transmissieverlies_raam"] = pd.Series(dtype='float')
data["temp_na_wtw"] = pd.Series(dtype='float')
data["fv_ventilatie"] = pd.Series(dtype='float')
data["ventilatieverlies"] = pd.Series(dtype='float')
data["infiltratieverlies"] = pd.Series(dtype='float')
data["opwarmtoeslag"] = pd.Series(dtype='float')
data["elektriciteitsvraag_ventilatie"] = pd.Series(dtype='float')

data_copy = data.copy()
####################### LOAD DATASET #############################
####################### HISTOGRAM ###############################
def create_profiel(gevel_opp, vloer_opp, dak_opp, raam_opp, rc_gevel, rc_vloer, rc_dak, u_raam, qi, warmtevoorziening, cop_wp, bh_warmte, eh_warmte, ven_debiet, wtw_toepassen, ren_ww, bh_ven, eh_ven, ontwerp_temp, grond_temp, opwarmtoeslag, simulatieduur):
    bh_opwarmtoeslag = bh_warmte
    eh_opwarmtoeslag = bh_warmte + 2
    
    if warmtevoorziening == "bwp":
        COP = cop_wp
    else:
        COP = 2
        
    laagste_temperatuur = data_copy["temperatuur"].idxmin()
    dag_van_laagste_temperatuur = laagste_temperatuur.date()
    
    if simulatieduur == "jaar":
        data_copy_min = data_copy
    elif simulatieduur == "maand":
        start_dag = laagste_temperatuur.replace(day=1, hour=0, minute=0, second=0)  # First day of the month at 00:00:00
        end_of_month = laagste_temperatuur + pd.DateOffset(months=1)  # This will move you to the 1st day of the next month
        eind_dag = end_of_month.replace(day=1, hour=0, minute=0, second=0) - pd.Timedelta(minutes=15)  # Last time point of the current month
        data_copy_min = data_copy[(data_copy.index >= start_dag) & (data_copy.index <= eind_dag)]
    elif simulatieduur == "week":
        start_dag = laagste_temperatuur.replace(hour=0, minute=0, second=0) - pd.DateOffset(days=laagste_temperatuur.weekday())  # Adjust to Monday of that week
        eind_dag = start_dag + pd.DateOffset(days=7)  # Sunday of the same week
        data_copy_min = data_copy[(data_copy.index >= start_dag) & (data_copy.index < eind_dag)]
    elif simulatieduur == "dag":
        start_dag = laagste_temperatuur.normalize()  # This sets the time to 00:00:00, effectively finding the start of the day
        eind_dag = start_dag + pd.DateOffset(days=1) 
        data_copy_min = data_copy[(data_copy.index >= start_dag) & (data_copy.index < eind_dag)]
    
    T = range(len(data_copy_min.index))
    
    for t in T:
            if data_copy_min["temperatuur"][t] < ontwerp_temp:
                data_copy_min["transmissieverlies_gevel"][t] = ((gevel_opp/rc_gevel)*(ontwerp_temp - data_copy_min["temperatuur"][t]))/1000
                data_copy_min["transmissieverlies_dak"][t] = ((dak_opp/rc_dak)*(ontwerp_temp - data_copy_min["temperatuur"][t]))/1000
                data_copy_min["transmissieverlies_vloer"][t] = ((vloer_opp/rc_vloer)*(ontwerp_temp - grond_temp))/1000
                data_copy_min["transmissieverlies_raam"][t] = ((raam_opp*u_raam)*(ontwerp_temp - data_copy_min["temperatuur"][t]))/1000
            else:
                data_copy_min["transmissieverlies_gevel"][t] = 0
                data_copy_min["transmissieverlies_dak"][t] = 0
                data_copy_min["transmissieverlies_vloer"][t] = 0
                data_copy_min["transmissieverlies_raam"][t] = 0
    
    data_copy_min["transmissieverlies"] = data_copy_min["transmissieverlies_gevel"] + data_copy_min["transmissieverlies_dak"] + data_copy_min["transmissieverlies_vloer"] +data_copy_min["transmissieverlies_raam"]

    data_copy_min["temp_na_wtw"] = ren_ww * (ontwerp_temp - data_copy_min["temperatuur"]) + data_copy_min["temperatuur"]

    for t in T:
        if data_copy_min["temperatuur"][t] < ontwerp_temp:
            data_copy_min["fv_ventilatie"][t] = (ontwerp_temp - data_copy_min["temp_na_wtw"][t])/(ontwerp_temp - data_copy_min["temperatuur"][t])
        else:
            data_copy_min["fv_ventilatie"][t] = 0
            
    data_copy_min["ventilatieverlies"] = (ven_debiet/3600) * 1.2 * 1000 * data_copy_min["fv_ventilatie"] * (ontwerp_temp - data_copy_min["temperatuur"])/1000
    data_copy_min["elektriciteitsvraag_ventilatie"] = (ven_debiet/3600) * 300 / 0.6 / 1000        
    
    for t in T:
        if data_copy_min["temperatuur"][t] < ontwerp_temp:
            data_copy_min["infiltratieverlies"][t] = (qi)*(gevel_opp + raam_opp) * 1000 * 1 * (ontwerp_temp - data_copy_min["temperatuur"][t]) / 1000 * 0.5
        else:
            data_copy_min["infiltratieverlies"][t] = 0

    num_days = (data_copy_min.index.max() - data_copy_min.index.min()).days + 1
    time_steps_per_day = 96
    for day in range(num_days):  # Assuming a non-leap year
                        for t in range(day * time_steps_per_day, (day + 1) * time_steps_per_day):
                    #        # Calculate the current hour (assuming 4 time steps per hour)
                            current_hour = (t % time_steps_per_day) // 4
                    #        # Check if the current time step falls within the specified hours
                            if current_hour < bh_ven:
                                data_copy_min["ventilatieverlies"][t] = 0
                                data_copy_min["elektriciteitsvraag_ventilatie"][t] = 0
                            if current_hour >= eh_ven:
                                data_copy_min["ventilatieverlies"][t] = 0
                                data_copy_min["elektriciteitsvraag_ventilatie"][t] = 0
                            if bh_opwarmtoeslag <= current_hour < eh_opwarmtoeslag:
                                data_copy_min["opwarmtoeslag"][t] = (vloer_opp * opwarmtoeslag)/1000
                            else:
                                data_copy_min["opwarmtoeslag"][t] = 0
                            if current_hour < bh_warmte:
                                data_copy_min["transmissieverlies"][t] = 0
                                data_copy_min["ventilatieverlies"][t] = 0
                                data_copy_min["infiltratieverlies"][t] = 0
                                data_copy_min["opwarmtoeslag"][t] = 0
                            if current_hour >= eh_warmte:
                                data_copy_min["transmissieverlies"][t] = 0
                                data_copy_min["ventilatieverlies"][t] = 0
                                data_copy_min["infiltratieverlies"][t] = 0
                                data_copy_min["opwarmtoeslag"][t] = 0
    
    # Extract the day of the week and add it as a column
    data_copy_min['Day of the Week'] = data_copy_min.index.day_name()
    weekend_mask = data_copy_min['Day of the Week'] .isin(['Saturday', 'Sunday'])
    columns_to_update = ["elektriciteitsvraag_ventilatie", "opwarmtoeslag", "transmissieverlies", "ventilatieverlies", "infiltratieverlies"]
    data_copy_min.loc[weekend_mask, columns_to_update] = 0
    
    data_copy_min["warmteverlies_totaal"] = data_copy_min["transmissieverlies"] + data_copy_min["ventilatieverlies"] + data_copy_min["infiltratieverlies"] + data_copy_min["opwarmtoeslag"]
    data_copy_min["elektriciteitsvraag_warmte"] = data_copy_min["warmteverlies_totaal"]/COP
    data_copy_min["elektriciteitsvraag_warmte_ventilatie_totaal"] = data_copy_min["elektriciteitsvraag_warmte"] + data_copy_min["elektriciteitsvraag_ventilatie"]
    
    #Dataframe
    piek_warmte_ventilatie = data_copy_min["elektriciteitsvraag_warmte_ventilatie_totaal"].idxmax()
    start_date = piek_warmte_ventilatie.normalize()
    eind_date = start_date + pd.DateOffset(days=1) 

    max_value_warmtevraag = round(data_copy_min["elektriciteitsvraag_warmte_ventilatie_totaal"].max())
    max_index_warmtevraag = data_copy_min["elektriciteitsvraag_warmte_ventilatie_totaal"].idxmax()
    
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
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["transmissieverlies"]/COP, fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = blauw, name = 'Transmissieverlies'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["ventilatieverlies"]/COP, fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = lichtblauw, name = 'Ventilatieverlies'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["infiltratieverlies"]/COP, fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = oranje, name = 'Transmissieverlies'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["opwarmtoeslag"]/COP, fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = groen, name = 'Opwarmtoeslag'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["elektriciteitsvraag_warmte"] , mode = 'lines', line=dict(color='black', dash = "dash"), name = 'Warmtevoorziening totaal'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["elektriciteitsvraag_ventilatie"], fill = 'tonexty', mode = 'none', stackgroup = 'one', fillcolor = blauw_l, name = 'Ventilatie'))
    fig.add_trace(go.Scatter(x = data_copy_min.index, y = data_copy_min["elektriciteitsvraag_warmte_ventilatie_totaal"] , mode = 'lines', line=dict(color='black'), name = 'Totaal'))
    
    fig.update_layout(
                title = dict(
                    text="Elektriciteitsprofiel warmtevoorziening en ventilatie",
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
    data_json = data_copy_min.to_json(date_format='iso', orient='split')
    return fig, data_json

####################### WIDGETS ################################
button = html.Button(
                        "Klik om een elektriciteitsprofiel voor de warmtevoorziening en ventilatie te genereren",
                        id=ids.BUTTON_FIGUUR_WARMTE_VENTILATIE,
                        n_clicks=0,
                        className="button",
                        style={'width': '100%', 'display': 'block'} 
                    )


##Bouwkundigde uitgangspunten
#Oppervlaktes
geveloppervlakte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Geveloppervlakte: ", style={"display": "inline-block", "margin-right": "10px", "width": "125px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.GEVELOPPERVLAKTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=1345,
                    min=0,
                    max=50000,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

vloeroppervlakte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Vloeroppervlakte: ", style={"display": "inline-block", "margin-right": "10px", "width": "125px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.VLOEROPPERVLAKTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=1833,
                    min=0,
                    max=50000,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

dakoppervlakte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Dakoppervlakte: ", style={"display": "inline-block", "margin-right": "10px", "width": "125px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.DAKOPPERVLAKTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=1930,
                    min=0,
                    max=50000,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

raamoppervlakte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Raamoppervlakte: ", style={"display": "inline-block", "margin-right": "10px", "width": "125px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.RAAMOPPERVLAKTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=400,
                    min=0,
                    max=50000,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

#Isolatiewaarden
rc_gevel_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Rc-waarde gevel: ", style={"display": "inline-block", "margin-right": "10px", "width": "130px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.RC_GEVEL_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=2.9,
                    min=0,
                    max=10,
                    step=0.1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "80px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²K/W", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

rc_vloer_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Rc-waarde vloer: ", style={"display": "inline-block", "margin-right": "10px", "width": "130px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.RC_VLOER_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=2.0,
                    min=0,
                    max=10,
                    step=0.1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "80px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²K/W", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

rc_dak_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Rc-waarde dak: ", style={"display": "inline-block", "margin-right": "10px", "width": "130px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.RC_DAK_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=4.3,
                    min=0,
                    max=10,
                    step=0.1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "80px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m²K/W", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

u_raam_input_box = html.Div(
        children=[
            html.Div([
                html.H6("U-waarde raam: ", style={"display": "inline-block", "margin-right": "10px", "width": "130px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.U_RAAM_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=4.3,
                    min=0,
                    max=10,
                    step=0.1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "80px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" W/(m²K)", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

qi_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Infiltratiedebiet qi: ", style={"display": "inline-block", "margin-right": "10px", "width": "130px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.QI_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=0.00175,
                    min=0,
                    max=1,
                    step=0.00005,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "80px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" dm³/(s*m²)", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

##Installatietechnische uitgangspunten
#Warmtevoorziening
warmtevoorziening_dropdown_box = html.Div(
        children=[
            html.Div([
                html.H6("Type warmtevoorziening: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),
                dcc.Dropdown(
                    className = "dropdown-box",
                    id=ids.WARMTEVOORZIENING_DROPDOWN,
                    options=[
                        {'label': 'Bodemwarmtepomp', 'value': 'bwp'},
                        {'label': 'Luchtwarmtepomp', 'value': 'lwp'},
                    ],
                    value = "bwp",
                    placeholder="Selecteer een optie...",
                    clearable = True,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "190px", "text-align": "left"}  # Adjust alignment and display
                ),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

cop_warmtepomp_input_placeholder = html.Div(id=ids.COP_WARMTEPOMP_INPUT_DUMMY)

@callback(Output(ids.COP_WARMTEPOMP_INPUT_DUMMY, "children"), [Input(ids.WARMTEVOORZIENING_DROPDOWN, "value"), ])
def update_cop_box(warmtevoorziening):
    if warmtevoorziening == "bwp":
        return html.Div(
                children=[
                    html.Div([
                        html.H6("COP warmtepomp: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                        dcc.Input(
                            className = "input-box",
                            id=ids.COP_WARMTEPOMP_INPUT,
                            type="number",
                            placeholder="input with range",
                            value=5,
                            min=1,
                            max=10,
                            step=0.1,
                            style={"display": "inline-block", "vertical-align": "middle", "width": "50px", "text-align": "right"}  # Adjust alignment and display
                        ),
                        html.H6(" ", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
                    ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
                ]
            )
    else:
        return html.Div(id = ids.COP_WARMTEPOMP_INPUT)

bh_warmte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Start verwarming: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.BH_WARMTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=7,
                    min=1,
                    max=14,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "40px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(":00", style={"display": "inline-block", "margin-left": "0px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

eh_warmte_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Eind verwarming: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.EH_WARMTE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=17,
                    min=15,
                    max=23,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "40px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(":00", style={"display": "inline-block", "margin-left": "0px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

#Ventilatie
ventilatiedebiet_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Ventilatiedebiet: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.VENTILATIEDEBIET_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=19230,
                    min=100,
                    max=1000000,
                    step=10,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "70px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" m³/h", style={"display": "inline-block", "margin-left": "0px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

wtw_dropdown_box = html.Div(
        children=[
            html.Div([
                html.H6("Warmteterugwinning toepassen?: ", style={"display": "inline-block", "margin-right": "10px", "width": "240px"}),
                dcc.Dropdown(
                    className = "dropdown-box",
                    id=ids.WTW_DROPDOWN,
                    options=[
                        {'label': 'Ja', 'value': 'wtw_ja'},
                        {'label': 'Nee', 'value': 'wtw_nee'},
                    ],
                    value = "wtw_ja",
                    placeholder="Selecteer een optie...",
                    clearable = True,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "190px", "text-align": "left"}  # Adjust alignment and display
                ),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

rendement_warmtewiel_input_placeholder = html.Div(id=ids.RENDEMENT_WARMTEWIEL_INPUT_DUMMY)

@callback(Output(ids.RENDEMENT_WARMTEWIEL_INPUT_DUMMY, "children"), [Input(ids.WTW_DROPDOWN, "value"), ])
def update_rendement_warmtewiel(wtw):
    if wtw == "wtw_ja":
        return html.Div(
                children=[
                    html.Div([
                        html.H6("Rendement warmtewiel: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                        dcc.Input(
                            className = "input-box",
                            id=ids.RENDEMENT_WARMTEWIEL_INPUT,
                            type="number",
                            placeholder="input with range",
                            value=0.75,
                            min=0.1,
                            max=1,
                            step=0.01,
                            style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                        ),
                        html.H6(" ", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
                    ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
                ]
            )
    else:
        # Set ren_ww to 0 or another default value when WTW is not applied
        return html.Div([
            dcc.Input(
                style={'display': 'none'},
                id=ids.RENDEMENT_WARMTEWIEL_INPUT,
                value=0  # default value when no WTW is applied
            )
        ])

bh_ventilatie_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Start ventilatie: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.BH_VENTILATIE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=7,
                    min=1,
                    max=14,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "40px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(":00", style={"display": "inline-block", "margin-left": "0px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

eh_ventilatie_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Eind ventilatie: ", style={"display": "inline-block", "margin-right": "10px", "width": "180px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.EH_VENTILATIE_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=17,
                    min=15,
                    max=23,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "40px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(":00", style={"display": "inline-block", "margin-left": "0px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )


##Bouwkundigde uitgangspunten
#Oppervlaktes
ontwerptemperatuur_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Ontwerptemperatuur: ", style={"display": "inline-block", "margin-right": "10px", "width": "210px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.ONTWERPTEMPERATUUR_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=20,
                    min=10,
                    max=30,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" °C", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

grondtemperatuur_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Grondtemperatuur: ", style={"display": "inline-block", "margin-right": "10px", "width": "210px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.GRONDTEMPERATUUR_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=10,
                    min=5,
                    max=20,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" °C", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

opwarmtoeslag_input_box = html.Div(
        children=[
            html.Div([
                html.H6("Opwarmtoeslag: ", style={"display": "inline-block", "margin-right": "10px", "width": "210px"}),  # Added margin for spacing
                dcc.Input(
                    className = "input-box",
                    id=ids.OPWARMTOESLAG_INPUT,
                    type="number",
                    placeholder="input with range",
                    value=10,
                    min=1,
                    max=100,
                    step=1,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "60px", "text-align": "right"}  # Adjust alignment and display
                ),
                html.H6(" W/m²", style={"display": "inline-block", "margin-left": "10px", "width": "20px"}),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

jaar_maand_week_dag_dropdown_box = html.Div(
        children=[
            html.Div([
                html.H6("Simulatieduur: ", style={"display": "inline-block", "margin-right": "10px", "width": "210px"}),
                dcc.Dropdown(
                    className = "dropdown-box",
                    id=ids.JAAR_MAAND_WEEK_DAG_DROPDOWN,
                    options=[
                        {'label': 'Jaar', 'value': 'jaar'},
                        {'label': 'Maand', 'value': 'maand'},
                        {'label': 'Week', 'value': 'week'},
                        {'label': 'Dag', 'value': 'dag'},
                    ],
                    value = "dag",
                    placeholder="Selecteer een optie...",
                    clearable = True,
                    style={"display": "inline-block", "vertical-align": "middle", "width": "190px", "text-align": "left"}  # Adjust alignment and display
                ),  # Added margin for spacing and adjusted alignment
            ], style={'display': "inline-block", 'align-items': 'center'}),  # Ensure alignment of all items
        ]
    )

##BOXES
bouwkundige_uitgangspunten_box = dbc.Col(
    [
        html.Div([
            html.Div([
                html.H4("Bouwkundige uitgangspunten", className="mb-2"),
            ],style={'padding': '10px', 'border-radius': '5px', 'margin-bottom': '0px'}),
        ], style={'margin': '0 15px'}),# Heading above the box, added bottom margin for spacing
        html.Div([  # This Div contains the content of the box with borders and styling
            html.Div([
                html.H5("Oppervlaktes"),
                html.Hr(),
                geveloppervlakte_input_box,
                vloeroppervlakte_input_box,
                dakoppervlakte_input_box,
                raamoppervlakte_input_box,
                html.Hr(),
                html.H5("Isolatiewaardes"),
                html.Hr(),
                rc_gevel_input_box,
                rc_vloer_input_box,
                rc_dak_input_box,
                u_raam_input_box,
                qi_input_box,
            ], style={'border': '3px solid #ddd', 'padding': '10px', 'border-radius': '5px'}),
        ], style={'margin-top': '0px', 'margin-bottom': '15px', 'margin-left': '15px', 'margin-right': '15px'}),
    ],
    md=4, 
    className="box-inputs"
)

installatietechnische_uitgangspunten_box = dbc.Col(
    [
        html.Div([
            html.Div([
                html.H4("Installatietechnische uitgangspunten", className="mb-2"),
            ],style={'padding': '10px', 'border-radius': '5px', 'margin-bottom': '0px'}),
        ], style={'margin': '0 15px'}),# Heading above the box, added bottom margin for spacing
        html.Div([  # This Div contains the content of the box with borders and styling
            html.Div([
                html.H5("Warmtevoorziening"),
                html.Hr(),
                warmtevoorziening_dropdown_box,
                cop_warmtepomp_input_placeholder,
                bh_warmte_input_box,
                eh_warmte_input_box,
                html.Hr(),
                html.H5("Ventilatie"),
                html.Hr(),
                ventilatiedebiet_input_box,
                bh_ventilatie_input_box,
                eh_ventilatie_input_box,
                wtw_dropdown_box,
                rendement_warmtewiel_input_placeholder,
                html.Hr(),
            ], style={'border': '3px solid #ddd', 'padding': '10px', 'border-radius': '5px'}),
        ], style={'margin-top': '0px', 'margin-bottom': '15px', 'margin-left': '15px', 'margin-right': '15px'}),
    ],
    md=4, 
    className="box-inputs"
)

ontwerp_uitgangspunten_box = dbc.Col(
    [
        html.Div([
            html.Div([
                html.H4("Overige uitgangspunten", className="mb-2"),
            ],style={'padding': '10px', 'border-radius': '5px', 'margin-bottom': '0px'}),
        ], style={'margin': '0 15px'}),# Heading above the box, added bottom margin for spacing
        html.Div([  # This Div contains the content of the box with borders and styling
            html.Div([
                html.H5("Ontwerpuitgangspunten"),
                html.Hr(),
                ontwerptemperatuur_input_box,
                grondtemperatuur_input_box,
                opwarmtoeslag_input_box,
                html.Hr(),
                html.H5("Uitgangspunten simulatie"),
                html.Hr(),
                jaar_maand_week_dag_dropdown_box,
            ], style={'border': '3px solid #ddd', 'padding': '10px', 'border-radius': '5px'}),
        ], style={'margin-top': '0px', 'margin-bottom': '15px', 'margin-left': '15px', 'margin-right': '15px'}),
    ],
    md=4, 
    className="box-inputs"
)


####################### PAGE LAYOUT #############################
layout = html.Div(className = "app-div", children=[
    dbc.Row([
        dbc.Col(
        html.H1("Merosch Netcongestie Model - versie 0.1", style={'text-align': 'center', 'margin': 'auto'}), width=9),
        dbc.Col(html.Img(src='assets/Logo-Merosch_liggend_RGB.png', alt='image', style={'height':'75%', 'width':'75%'}))
            ]),
    html.Hr(),
    dbc.Row([  # This row contains both boxes
                bouwkundige_uitgangspunten_box,
                installatietechnische_uitgangspunten_box,
                ontwerp_uitgangspunten_box,
            ]),
    html.Hr(),
    button,
    html.Hr(),
    html.Div(id="graph-container", style={'display': 'none'}, children=[
        dcc.Graph(id=ids.ELEKTRICITEITSPROFIEL_WARMTEVOORZIENING)
    ])
    #dcc.Graph(id=ids.ELEKTRICITEITSPROFIEL_WARMTEVOORZIENING)
])

####################### CALLBACKS ################################
@callback(
    [Output(ids.ELEKTRICITEITSPROFIEL_WARMTEVOORZIENING, 'figure'),
     Output('data-store-warmte-ventilatie', 'data')],
    [Input(ids.BUTTON_FIGUUR_WARMTE_VENTILATIE, 'n_clicks')],
    [State(ids.GEVELOPPERVLAKTE_INPUT, 'value'),
     State(ids.VLOEROPPERVLAKTE_INPUT, 'value'),
     State(ids.DAKOPPERVLAKTE_INPUT, 'value'),
     State(ids.RAAMOPPERVLAKTE_INPUT, 'value'),
     State(ids.RC_GEVEL_INPUT, 'value'),
     State(ids.RC_VLOER_INPUT, 'value'),
     State(ids.RC_DAK_INPUT, 'value'),
     State(ids.U_RAAM_INPUT, 'value'),
     State(ids.QI_INPUT, 'value'),
     State(ids.WARMTEVOORZIENING_DROPDOWN, 'value'),
     State(ids.COP_WARMTEPOMP_INPUT, 'value'),
     State(ids.BH_WARMTE_INPUT, 'value'),
     State(ids.EH_WARMTE_INPUT, 'value'),
     State(ids.VENTILATIEDEBIET_INPUT, 'value'),
     State(ids.WTW_DROPDOWN, 'value'),  # Ensure this matches the ID used in the layout
     State(ids.RENDEMENT_WARMTEWIEL_INPUT, 'value'),  # Ensure this matches the ID used in the layout
     State(ids.BH_VENTILATIE_INPUT, 'value'),
     State(ids.EH_VENTILATIE_INPUT, 'value'),
     State(ids.ONTWERPTEMPERATUUR_INPUT, 'value'),
     State(ids.GRONDTEMPERATUUR_INPUT, 'value'),
     State(ids.OPWARMTOESLAG_INPUT, 'value'),
     State(ids.JAAR_MAAND_WEEK_DAG_DROPDOWN, 'value')]
)
def update_profiel(nclicks, gevel_opp, vloer_opp, dak_opp, raam_opp, rc_gevel, rc_vloer, rc_dak, u_raam, qi, warmtevoorziening, cop_wp, bh_warmte, eh_warmte, ven_debiet, wtw_toepassen, ren_ww, bh_ven, eh_ven, ontwerp_temp, grond_temp, opwarmtoeslag, simulatieduur):
    if nclicks is None or nclicks == 0:
        raise PreventUpdate
    return create_profiel(gevel_opp, vloer_opp, dak_opp, raam_opp, rc_gevel, rc_vloer, rc_dak, u_raam, qi, warmtevoorziening, cop_wp, bh_warmte, eh_warmte, ven_debiet, wtw_toepassen, ren_ww, bh_ven, eh_ven, ontwerp_temp, grond_temp, opwarmtoeslag, simulatieduur)
           
@callback(
    Output('graph-container', 'style'),
    Input(ids.BUTTON_FIGUUR_WARMTE_VENTILATIE, 'n_clicks'),
    Input(ids.WARMTEVOORZIENING_DROPDOWN, 'value'),
    Input(ids.WTW_DROPDOWN, 'value'),
    Input(ids.JAAR_MAAND_WEEK_DAG_DROPDOWN, 'value')
)
def display_graph(n_clicks, warmtevoorziening, wtw_toepassen, simulatieduur):
    if n_clicks and n_clicks > 0 and warmtevoorziening is not None and wtw_toepassen is not None and simulatieduur is not None:
        return {'display': 'block'}  # Makes the graph visible
    return {'display': 'none'}  # Keeps the graph hidden initially

