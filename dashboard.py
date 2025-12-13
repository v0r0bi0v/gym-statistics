import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime
import os
import pytz
import ast

timezone = pytz.timezone('Europe/Moscow')

# Функция для загрузки данных с проверкой времени изменения файла
def load_data():
    global last_modified_time, df
    current_modified_time = os.path.getmtime('workouts.csv')

    if 'last_modified_time' not in globals() or current_modified_time != last_modified_time:
        last_modified_time = current_modified_time
        try:
            # Читаем данные с явным указанием типа данных
            df = pd.read_csv("workouts.csv", sep=';')
            print("Первые 5 строк после загрузки:")
            print(df.head())

            # Проверяем и преобразуем колонку reps
            if 'reps' in df.columns:
                # Преобразуем строки в tuple, если они не пустые
                df['reps'] = df['reps'].apply(
                    lambda x: ast.literal_eval(x) if pd.notnull(x) and isinstance(x, str) else tuple()
                )

                # Создаем колонку max_reps только если reps содержит tuple
                df['max_reps'] = df['reps'].apply(
                    lambda x: max(x) if isinstance(x, tuple) and len(x) > 0 else 0
                )
            else:
                df['reps'] = tuple()
                df['max_reps'] = 0

            # Преобразуем дату
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            else:
                df['date'] = pd.to_datetime([])

            print("Данные после обработки:")
            print(df.head())
            print(f"Данные обновлены в {datetime.now(timezone).strftime('%H:%M:%S')}")

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            # Создаем пустой DataFrame с нужными колонками
            df = pd.DataFrame(columns=["user_id", "date", "muscle_group", "exercise", "weight", "reps", "max_reps"])

    df.sort_values("date", inplace=True)

    return df

# Инициализация приложения Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server


def build_layout():
    return dbc.Container(
        fluid="lg",
        className="py-4",
        children=[
            # ===== Header =====
            dbc.Row(
                className="align-items-center gy-2",
                children=[
                    dbc.Col(
                        html.Div(
                            [
                                html.H2("Анализ тренировок", className="mb-0"),
                                html.Div(
                                    "Прогресс по упражнениям с учетом повторений",
                                    className="text-muted",
                                ),
                            ]
                        ),
                        xs=12,
                        md=8,
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Обновить данные",
                            id="refresh-button",
                            n_clicks=0,
                            color="primary",
                            className="w-100 w-md-auto",
                        ),
                        xs=12,
                        md="auto",
                    ),
                ],
            ),
            html.Div(id="last-updated", className="text-muted mt-2"),
            html.Hr(className="my-3"),

            # ===== Filters card =====
            dbc.Card(
                className="shadow-sm",
                children=[
                    dbc.CardHeader(html.Div("Фильтры", className="fw-semibold")),
                    dbc.CardBody(
                        dbc.Row(
                            className="g-3",
                            children=[
                                dbc.Col(
                                    [
                                        dbc.Label("Пользователь", className="text-muted"),
                                        dcc.Dropdown(
                                            id='user-dropdown',
                                            options=[],
                                            value=None,
                                            clearable=False
                                        ),
                                    ],
                                    xs=12,
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Мышечная группа", className="text-muted"),
                                        dcc.Dropdown(
                                            id='muscle-dropdown',
                                            options=[],
                                            value=None,
                                            clearable=False
                                        ),
                                    ],
                                    xs=12,
                                    md=4,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Label("Упражнение", className="text-muted"),
                                        dcc.Dropdown(
                                            id='exercise-dropdown',
                                            options=[],
                                            value=None,
                                            clearable=False
                                        ),
                                    ],
                                    xs=12,
                                    md=4,
                                ),
                            ],
                        )
                    ),
                ],
            ),

            # ===== Graph card =====
            dbc.Row(
                className="g-3 mt-1",
                children=[
                    dbc.Col(
                        dbc.Card(
                            className="shadow-sm",
                            children=[
                                dbc.CardHeader(html.Div("График прогресса", className="fw-semibold")),
                                dbc.CardBody(
                                    dbc.Spinner(
                                        dcc.Graph(
                                            id='progress-graph',
                                            config={"displayModeBar": False},
                                        ),
                                        color="primary",
                                    )
                                ),
                            ],
                        ),
                        xs=12,
                    )
                ],
            ),

            # Скрытый компонент для автоматического обновления (закомментирован)
            # dcc.Interval(
            #     id='interval-component',
            #     interval=120*1000,  # 120 секунд
            #     n_intervals=0
            # )
        ],
    )


