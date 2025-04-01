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
        interval=120*1000,  # 120 секунд
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

# Callback для обновления dropdown мышечных групп
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

# Callback для обновления dropdown упражнений
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

# Callback для обновления графика прогресса
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
    
    # Создаем график с цветовым градиентом по количеству повторений
    fig = px.scatter(
        filtered_df, 
        x='date', 
        y='weight',
        color='reps',
        color_continuous_scale='Reds',  # Градиентная палитра (можно заменить на 'Plasma', 'Inferno', 'Magma', 'Cividis')
        range_color=[1, 15],
        title=f"Прогресс в упражнении {selected_exercise}",
        hover_data=['reps'],
        size=[12] * len(filtered_df)  # Размер точек
    )
    
    # Добавляем линии между точками
    fig.add_scatter(
        x=filtered_df['date'],
        y=filtered_df['weight'],
        mode='lines+markers',
        line=dict(color='rgba(150, 150, 150, 0.5)', width=1),
        marker=dict(size=0),  # Скрываем маркеры для этого следа
        showlegend=False,
        hoverinfo='skip'
    )
    
    # Настраиваем отображение точек
    fig.update_traces(
        hovertemplate="<b>Дата:</b> %{x}<br><b>Вес:</b> %{y} кг<br><b>Повторений:</b> %{customdata[0]}<extra></extra>",
        marker=dict(
            size=12,
            line=dict(width=1, color='DarkSlateGrey'),
            opacity=0.8
        ),
        selector=dict(mode='markers')
    )
    
    # Настраиваем layout графика
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Вес (кг)",
        hovermode="x unified",
        coloraxis_colorbar=dict(
            title="Повторений",
            thickness=20,
            len=0.5
        ),
        plot_bgcolor='rgba(240, 240, 240, 0.8)',
        paper_bgcolor='rgba(240, 240, 240, 0.1)'
    )
    
    # Настраиваем оси
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(200, 200, 200, 0.5)')
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='rgba(200, 200, 200, 0.5)')
    
    return fig

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)