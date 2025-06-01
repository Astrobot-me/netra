import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input
import datetime

# --- 1. Generate Dummy Data ---
def generate_dummy_data(num_crossroads=5, duration_hours=48, interval_minutes=10):
    data = []
    start_time = datetime.datetime.now() - datetime.timedelta(hours=duration_hours)
    time_points = pd.date_range(start=start_time, periods=int(duration_hours * 60 / interval_minutes), freq=f'{interval_minutes}min')

    daily_accidents = {}
    # Track ongoing major incidents for each crossroad
    ongoing_incidents = {crossroad_id: {'active': False, 'end_time': None, 'incident_level': 0}
                         for crossroad_id in [f"Crossroad {chr(65 + i)}" for i in range(num_crossroads)]}


    for i in range(num_crossroads):
        crossroad_id = f"Crossroad {chr(65 + i)}"
        base_vehicles = np.random.randint(50, 200)

        daily_accidents[crossroad_id] = {}

        for t in time_points:
            vehicle_count = max(0, base_vehicles + np.random.randint(-30, 50) +
                                  (np.sin(t.hour / 24 * 2 * np.pi) * 100))

            emergency_vehicles = np.random.randint(0, 2) # Base 0 or 1

            # --- Simulate Accidents per Day ---
            current_day = t.date()
            if current_day not in daily_accidents[crossroad_id]:
                # Generate accidents for the day once
                daily_accidents[crossroad_id][current_day] = np.random.choice([0, 1, 2, 3], p=[0.6, 0.25, 0.1, 0.05]) # Increased chance for some accidents


            accidents_today = daily_accidents[crossroad_id][current_day]

            # --- Major Incident Logic ---
            if not ongoing_incidents[crossroad_id]['active']:
                # Chance to start a major incident (e.g., 0.5% chance per time interval)
                if np.random.rand() < 0.005: # Low probability for a major incident
                    ongoing_incidents[crossroad_id]['active'] = True
                    # Incident lasts for 30-90 minutes (3 to 9 intervals)
                    incident_duration = np.random.randint(3, 10) * interval_minutes
                    ongoing_incidents[crossroad_id]['end_time'] = t + datetime.timedelta(minutes=incident_duration)
                    # High emergency vehicle count during major incident
                    ongoing_incidents[crossroad_id]['incident_level'] = np.random.randint(10, 31)
            else:
                # If incident is active, check if it has ended
                if t >= ongoing_incidents[crossroad_id]['end_time']:
                    ongoing_incidents[crossroad_id]['active'] = False
                    ongoing_incidents[crossroad_id]['incident_level'] = 0


            if ongoing_incidents[crossroad_id]['active']:
                emergency_vehicles = ongoing_incidents[crossroad_id]['incident_level']
            else:
                # Regular emergency vehicle presence if no major incident
                if np.random.rand() < 0.2:
                    emergency_vehicles += np.random.randint(1, 3)
                if np.random.rand() < 0.05:
                    emergency_vehicles += np.random.randint(2, 5)
                emergency_vehicles = min(emergency_vehicles, 5) # Cap regular presence at 5

            # If accidents occurred on that day, and emergency vehicles are low,
            # slightly boost them to indicate ongoing response for non-major incidents.
            if accidents_today > 0 and emergency_vehicles < 5 and not ongoing_incidents[crossroad_id]['active']:
                emergency_vehicles = min(emergency_vehicles + np.random.randint(1, 3), 5)


            data.append({
                'timestamp': t,
                'crossroad_id': crossroad_id,
                'vehicle_count': int(vehicle_count),
                'emergency_vehicles': int(emergency_vehicles),
                'accidents_today': int(accidents_today)
            })
    return pd.DataFrame(data)

df = generate_dummy_data()

# --- 2. Initialize Dash App ---
app = Dash(__name__)
server = app.server

