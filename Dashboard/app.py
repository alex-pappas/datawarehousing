import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from datetime import datetime as dt
import pymongo
import pandas as pd
import numpy as np
import plotly.graph_objs as go

client = pymongo.MongoClient("localhost", 27017)

db = client['season2020']
test = db.games.find()

def player_avg_stat(player, stat):
    player = str(player)
    stat = str(stat)
    cursor = db.games.find({"teamA_stats."+player:{"$exists":True}},{"teamA_stats."+player+"."+stat:1,"_id":False})
    value = [doc['teamA_stats'][player][stat] for doc in cursor]
    cursor1 = db.games.find({"teamH_stats."+player:{"$exists":True}},{"teamH_stats."+player+"."+stat:1,"_id":False})
    value1 = [doc['teamH_stats'][player][stat] for doc in cursor1]
    values = value + value1
    num_values = [float(num) for num in values if (num is not None) and (num is not '')]
    stat_mean = np.array(num_values).mean()
    return player, stat, stat_mean

def list_of_names():
    cursor2 = db.games.find({},{"teamA":1,"teamA_stats":1,"_id":False})
    c = pd.DataFrame(cursor2)
    total_players = pd.DataFrame()
    for j in range(len(c)):
        players = c.to_dict(orient='split')['data'][j][1]
        team = c.to_dict(orient='split')['data'][j][0]
        name_players = [name for name in pd.DataFrame(players).columns]
        team_list = [team for i in range(len(pd.DataFrame(players).columns))]
        total_players = total_players.append(pd.DataFrame({'teams':team_list, 'players':name_players}),ignore_index=True)
        total_players1 = total_players.drop_duplicates(subset ="players", keep = 'first', inplace = False)
    return total_players1

def get_avgs_dataframe():
    stats = ['FG','FGA','FG%','3P','3PA','3P%','FT','FTA','FT%','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS','+/-']
    names = list(total_players['players'])
    store = []
    final_list = []
    avg_stats = pd.DataFrame()
    for name in names:
        store = [name]
        for stat in stats:
            foo = player_avg_stat(name, stat)
            store = store + [foo[2]]
        final_list.append(store)
    return pd.DataFrame(final_list, columns=(['Players'] +stats)).sort_values('PTS', ascending=False)

total_players = list_of_names()
df_avg_stats = get_avgs_dataframe()

app = dash.Dash('nba')


app.layout = html.Div(className = 'layout', children = [

            html.Div(className = 'firstbox', children = [
                html.Img(className= 'logo', src=app.get_asset_url('nba_logo.jpg')),           
                html.H2(className = 'stats_font',children = 'Stats')
                ]),

            html.Div(className= 'secondbox', children = [

                html.Div(className = 'firstteam', children = [
                    html.H2('Home Team', className = 'Home_Team'),
                    dcc.Dropdown(
                        id='select_home',
                        className="select_home",
                        options=[{'label': i, 'value': i} for i in ['Los Angeles', 'New York Knicks', 'Miami Heat']],
                        value='LA')]),

                html.Div(className = 'datebox', children = [
                    dcc.DatePickerSingle(
                        id='date-selection')]),

                html.Div(className = 'secondteam', children = [
                    html.H2('Away Team', className = 'Away_Team'),
                    dcc.Dropdown(
                        id='select_away',
                        className="select_away",
                        options=[{'label': i, 'value': i} for i in ['Los Angeles', 'New York Knicks', 'Miami Heat']],
                        value='LA')])
                ]),

            html.Div(className = 'graph', children = [
                    dcc.Graph(
                        id='graph',
                        figure={'data':[go.Bar(x = df_avg_stats.PTS,
                        y = df_avg_stats.Players,
                        orientation = 'h')],
                        'layout': {
                        'title': 'Harden sucks'}})
                        ]),

            html.Div(className = 'data_frame', children = [
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": i, "id": i} for i in df_avg_stats.columns],
                        data=df_avg_stats.to_dict('records'),
                        fixed_columns={ 'headers': True, 'data': 1})
                        ])

    ])

app.run_server(debug=True)
