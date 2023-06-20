# ====================== Импорт ======================#
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# ====================== Получение данных ======================#
df = pd.read_csv('ArgoFloats_east.csv', low_memory=False)

df = df.dropna()

convert_dict = {'latitude': float,
                'longitude': float,
                'pres': float,
                'temp': float,
                'psal': float}
df = df.astype(convert_dict)

df_last = df.sort_values('cycle_number', ascending=False).drop_duplicates(['fileNumber'])
# ====================== Установка параметров и контейнеров ======================#
app = Dash(name="my_first_dash_app", external_stylesheets=external_stylesheets)

server = app.server # Если не добавить эту строку, то не заработает.

app.layout = html.Div(children=[
    html.Div(children=[
        dcc.Dropdown(df['fileNumber'].unique(), id='Number', style={'width': '250px'}),
        dcc.Dropdown(id='cycle', style={'width': '250px'}),
        html.A('Download CSV', href='https://www.dropbox.com/s/80kbuzytevva13g/ArgoFloats.csv?dl=1'),
        html.A('Download JSON', href='https://www.dropbox.com/s/80kbuzytevva13g/ArgoFloats.csv?dl=1')],
        style={'display': 'flex', 'justify-content': 'space-between', 'width': '750px', 'align-items': 'center', 'margin': '20px'}),
    html.Div(children=[
        dcc.Graph(id='map')]),
    html.Div(children=[
        dcc.Graph(id='PSU_decibar', style={'width': '450px', 'height': '450px'}),
        dcc.Graph(id='degrees_decibar', style={'width': '450px', 'height': '450px'}),
        dcc.Graph(id='anomaly_density', style={'width': '450px', 'height': '450px'}),
        dcc.Graph(id='speed_of_sound', style={'width': '450px', 'height': '450px'})
    ], style={'display': 'flex'})
])

# ====================== Обработка и расчет данных ======================#
# Аномалия плотности
df['anomaly_density'] = 28.132 - (0.0734 * df.temp) - (0.00469 * df.temp ** 2) + (0.803 - 0.002 * df.temp) * (
        df.psal - 35)

# Скорость звука
C00 = 1402.388
C01 = 5.03830
C02 = -5.81090E-2
C03 = 3.3432E-4
C04 = -1.47797E-6
C05 = 3.1419E-9
C10 = 0.153563
C11 = 6.8999E-4
C12 = -8.1829E-6
C13 = 1.3632E-7
C14 = -6.1260E-10
C20 = 3.1260E-5
C21 = -1.7111E-6
C22 = 2.5986E-8
C23 = -2.5353E-10
C24 = 1.0415E-12
C30 = -9.7729E-9
C31 = 3.8513E-10
C32 = -2.3654E-12
A00 = 1.389
A01 = -1.262E-2
A02 = 7.166E-5
A03 = 2.008E-6
A04 = -3.21E-8
A10 = 9.4742E-5
A11 = -1.2583E-5
A12 = -6.4928E-8
A13 = 1.0515E-8
A14 = -2.0142E-10
A20 = -3.9064E-7
A21 = 9.1061E-9
A22 = -1.6009E-10
A23 = 7.994E-12
A30 = 1.100E-10
A31 = 6.651E-12
A32 = -3.391E-13
B00 = -1.922E-2
B01 = -4.42E-5
B10 = 7.3637E-5
B11 = 1.7950E-7
D00 = 1.727E-3
D10 = -7.9836E-6

df['speed_of_sound'] = ((C00 + C01 * df.temp + C02 * df.temp ** 2 + C03 * df.temp ** 3 + C04 * df.temp ** 4 + C05 * df.temp ** 5)
                        + (C10 + C11 * df.temp + C12 * df.temp ** 2 + C13 * df.temp ** 3 + C14 * df.temp ** 4) *
                        df.pres + (C20 + C21 * df.temp + C22 * df.temp ** 2 + C23 * df.temp ** 3 + C24 * df.temp ** 4) *
                        df.pres ** 2 + (C30 + C31 * df.temp + C32 * df.temp ** 2) * df.pres ** 3) + \
                       ((A00 + A01 * df.temp + A02 * df.temp ** 2 + A03 * df.temp ** 3 + A04 * df.temp ** 4) +
                        (A10 + A11 * df.temp + A12 * df.temp ** 2 + A13 * df.temp ** 3 + A14 * df.temp ** 4) *
                        df.pres + (A20 + A21 * df.temp + A22 * df.temp ** 2 + A23 * df.temp ** 3) *
                        df.pres ** 2 + (A30 + A31 * df.temp + A32 * df.temp ** 2) * df.pres ** 3) * df.psal + \
                       (B00 + B01 * df.temp + (B10 + B11 * df.temp) * df.pres) * df.psal ** 1.5 + \
                       (D00 + D10 * df.pres) * df.psal ** 2


# ====================== Декораторы ======================#
# Фильтрация для получения номеров циклов буя
@app.callback(
    Output('cycle', 'options'),
    Output('cycle', 'value'),
    Input('Number', 'value'))
