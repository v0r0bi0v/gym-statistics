import dash
from dash import dcc, html, Input, Output, callback, clientside_callback
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os

# Инициализация приложения с темной темой
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)
server = app.server

# Кастомные стили для темной темы
app.layout = dbc.Container([
    # Стили для выпадающих списков
    html.Div(style={
        'color': 'white',
        'backgroundColor': '#303030'
    }),
    
    html.H1("Анализ тренировок", className="mb-4", style={'color': 'white'}),
    
    dbc.Row([
        dbc.Col([
            html.Label("Выберите пользователя:", style={'color': 'white'}),
            dcc.Dropdown(
                id='user-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={
                    'backgroundColor': '#303030',
                    'color': 'white',
                    'border': '1px solid #555'
                }
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите мышечную группу:", style={'color': 'white'}),
            dcc.Dropdown(
                id='muscle-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={
                    'backgroundColor': '#303030',
                    'color': 'white',
                    'border': '1px solid #555'
                }
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите упражнение:", style={'color': 'white'}),
            dcc.Dropdown(
                id='exercise-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={
                    'backgroundColor': '#303030',
                    'color': 'white',
                    'border': '1px solid #555'
                }
            )
        ], width=3)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='progress-graph',
                config={'displayModeBar': True},
                style={'height': '70vh'}
            )
        ], width=12)
    ])
], fluid=True, style={'backgroundColor': '#222', 'padding': '20px'})

# Callback для обновления данных
@callback(
    Output('user-dropdown', 'options'),
    Output('user-dropdown', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_data(n_intervals):
    df = pd.read_csv("workouts.csv")
    df['date'] = pd.to_datetime(df['date'])
    user_options = [{'label': user, 'value': user} for user in df['user_id'].unique()]
    return user_options, user_options[0]['value'] if user_options else None

# Остальные callback'и (аналогичные предыдущим)
# ...

# Настройка темного оформления графиков
def create_dark_figure(df, selected_user, selected_muscle, selected_exercise):
    filtered_df = df[(df['user_id'] == selected_user) & 
                    (df['muscle_group'] == selected_muscle) & 
                    (df['exercise'] == selected_exercise)]
    
    if filtered_df.empty:
        return px.scatter(title="Нет данных для выбранных параметров")
    
    fig = px.line(
        filtered_df,
        x='date',
        y='weight',
        template='plotly_dark',  # Темная тема для графика
        title=f"Прогресс в упражнении {selected_exercise}",
        hover_data=['reps'],
        markers=True
    )
    
    # Дополнительные настройки для темной темы
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis=dict(gridcolor='#444'),
        yaxis=dict(gridcolor='#444'),
        hoverlabel=dict(
            bgcolor='#333',
            font_size=14,
            font_family="Arial"
        )
    )
    
    return fig

@callback(
    Output('progress-graph', 'figure'),
    [Input('user-dropdown', 'value'),
     Input('muscle-dropdown', 'value'),
     Input('exercise-dropdown', 'value')]
)
def update_graph(selected_user, selected_muscle, selected_exercise):
    df = pd.read_csv("workouts.csv")
    return create_dark_figure(df, selected_user, selected_muscle, selected_exercise)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)