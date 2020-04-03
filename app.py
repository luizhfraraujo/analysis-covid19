import flask
from flask import jsonify
import pandas as pd

app = flask.Flask(__name__, template_folder='templates')

df_ts_confirmed = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')
df_ts_deaths = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv')
df_ts_recovered = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_recovered_global.csv')

df_ts_deaths = df_ts_deaths.drop(columns=["Lat", "Long"])
df_ts_recovered = df_ts_recovered.drop(columns=["Lat", "Long"])

df_ts_confirmed.fillna("", inplace=True)
df_ts_deaths.fillna("", inplace=True)
df_ts_recovered.fillna("", inplace=True)

df_ts_confirmed.rename(columns={"Country/Region":"country_region", "Province/State":"province_state", "Lat":"lat","Long":"long"  }, inplace=True)
df_ts_deaths.rename(columns={"Country/Region":"country_region", "Province/State":"province_state" }, inplace=True)
df_ts_recovered.rename(columns={"Country/Region":"country_region", "Province/State":"province_state" }, inplace=True)

df_ts_confirmed["country_id"] = df_ts_confirmed["country_region"].str.lower().replace(' ', '_', regex=True) + '_' + df_ts_confirmed["province_state"].str.lower().replace(' ', '_', regex=True)
df_ts_deaths["country_id"] = df_ts_deaths["country_region"].str.lower().replace(' ', '_', regex=True) + '_' + df_ts_deaths["province_state"].str.lower().replace(' ', '_', regex=True)
df_ts_recovered["country_id"] = df_ts_recovered["country_region"].str.lower().replace(' ', '_', regex=True) + '_' + df_ts_recovered["province_state"].str.lower().replace(' ', '_', regex=True)

df_ts_confirmed["country_id"] = df_ts_confirmed["country_id"].str[:-1]
df_ts_deaths["country_id"] = df_ts_deaths["country_id"].str[:-1]
df_ts_recovered["country_id"] = df_ts_recovered["country_id"].str[:-1]


df_confirmed = df_ts_confirmed.melt(id_vars=["country_id", "country_region", "province_state", "lat", "long"], var_name="date", value_name="confirmed")
df_deaths = df_ts_deaths.melt(id_vars=["country_id"], var_name="date", value_name="deaths")
df_recovered = df_ts_recovered.melt(id_vars=["country_id"], var_name="date", value_name="recovered")

df_merge_01 = pd.merge(df_confirmed, df_deaths, how='left', on=['country_id', 'date'])
df_covid_countries = pd.merge(df_merge_01, df_recovered, how='left', on=['country_id', 'date'])
df_covid_countries["date"] = pd.to_datetime(df_covid_countries["date"])

countries = df_covid_countries["country_region"].unique()

@app.route("/")
def main():
    return flask.render_template('pages/dashboard.html',countries=countries)


@app.route("/api/v1/data/countries")
def get_countries_data():
    locations = df_covid_countries.groupby("country_region").tail(1)
    locations = locations.sort_values(by=['confirmed'], ascending=False)
    return locations.to_json(orient='records')

@app.route("/api/v1/data/provinces")
def get_provinces_data():
    locations = df_covid_countries.groupby("province_state").tail(1)
    locations = locations.sort_values(by=['confirmed'], ascending=False)
    return locations.to_json(orient='records')


@app.route("/tables")
def tables():
    return flask.render_template('others/tables.html')

@app.route("/api/v1/maps/country/<string:country>")
def get_map_data_country(country):
    if country != "Todos":
        df_country = df_covid_countries.where(df_covid_countries['country_region'] == country)
        df_country.dropna(inplace=True)
        return df_country.tail(1).to_json(orient='records')
    else:
        return df_covid_countries.groupby("country_region").tail(1).to_json(orient='records')


@app.route("/api/v1/data/country/<string:country>")
def get_report_data_country(country):   
    if country != "Todos":
        df_country = df_covid_countries.where(df_covid_countries['country_region'] == country)
        
        df_country = df_country.where(df_country['confirmed'] > 0)
        df_country.dropna(inplace=True)

        return jsonify({
                'confirmed': int(df_country["confirmed"].tail(1)),
                'deaths': int(df_country["deaths"].tail(1)),
                'recovered': int(df_country["recovered"].tail(1)),
                'active': int(df_country["confirmed"].tail(1)) - (int(df_country["recovered"].tail(1)) + int(df_country["deaths"].tail(1))),
                'chart':{
                'confirmed': {
                    'series': df_country.groupby(["date"]).confirmed.sum().tolist(),
                    'labels': df_country["date"].dt.strftime('%d/%m').unique().tolist()
                },
                'deaths': {
                   'series': df_country.groupby(["date"]).deaths.sum().tolist(),
                    'labels': df_country["date"].dt.strftime('%d/%m').unique().tolist()
                },
                'recovered': {
                    'series': df_country.groupby(["date"]).recovered.sum().tolist(),
                    'labels': df_country["date"].dt.strftime('%d/%m').unique().tolist()
                }
            }
        })
    else:
        return jsonify({
                'confirmed': int(df_covid_countries.groupby(["date"]).confirmed.sum().tail(1)),
                'deaths': int(df_covid_countries.groupby(["date"]).deaths.sum().tail(1)),
                'recovered': int(df_covid_countries.groupby(["date"]).recovered.sum().tail(1)),
                'active': int(df_covid_countries.groupby(["date"]).confirmed.sum().tail(1)) - (int(df_covid_countries.groupby(["date"]).recovered.sum().tail(1)) + int(df_covid_countries.groupby(["date"]).deaths.sum().tail(1))),
                'chart':{
                'confirmed': {
                    'series': df_covid_countries.groupby(["date"]).confirmed.sum().tolist(),
                    'labels': df_covid_countries["date"].dt.strftime('%d/%m').unique().tolist()
                },
                'deaths': {
                   'series': df_covid_countries.groupby(["date"]).deaths.sum().tolist(),
                    'labels': df_covid_countries["date"].dt.strftime('%d/%m').unique().tolist()
                },
                'recovered': {
                    'series': df_covid_countries.groupby(["date"]).recovered.sum().tolist(),
                    'labels': df_covid_countries["date"].dt.strftime('%d/%m').unique().tolist()
                }}
            })
    

@app.errorhandler(404)
def not_found(e):
    return flask.render_template('pages/404.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')