def update_cycle(input_obj):
    return df[df.fileNumber == input_obj]['cycle_number'].unique(), None


# Получение номера буя и цикла для вывода местоположения на карте
@app.callback(
    Output('map', 'figure'),
    Input('Number', 'value'),
    Input('cycle', 'value'))
def set_cities_value(inp_number, inp_cycle):
    if inp_cycle is None and inp_number is None:
        figure_1 = go.Figure(go.Scattermapbox(mode='markers', lat=df_last.latitude, lon=df_last.longitude,
                                              marker={'size': 5}, marker_color=df_last.fileNumber,
                                              customdata=df_last[['fileNumber', 'longitude', 'latitude']],
                                              hovertemplate=
                                              '<i>Number</i>: %{customdata[0]}<extra></extra><br>' +
                                              '<i>Lat</i>: %{customdata[2]:.2f}<br>' +
                                              '<i>Lon</i>: %{customdata[1]:.2f}'))
    elif inp_cycle is None and inp_number is not None:
        filtered_df = df.loc[(df.fileNumber == float(inp_number))]
        figure_1 = go.Figure(go.Scattermapbox(mode='markers+text+lines', lat=filtered_df.latitude, lon=filtered_df.longitude,
                                              marker={'size': 5}, marker_color=filtered_df.cycle_number,
                                              customdata=filtered_df[['longitude', 'latitude', 'cycle_number']],
                                              hovertemplate=
                                              '<i>Cycle</i>: %{customdata[2]}<extra></extra><br>' +
                                              '<i>Lat</i>: %{customdata[1]:.2f}<br>' +
                                              '<i>Lon</i>: %{customdata[0]:.2f}'))
    else:
        filtered_df = df.loc[(df.fileNumber == float(inp_number)) & (df.cycle_number == float(inp_cycle))]
        figure_1 = go.Figure(go.Scattermapbox(mode='markers+text+lines', lat=filtered_df.latitude, lon=filtered_df.longitude,
                                              marker={'size': 5}, hovertemplate=
                                              '<i>Lat</i>: %{lat:.2f}<extra></extra><br>' +
                                              '<i>Lon</i>: %{lon:.2f}'))
    figure_1.update_layout(
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        mapbox={
            'style': "stamen-terrain",
            'center': {'lon': 70, 'lat': 70},
            'zoom': 1.5})
    return figure_1


# Вывод графиков по бую и циклу
@app.callback(
    Output('PSU_decibar', 'figure'),
    Input('Number', 'value'),
    Input('cycle', 'value'))
def fig(number, cycle):
    if cycle is None:
        figure_psal = px.line(x=[0], y=[0])
    else:
        figure_psal = px.line(df.loc[(df.fileNumber == float(number)) & (df.cycle_number == float(cycle))],
                              x="psal", y="pres", markers=True)
    figure_psal.update_yaxes(autorange='reversed')
    figure_psal.update_layout(margin={'l': 0, 't': 0, 'b': 0, 'r': 0})
    return figure_psal


@app.callback(
    Output('anomaly_density', 'figure'),
    Input('Number', 'value'),
    Input('cycle', 'value'))
def fig(number, cycle):
    if cycle is None:
        figure_psal = px.line(x=[0], y=[0])
    else:
        figure_psal = px.line(df.loc[(df.fileNumber == float(number)) & (df.cycle_number == float(cycle))],
                              x="anomaly_density", y="pres", markers=True)
    figure_psal.update_yaxes(autorange='reversed')
    figure_psal.update_layout(margin={'l': 0, 't': 0, 'b': 0, 'r': 0})
    return figure_psal


@app.callback(
    Output('speed_of_sound', 'figure'),
    Input('Number', 'value'),
    Input('cycle', 'value'))
def fig(number, cycle):
    if cycle is None:
        figure_psal = px.line(x=[0], y=[0])
    else:
        figure_psal = px.line(df.loc[(df.fileNumber == float(number)) & (df.cycle_number == float(cycle))],
                              x="speed_of_sound", y="pres", markers=True)
    figure_psal.update_yaxes(autorange='reversed')
    figure_psal.update_layout(margin={'l': 0, 't': 0, 'b': 0, 'r': 0})
    return figure_psal


@app.callback(
    Output('degrees_decibar', 'figure'),
    Input('Number', 'value'),
    Input('cycle', 'value'))
def fig(number, cycle):
    if cycle is None:
        figure_temp = px.line(x=[0], y=[0])
    else:
        figure_temp = px.line(df.loc[(df.fileNumber == float(number)) & (df.cycle_number == float(cycle))],
                              x="temp", y="pres", markers=True)
    figure_temp.update_yaxes(autorange='reversed')
    figure_temp.update_layout(margin={'l': 0, 't': 0, 'b': 0, 'r': 0})
    return figure_temp


# ====================== Запуск приложения ======================#
if __name__ == '__main__':
    app.run_server(debug=True)
