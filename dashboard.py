import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc

# Загрузка данных (замените на ваш способ загрузки)
# df = pd.read_csv('your_data.csv')
# Для примера создадим тестовые данные
# data = {
#     'user_id': ['user1', 'user1', 'user1', 'user2', 'user2', 'user3'] * 5,
#     'date': pd.date_range(start='2023-01-01', periods=30).tolist(),
#     'muscle_group': ['chest', 'back', 'legs', 'chest', 'arms', 'legs'] * 5,
#     'exercise': ['bench press', 'deadlift', 'squat', 'bench press', 'bicep curl', 'squat'] * 5,
#     'weight': [50, 70, 60, 55, 20, 65] * 5,
#     'reps': [10, 8, 12, 9, 15, 10] * 5
# }
# df = pd.DataFrame(data)
df = pd.read_csv("workouts.csv")
df['date'] = pd.to_datetime(df['date'])

# Инициализация приложения Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Создание layout дэшборда
app.layout = dbc.Container([
    html.H1("Анализ тренировок", className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            html.Label("Выберите пользователя:"),
            dcc.Dropdown(
                id='user-dropdown',
                options=[{'label': user, 'value': user} for user in df['user_id'].unique()],
                value=df['user_id'].unique()[0],
                clearable=False
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите мышечную группу:"),
            dcc.Dropdown(
                id='muscle-dropdown',
                clearable=False
            )
        ], width=3),
        
        dbc.Col([
            html.Label("Выберите упражнение:"),
            dcc.Dropdown(
                id='exercise-dropdown',
                clearable=False
            )
        ], width=3)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='progress-graph')
        ], width=12)
    ])
], fluid=True)

# Callback для обновления dropdown мышечных групп
@callback(
    Output('muscle-dropdown', 'options'),
    Output('muscle-dropdown', 'value'),
    Input('user-dropdown', 'value')
)
def update_muscle_dropdown(selected_user):
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
    filtered_df = df[(df['user_id'] == selected_user) & 
                    (df['muscle_group'] == selected_muscle)]
    exercise_options = [{'label': ex, 'value': ex} for ex in filtered_df['exercise'].unique()]
    default_value = exercise_options[0]['value'] if exercise_options else None
    return exercise_options, default_value

# Callback для обновления графика
@callback(
    Output('progress-graph', 'figure'),
    Input('user-dropdown', 'value'),
    Input('muscle-dropdown', 'value'),
    Input('exercise-dropdown', 'value')
)
def update_graph(selected_user, selected_muscle, selected_exercise):
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
    app.run(debug=True, host='127.0.0.1', port=8055)