app.layout = html.Div(children=build_layout())


# Callback для обновления данных и dropdown пользователей
@callback(
    Output('user-dropdown', 'options'),
    Output('user-dropdown', 'value'),
    Output('last-updated', 'children'),
    Input('refresh-button', 'n_clicks'),
    # Input('interval-component', 'n_intervals')  # Закомментировано
)
def update_data(n_clicks, n_intervals=None):  # Убрал n_intervals из обязательных аргументов
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
    print(f"Обновление графика для: {selected_user}, {selected_muscle}, {selected_exercise}")

    if selected_user is None or selected_muscle is None or selected_exercise is None:
        return px.scatter(title="Выберите параметры для отображения графика")

    # Проверяем наличие необходимых колонок
    required_cols = ['user_id', 'muscle_group', 'exercise', 'date', 'weight']
    if not all(col in df.columns for col in required_cols):
        print("Отсутствуют необходимые колонки в DataFrame")
        return px.scatter(title="Ошибка: данные неполные")

    # Фильтруем данные
    filtered_df = df[(df["user_id"] == selected_user) &
                     (df["muscle_group"] == selected_muscle) &
                     (df["exercise"] == selected_exercise)]

    print(f"Найдено записей: {len(filtered_df)}")
    if not filtered_df.empty:
        print(filtered_df[['date', 'weight', 'reps']].head())

    if filtered_df.empty:
        return px.scatter(title="Нет данных для выбранных параметров")

    try:
        # Если есть колонка max_reps, используем ее, иначе создаем временную
        if 'max_reps' not in filtered_df.columns:
            filtered_df['max_reps'] = filtered_df['reps'].apply(
                lambda x: max(x) if isinstance(x, tuple) and len(x) > 0 else 0
            )

        # Определяем диапазон для цветовой шкалы
        min_reps = filtered_df['max_reps'].min()
        max_reps = filtered_df['max_reps'].max()

        # Если все значения одинаковые, немного расширяем диапазон
        if min_reps == max_reps:
            min_reps = max(0, min_reps - 1)
            max_reps = max_reps + 1

        # Создаем график
        fig = px.scatter(
            filtered_df,
            x='date',
            y='weight',
            color='max_reps',
            color_continuous_scale='RdYlGn',
            range_color=[min_reps, max_reps],
            title=f"Прогресс в упражнении {selected_exercise}",
            hover_data=['reps'],
            size=[24] * len(filtered_df)
        )

        # Добавляем линии между точками
        fig.add_scatter(
            x=filtered_df['date'],
            y=filtered_df['weight'],
            mode='lines+markers',
            line=dict(color='rgba(150, 150, 150, 0.5)', width=1),
            marker=dict(size=0),
            showlegend=False,
            hoverinfo='skip'
        )

        # Настраиваем отображение
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
                title="Макс. повторений",
                thickness=20,
                len=0.5
            ),
            plot_bgcolor='rgba(240, 240, 240, 0.8)',
            paper_bgcolor='rgba(240, 240, 240, 0.1)',
            margin=dict(l=10, r=10, t=70, b=10),
        )

        return fig

    except Exception as e:
        print(f"Ошибка при создании графика: {e}")
        return px.scatter(title="Ошибка при отображении данных")


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
