import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
import datetime
import random

# --- 1. Generate Dummy Data ---
def generate_dummy_data(num_crossroads=5):
    """Generates dummy data for vehicle counts and emergency vehicles."""
    crossroads = [f"CR{i+1}" for i in range(num_crossroads)]
    data = []
    for cr in crossroads:
        vehicles = random.randint(50, 200)
        emergency = random.randint(0, min(5, vehicles // 10)) # Max 5 emergency vehicles
        data.append({
            'crossroad_id': cr,
            'vehicles_present': vehicles,
            'active_emergency_vehicles': emergency
        })
    return pd.DataFrame(data)

# Initialize historical data for the time-series graph
time_series_data = pd.DataFrame(columns=['timestamp', 'total_vehicles'])

# --- 2. Create Dash App ---
app = dash.Dash(__name__)

# --- 3. Define Layout ---
app.layout = html.Div(
    style={'fontFamily': 'Inter, sans-serif', 'backgroundColor': '#f0f2f5', 'padding': '20px'},
    children=[
        html.H1(
            "Crossroads Traffic Dashboard",
            style={'textAlign': 'center', 'color': '#333', 'marginBottom': '30px'}
        ),

        html.Div(
            style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '40px'},
            children=[
                html.Div(
                    id='total-vehicles-card',
                    style={
                        'backgroundColor': '#ffffff', 'padding': '25px', 'borderRadius': '12px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.08)', 'textAlign': 'center',
                        'flex': '1', 'marginRight': '20px', 'maxWidth': '450px'
                    },
                    children=[
                        html.H2("Total Vehicles", style={'color': '#555', 'fontSize': '1.5em'}),
                        html.P("Loading...", id='total-vehicles-value', style={'fontSize': '2.5em', 'fontWeight': 'bold', 'color': '#007bff'})
                    ]
                ),
                html.Div(
                    id='emergency-vehicles-card',
                    style={
                        'backgroundColor': '#ffffff', 'padding': '25px', 'borderRadius': '12px',
                        'boxShadow': '0 4px 12px rgba(0,0,0,0.08)', 'textAlign': 'center',
                        'flex': '1', 'maxWidth': '450px'
                    },
                    children=[
                        html.H2("Active Emergency Vehicles", style={'color': '#555', 'fontSize': '1.5em'}),
                        html.P("Loading...", id='emergency-vehicles-value', style={'fontSize': '2.5em', 'fontWeight': 'bold', 'color': '#dc3545'})
                    ]
                ),
            ]
        ),

        html.Div(
            style={
                'backgroundColor': '#ffffff', 'padding': '25px', 'borderRadius': '12px',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.08)', 'marginBottom': '40px'
            },
            children=[
                html.H2("Vehicles at Crossroads (Current Snapshot)", style={'color': '#555', 'textAlign': 'center'}),
                dcc.Graph(id='crossroads-bar-chart')
            ]
        ),

        html.Div(
            style={
                'backgroundColor': '#ffffff', 'padding': '25px', 'borderRadius': '12px',
                'boxShadow': '0 4px 12px rgba(0,0,0,0.08)'
            },
            children=[
                html.H2("Total Vehicles Over Time", style={'color': '#555', 'textAlign': 'center'}),
                dcc.Graph(id='time-series-graph')
            ]
        ),

        # Interval component to update data every 5 seconds
        dcc.Interval(
            id='interval-component',
            interval=5*1000, # in milliseconds
            n_intervals=0
        )
    ]
)

# --- 4. Implement Callbacks ---

@app.callback(
    [Output('total-vehicles-value', 'children'),
     Output('emergency-vehicles-value', 'children'),
     Output('crossroads-bar-chart', 'figure')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics_and_bar_chart(n):
    """Updates the total vehicle counts, emergency vehicle counts, and the bar chart."""
    df = generate_dummy_data()

    total_vehicles = df['vehicles_present'].sum()
    total_emergency_vehicles = df['active_emergency_vehicles'].sum()

    # Create bar chart for current snapshot
    bar_fig = go.Figure(data=[
        go.Bar(
            x=df['crossroad_id'],
            y=df['vehicles_present'],
            marker_color='#28a745', # Green color for vehicles
            name='Vehicles Present'
        ),
        go.Bar(
            x=df['crossroad_id'],
            y=df['active_emergency_vehicles'],
            marker_color='#dc3545', # Red color for emergency vehicles
            name='Emergency Vehicles'
        )
    ])
    bar_fig.update_layout(
        barmode='stack', # Stack bars for better comparison
        xaxis_title="Crossroad ID",
        yaxis_title="Number of Vehicles",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='#333',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.7)', bordercolor='rgba(0,0,0,0.1)', borderwidth=1),
        hovermode="x unified"
    )

    return total_vehicles, total_emergency_vehicles, bar_fig

@app.callback(
    Output('time-series-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_time_series_graph(n):
    """Updates the time-series graph with new data points."""
    global time_series_data # Access the global DataFrame

    current_data = generate_dummy_data()
    current_total_vehicles = current_data['vehicles_present'].sum()
    current_timestamp = datetime.datetime.now()

    # Append new data point
    new_row = pd.DataFrame([{'timestamp': current_timestamp, 'total_vehicles': current_total_vehicles}])
    time_series_data = pd.concat([time_series_data, new_row], ignore_index=True)

    # Keep only the last 20 data points for better visualization
    if len(time_series_data) > 20:
        time_series_data = time_series_data.tail(20).reset_index(drop=True)

    # Create time-series plot
    time_series_fig = go.Figure(data=[
        go.Scatter(
            x=time_series_data['timestamp'],
            y=time_series_data['total_vehicles'],
            mode='lines+markers',
            name='Total Vehicles',
            line=dict(color='#007bff', width=3),
            marker=dict(size=8, color='#007bff', symbol='circle', line=dict(width=1, color='DarkSlateGrey'))
        )
    ])
    time_series_fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Total Vehicles Present",
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_color='#333',
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )

    return time_series_fig

# --- 5. Run the App ---
if __name__ == '__main__':
    app.run_server(debug=True)
