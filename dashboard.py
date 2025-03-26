import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import pytz

timezone = pytz.timezone('Europe/Moscow')

# Функция для загрузки данных с проверкой времени изменения файла
def load_data():
    global last_modified_time, df
    current_modified_time = os.path.getmtime('workouts.csv')
    
    if 'last_modified_time' not in globals() or current_modified_time != last_modified_time:
        last_modified_time = current_modified_time
        df = pd.read_csv("workouts.csv")
        df['date'] = pd.to_datetime(df['date'])
        print(f"Данные обновлены в {datetime.now(timezone).strftime('%H:%M:%S')}")
    
    return df

# Инициализация приложения Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Создание layout дэшборда
app.layout = dbc.Container([
    html.H1("Анализ тренировок", className="mb-4"),
    
    # Кнопка для принудительного обновления данных
    dbc.Button("Обновить данные", id="refresh-button", n_clicks=0, className="mb-3"),
    html.Div(id="last-updated", className="mb-2"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Выберите пользователя:"),
            dcc.Dropdown(
                id='user-dropdown',
                options=[],
                value=None,
                clearable=False
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите мышечную группу:"),
            dcc.Dropdown(
                id='muscle-dropdown',
                options=[],
                value=None,
                clearable=False
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите упражнение:"),
            dcc.Dropdown(
                id='exercise-dropdown',
                options=[],
                value=None,
                clearable=False
            )
        ], width=3)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='progress-graph')
        ], width=12)
    ]),
    
    # Скрытый компонент для автоматического обновления
    dcc.Interval(
        id='interval-component',
        interval=120*1000,  # 10 секунд
        n_intervals=0
    )
], fluid=True)

# Callback для обновления данных и dropdown пользователей
@callback(
    Output('user-dropdown', 'options'),
    Output('user-dropdown', 'value'),
    Output('last-updated', 'children'),
    Input('refresh-button', 'n_clicks'),
    Input('interval-component', 'n_intervals')
)
def update_data(n_clicks, n_intervals):
    df = load_data()
    user_options = [{'label': user, 'value': user} for user in df['user_id'].unique()]
    default_user = user_options[0]['value'] if user_options else None
    last_update = f"Последнее обновление: {datetime.now(timezone).strftime('%H:%M:%S')}"
    return user_options, default_user, last_update

# Остальные callback'и остаются без изменений
@callback(
    Output('muscle-dropdown', 'options'),
    Output('muscle-dropdown', 'value'),
    Input('user-dropdown', 'value')
)
def update_muscle_dropdown(selected_user):
    df = load_data()
    filtered_df = df[df['user_id'] == selected_user]
    muscle_options = [{'label': mg, 'value': mg} for mg in filtered_df['muscle_group'].unique()]
    default_value = muscle_options[0]['value'] if muscle_options else None
    return muscle_options, default_value

@callback(
    Output('exercise-dropdown', 'options'),
    Output('exercise-dropdown', 'value'),
    Input('user-dropdown', 'value'),
    Input('muscle-dropdown', 'value')
)
def update_exercise_dropdown(selected_user, selected_muscle):
    df = load_data()
    filtered_df = df[(df['user_id'] == selected_user) & 
                    (df['muscle_group'] == selected_muscle)]
    exercise_options = [{'label': ex, 'value': ex} for ex in filtered_df['exercise'].unique()]
    default_value = exercise_options[0]['value'] if exercise_options else None
    return exercise_options, default_value

@callback(
    Output('progress-graph', 'figure'),
    Input('user-dropdown', 'value'),
    Input('muscle-dropdown', 'value'),
    Input('exercise-dropdown', 'value')
)
def update_graph(selected_user, selected_muscle, selected_exercise):
    df = load_data()
    filtered_df = df[(df['user_id'] == selected_user) & 
                    (df['muscle_group'] == selected_muscle) & 
                    (df['exercise'] == selected_exercise)]
    
    if filtered_df.empty:
        return px.scatter(title="Нет данных для выбранных параметров")
    
    fig = px.line(
        filtered_df, 
        x='date', 
        y='weight',
        title=f"Прогресс в упражнении {selected_exercise}",
        hover_data=['reps'],
        markers=True
    )
    
    fig.update_traces(
        hovertemplate="<b>Дата:</b> %{x}<br><b>Вес:</b> %{y} кг<br><b>Повторений:</b> %{customdata[0]}<extra></extra>"
    )
    
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Вес (кг)",
        hovermode="x unified"
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