# --- 3. Custom HTML Template ---
app.index_string = '''
<!DOCTYPE html>
<html lang="en">
<head>
    {%metas%}
    <title>🚦 Crossroads Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    {%favicon%}
    {%css%}
    <style>
        body {
            font-family: 'Orbitron', sans-serif;
            background: linear-gradient(to bottom right, #0f172a, #1e293b);
            color: #f8fafc;
            overflow-x: hidden;
        }
        .glass {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        .dropdown-wrapper {
            z-index: 10;
            position: relative;
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''

# --- 4. Layout ---
app.layout = html.Div(
    className='px-6 py-10 space-y-12',
    children=[
        html.Div(
            className='flex items-center justify-between text-center',
            children=[
                html.Div(
                    className='flex items-center space-x-2',
                    children=[
                        html.Span("👤", className='text-3xl'), # Profile icon
                        html.P("Vaishali Tiwari", className='text-lg font-semibold text-gray-300')
                    ]
                ),
                html.Div(
                    className='flex-grow text-center',
                    children=[
                        html.H1("🚦 Crossroads Traffic Dashboard", className='text-5xl font-bold text-cyan-400'),
                        html.P("Real-time insights into traffic, emergency patterns, and daily incidents",
                               className='text-gray-400 mt-2 text-lg')
                    ]
                ),
                 html.Div(className='w-48') # Placeholder to balance the layout
            ]
        ),

        html.Div(
            className='grid grid-cols-1 md:grid-cols-4 gap-6 relative',
            children=[
                html.Div(
                    className='glass p-6 rounded-2xl shadow-lg dropdown-wrapper',
                    children=[
                        html.H2("📍 Select Crossroad", className='text-lg font-semibold text-white mb-3'),
                        dcc.Dropdown(
                            id='crossroad-dropdown',
                            options=[{'label': i, 'value': i} for i in df['crossroad_id'].unique()],
                            value=df['crossroad_id'].unique()[0],
                            clearable=False,
                            className='text-black'
                        )
                    ]
                ),
                html.Div(
                    id='current-data-card',
                    className='md:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6 z-0'
                )
            ]
        ),

        html.Div(
            className='glass p-6 rounded-2xl shadow-lg relative z-0',
            children=[
                html.H2("📈 Traffic & Emergency Trends", className='text-lg font-semibold text-white mb-4'),
                dcc.Loading(
                    type="circle",
                    children=dcc.Graph(id='time-series-graph', className='w-full h-[500px]')
                )
            ]
        )
    ]
)

# --- 5. Callbacks ---
@callback(
    Output('current-data-card', 'children'),
    Input('crossroad-dropdown', 'value')
)
def update_current_data_card(selected_crossroad):
    filtered_df = df[df['crossroad_id'] == selected_crossroad]
    if filtered_df.empty:
        return html.Div("No data available.", className='text-red-500 text-center py-4')

    latest = filtered_df.sort_values(by='timestamp', ascending=False).iloc[0]

    accidents_for_today = latest['accidents_today']
    current_emergency_vehicles = latest['emergency_vehicles']

    # --- Logical Comparison Logic ---
    insight_text = ""
    insight_color = "text-gray-400" # Default color

    if accidents_for_today > 0:
        if current_emergency_vehicles >= 10: # High threshold for major incident response
            insight_text = "Major Incident Response Underway!"
            insight_color = "text-red-500"
        elif current_emergency_vehicles >= 3:
            insight_text = "Active Emergency Response to Accidents."
            insight_color = "text-orange-400"
        else:
            insight_text = "Accident Reported, Monitoring Situation."
            insight_color = "text-yellow-500"
    elif current_emergency_vehicles >= 10: # High threshold for major incident response (non-accident)
        insight_text = "Significant Emergency Activity (Non-Accident)."
        insight_color = "text-purple-400"
    elif current_emergency_vehicles >= 3:
        insight_text = "Elevated Emergency Presence."
        insight_color = "text-blue-400"
    else:
        insight_text = "Traffic Flow Normal. No Incidents."
        insight_color = "text-green-400"


    return [
        html.Div(
            className='glass p-6 rounded-xl text-center shadow-lg',
            children=[
                html.P("🚗 Current Vehicles", className='text-sm text-gray-300'),
                html.P(f"{latest['vehicle_count']}", className='text-5xl font-bold text-cyan-400')
            ]
        ),
        html.Div(
            className='glass p-6 rounded-xl text-center shadow-lg',
            children=[
                html.P("🚑 Emergency Vehicles", className='text-sm text-gray-300'),
                html.P(f"{current_emergency_vehicles}", className='text-5xl font-bold text-rose-400')
            ]
        ),
        html.Div(
            className='glass p-6 rounded-xl text-center shadow-lg',
            children=[
                html.P("💥 Accidents Today", className='text-sm text-gray-300'),
                html.P(f"{accidents_for_today}", className='text-5xl font-bold text-yellow-400')
            ]
        ),
        html.Div(
            className='glass p-6 rounded-xl text-center shadow-lg md:col-span-3',
            children=[
                html.P("🚨 Incident Insight", className='text-sm text-gray-300 mb-2'),
                html.P(insight_text, className=f'text-3xl font-bold {insight_color}')
            ]
        )
    ]

@callback(
    Output('time-series-graph', 'figure'),
    Input('crossroad-dropdown', 'value')
)
def update_graph(selected_crossroad):
    filtered_df = df[df['crossroad_id'] == selected_crossroad].sort_values(by='timestamp')

    fig = px.line(
        filtered_df,
        x='timestamp',
        y=['vehicle_count', 'emergency_vehicles'],
        title=f'Traffic & Emergency Trends for {selected_crossroad}',
        labels={'timestamp': 'Time', 'value': 'Count', 'variable': 'Metric'},
        line_shape='spline',
        template='plotly_dark',
        color_discrete_map={
            'vehicle_count': '#0ea5e9',
            'emergency_vehicles': '#fb7185'
        }
    )

    fig.update_layout(
        font=dict(family="Orbitron", size=14, color='#e2e8f0'),
        title_font_size=22,
        title_x=0.5,
        plot_bgcolor='#0f172a',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="x unified",
        legend_title_text='Metric',
        legend_orientation="h",
        legend_x=0.5,
        legend_xanchor="center",
        legend_y=-0.2,
        hoverlabel=dict(bgcolor="#1e293b", font_size=14, font_family="Orbitron")
    )
    fig.update_xaxes(showgrid=True, gridcolor='#334155', linecolor='#64748b', title_font_color='#94a3b8')
    fig.update_yaxes(showgrid=True, gridcolor='#334155', linecolor='#64748b', title_font_color='#94a3b8')

    return fig

# --- 6. Run App ---
if __name__ == '__main__':
    app.run(debug=True)