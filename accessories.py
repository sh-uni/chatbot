# import the required libraries
import datetime as dt
import pandas as pd
import requests
import pickle
import ast
from pprint import pprint


# check the connection to the websites used in this project
def check_websites():
    # URLs for the websites used in this project
    urls = {'OpenWeather': 'https://openweathermap.org/'}

    website_check = GetRequests()
    print("OpenWeather website check: ")
    print(website_check.make_get_requests(urls['OpenWeather']))

# convert weather.json to pd dataframe
def convert_to_df(data):
    df_original = pd.DataFrame(data['list'])
    #print(df_original.head())

    # get dictionary in 'main'
    df_main = pd.DataFrame(df_original['main'].apply(pd.Series))
    #print(df_main.head())

    # get dictionary in 'weather'
    df_weather = pd.DataFrame(df_original['weather'].apply(pd.Series))
    df_weather = pd.DataFrame(df_weather[0].apply(pd.Series))
    df_weather.rename({'main': 'weather_main'}, axis=1, inplace=True)
    #print(df_weather.head())

    # get dictionary in 'wind'
    df_wind = pd.DataFrame(df_original['wind'].apply(pd.Series))
    #print(df_wind.head())

    # get timezone and create local datetime
    df_dt = pd.DataFrame(df_original['dt'])
    df_dt = df_dt.add(data['city']['timezone'])
    df_dt.rename({'dt': 'dt_local'}, axis=1, inplace=True)

    # add dictionaries to original df and remove unnecessary data
    df_final = pd.concat([df_original, df_main], axis=1)
    df_final = pd.concat([df_final, df_weather], axis=1)
    df_final = pd.concat([df_final, df_wind], axis=1)
    df_final = pd.concat([df_final, df_dt], axis=1)
    df_final = df_final.drop(columns=['main','weather','wind','sea_level','grnd_level','temp_kf','icon'])
    df_final.rename({'speed': 'wind_speed',
                     'deg': 'wind_deg',
                     'gust': 'wind_gust',
                     'id': 'weather_id',
                     'description': 'weather_description'},
                    axis=1,
                    inplace=True)
    #print(df_final.head())
    #df_final.to_csv('json_test.csv')
    return df_final




# create a function to give the string day of the week from an index
def day_of_week(index):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][index]


# convert direction from degrees to compass readings
def deg_to_text(deg):
    return ["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"][round(deg/22.5)%16]


# create function to return best day to travel to location based on daytime characteristics
def get_best_day(daytime_data):
    # set up a dataframe
    df_setup_start = pd.DataFrame(daytime_data)
    df_data = pd.DataFrame(df_setup_start[1].apply(pd.Series))
    df_days = df_setup_start.drop(columns=[1])
    df_final = pd.concat([df_days, df_data], axis=1)
    df_final.rename({0: 'day'}, axis=1, inplace=True)

    #sort by best day
    df_sorted = df_final.sort_values(by='mean_humidity', ascending=True)  # lowest mean humidity
    df_sorted = df_sorted.sort_values(by='from_ideal_temp', ascending=True)  # closest to ideal temp (value of 0)
    df_sorted = df_sorted.sort_values(by='max_wind', ascending=True)  # lowest max wind
    df_sorted = df_sorted.sort_values(by='total_rain', ascending=True)  # lowest total rain
    #reset index and drop old index
    df_sorted = df_sorted.reset_index(drop=True)

    #best day is first in new index
    best_day = df_sorted['day'][0]

    return best_day


# create function to get the daily 'daytime' forecast from 3 hourly data
def get_daytime_forecast_from_df(df):
    # initialise dataset
    hourly_rain = []
    hourly_wind = []
    hourly_temp = []
    hourly_humidity = []
    daytime_data = []
    ideal_temp = 21  # degC

    # find data for all 'daytime' hours
    for index, row in df.iterrows():
        # if daytime
        if row['sys']['pod'] == 'd':
            try:
                hourly_rain.append([row['dt_local'], row['rain']['3h']])
            except:
                hourly_rain.append([row['dt_local'], 0])
            hourly_wind.append([row['dt_local'], round(row['wind_speed'] / 1000 * 3600, 1)])  # m/s to km/h
            hourly_temp.append([row['dt_local'], row['temp']])
            hourly_humidity.append([row['dt_local'], row['humidity']])

    # find required intervals
    date_now = dt.datetime.now(dt.timezone.utc).date()
    prev_date = dt.datetime.utcfromtimestamp(hourly_temp[0][0]).date()
    prev_dt_local = hourly_temp[0]
    all_daytime_rain = []
    all_daytime_wind = []
    all_daytime_temps = []
    all_daytime_humidity = []

    # for each timestamp in temperature list
    for dt_rain, dt_wind, dt_temp, dt_humidity in zip(hourly_rain, hourly_wind, hourly_temp, hourly_humidity):
        # get this date
        next_date = dt.datetime.utcfromtimestamp(dt_rain[0]).date()

        # if new day, calc and record total/ave/max for previous day
        if next_date != prev_date:
            date_total_rain = round(sum(all_daytime_rain),2)
            date_max_wind = int(max(all_daytime_wind))
            # how close to ideal temp is mean temp
            date_ideal_temp = int(abs(sum(all_daytime_temps)/len(all_daytime_temps) - ideal_temp))
            date_mean_humidity = int(sum(all_daytime_humidity)/len(all_daytime_humidity))

            # for first day, use 'today' instead of day of week
            date_collected = dt.datetime.utcfromtimestamp(prev_dt_local[0]).date()
            if date_collected == date_now:
                day_collected = 'Today'
            else:
                dt_day = dt.datetime.utcfromtimestamp(prev_dt_local[0]).weekday()
                day_collected = day_of_week(dt_day)

            daytime_data.append([day_collected, {'total_rain': date_total_rain,
                                                 'max_wind': date_max_wind,
                                                 'from_ideal_temp': date_ideal_temp,
                                                 'mean_humidity': date_mean_humidity}])

            all_daytime_rain = []
            all_daytime_wind = []
            all_daytime_temps = []
            all_daytime_humidity = []
            prev_date = next_date
            prev_dt_local = dt_rain

            # if required number of days already collected, break loop
            if len(daytime_data) == 5:
                break

        # get this data for this date
        all_daytime_rain.append(dt_rain[1])
        all_daytime_wind.append(dt_wind[1])
        all_daytime_temps.append(dt_temp[1])
        all_daytime_humidity.append(dt_humidity[1])

    return daytime_data


# create function to get the daily min/max temperature from 3 hourly data
def get_forecast_temps_from_df(df):
    # initialise dataset
    hourly_temps = []
    daily_temps = []

    # find temps for all hours
    for index, row in df.iterrows():
        hourly_temps.append([row['dt_local'], row['temp']])

    # find required intervals
    prev_date = dt.datetime.utcfromtimestamp(hourly_temps[0][0]).date()
    prev_dt_local = hourly_temps[0]
    all_day_temps = []
    today_collected = False

    # for each timestamp in temperature list
    for dt_local in hourly_temps:
        # get this date
        next_date = dt.datetime.utcfromtimestamp(dt_local[0]).date()

        # if new day, calc and record min/max for previous day
        if next_date != prev_date:
            date_min = int(min(all_day_temps), )
            date_max = int(max(all_day_temps))

            # for first day, use 'today' instead of day of week
            if today_collected is False:
                daily_temps.append(['Today', {'min': date_min, 'max': date_max}])
                today_collected = True
            else:
                dt_day = dt.datetime.utcfromtimestamp(prev_dt_local[0]).weekday()
                daily_temps.append([day_of_week(dt_day), {'min': date_min, 'max': date_max}])

            all_day_temps = []
            prev_date = next_date
            prev_dt_local = dt_local

            # if required number of days already collected, break loop
            if len(daily_temps) == 5:
                break

        # get this temp
        all_day_temps.append(dt_local[1])

    return daily_temps


# get daily forecast for all sites
def get_forecast_data_all(dfs):
    forecast_temps = {}
    daytime_data = {}
    best_days = {}
    weather_summary = {}
    for key in itinerary_location_keys:
        forecast_temps.update({key:get_forecast_temps_from_df(dfs[key])})
        daytime_data.update({key:get_daytime_forecast_from_df(dfs[key])})
        best_days.update({key:get_best_day(daytime_data[key])})
        day_collection, set_of_days, set_of_hours = get_weather_summary(dfs[key])
        weather_summary.update({key:day_collection})
    return forecast_temps, best_days, weather_summary, set_of_days, set_of_hours



# create a function to retrieve os API keys
def get_key(key_name):
    # enable if using environmental variables
    # API_key = os.environ.get(key_name)

    # get APIs from .txt file for assignment submission
    file = open('static/text/API_keys.txt','r')
    API_key = ast.literal_eval(file.read())[key_name]

    return API_key


# create a function to get the current weather, weather forecast and weather map
def get_weather(current_location):

    weather_coordinates = itinerary_locations[current_location]
    weather_lat = str(weather_coordinates[0])
    weather_lon = str(weather_coordinates[1])

    # create urls for location
    forecast_url = ("https://api.openweathermap.org/data/2.5/forecast?lat="
                    + weather_lat + "&lon=" + weather_lon
                    + "&appid=" + API_keys['OpenWeather'] + "&units=metric")

    # get current weather data
    resp = requests.get(forecast_url)
    forecast_weather = resp.json()
    #pprint(forecast_weather)

    return forecast_weather


# get weather for all itinerary locations and return dict of dataframes
def get_weather_all():
    itinerary_forcast_dfs = {}
    for key in itinerary_location_keys:
        forecast_weather_json = get_weather(key)
        forecast_weather_df = convert_to_df(forecast_weather_json)
        itinerary_forcast_dfs.update({key:forecast_weather_df})
    return itinerary_forcast_dfs


def get_weather_summary(df):
    # initialise dataset
    hourly_temp = []
    hourly_humidity = []
    hourly_description = []
    hourly_wind = []

    # find data for all hours
    for index, row in df.iterrows():
        hourly_temp.append([row['dt_local'], round(row['temp'], 1)])
        hourly_humidity.append([row['dt_local'], round(row['humidity'], 0)])
        hourly_description.append([row['dt_local'], row['weather_description']])
        hourly_wind.append([row['dt_local'], round(row['wind_speed'] / 1000 * 3600, 1)])  # m/s to km/h

    # find required intervals
    date_now = dt.datetime.now(dt.timezone.utc).date()
    prev_date = dt.datetime.utcfromtimestamp(hourly_temp[0][0]).date()
    prev_dt_local = hourly_temp[0]
    day_collection = {}
    hr_collection = {}
    list_of_hours = []
    list_of_days = []

    # for each timestamp in e.g. temperature list
    for dt_temp, dt_humidity, dt_description, dt_wind in zip(hourly_temp, hourly_humidity, hourly_description, hourly_wind):
        # get this date
        next_date = dt.datetime.utcfromtimestamp(dt_temp[0]).date()

        # if new day, create dict for previous day
        if next_date != prev_date:

            # for first day, use 'today' instead of day of week
            date_collected = dt.datetime.utcfromtimestamp(prev_dt_local[0]).date()
            if date_collected == date_now:
                day_collected = 'Today'
            else:
                dt_day = dt.datetime.utcfromtimestamp(prev_dt_local[0]).weekday()
                day_collected = day_of_week(dt_day)

            # get all hrs of data for day
            list_of_days.append(day_collected)
            day_collection.update({day_collected:hr_collection})

            # reset hr collector
            hr_collection = {}

            prev_date = next_date
            prev_dt_local = dt_temp

            # if required number of days already collected, break loop
            if len(day_collection) == 5:
                break

        # collect all data for this time
        current_hour = dt.datetime.utcfromtimestamp(dt_temp[0]).hour
        list_of_hours.append(current_hour)
        hr_collection.update({current_hour: {'temp': dt_temp[1],
                                             'humidity': dt_humidity[1],
                                             'description': dt_description[1],
                                             'wind': dt_wind[1]}})

    set_of_days = set(list_of_days)
    set_of_hours = set(list_of_hours)

    return day_collection, set_of_days, set_of_hours

# initialise weather data
def initialise_weather_data(mins_before_refresh):

    # try to get last update time
    try:
        # get last update time from .txt file
        file = open('data/last_data_refresh.txt', 'r')
        last_update_time = dt.datetime.strptime(file.read(), '%Y-%m-%dT%H:%M:%S.%f%z')
        file.close()
    # if failed, set default time
    except:
        last_update_time = dt.datetime.strptime('2024-01-01T12:00:00.000000+0000', '%Y-%m-%dT%H:%M:%S.%f%z')

    current_time = dt.datetime.now(dt.timezone.utc)
    refresh_mins = dt.timedelta(minutes=mins_before_refresh)

    # if data old, refresh it OR need new set at 12am
    if current_time - last_update_time > refresh_mins or current_time.date() != last_update_time.date():
        # debug - check websites for initial connection
        check_websites()

        # get 5 day weather for each location
        itinerary_forecast_dfs = get_weather_all()
        with open('data/itinerary_forecast_dfs.pickle', 'wb') as handle:
            pickle.dump(itinerary_forecast_dfs, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # set time of  APIs from .txt file for assignment submission
        file = open('data/last_data_refresh.txt', 'w')
        file.write(str(dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f%z')))
        file.close()

    # if data was retrieved recently, use that data
    else:
        with open('data/itinerary_forecast_dfs.pickle', 'rb') as handle:
            itinerary_forecast_dfs = pickle.load(handle)

    forecast_temps, best_days, weather_summary, set_of_days, set_of_hours = get_forecast_data_all(itinerary_forecast_dfs)

    return itinerary_forecast_dfs, forecast_temps, best_days, weather_summary, set_of_days, set_of_hours




# get API keys from os
def set_API_keys():
    # define the API key dictionary and API key names
    global API_keys
    API_keys = {}
    API_key_names = {'OpenWeather': 'OpenWeather_API_key'}

    # get the API keys from os
    for key in API_key_names:
        API_keys[key] = get_key(API_key_names[key])


# get the locations dictionary and list of dictionary keys
def set_itinerary():
    # create global variables for reuse
    global itinerary_locations, itinerary_location_keys

    # define the locations by their coordinates
    itinerary_locations = {'Cumbria': [54.4609, -3.0886], 'Corfe Castle': [50.6395, -2.0566],
                           'The Cotswolds': [51.8330, -1.8433], 'Cambridge': [52.2053, 0.1218],
                           'Bristol': [51.4545, -2.5879], 'Oxford': [51.7520, -1.2577],
                           'Norwich': [52.6309, 1.2974], 'Stonehenge': [51.1789, -1.8262],
                           'Watergate Bay': [50.4429, -5.0553], 'Birmingham': [52.4862, -1.8904]}

    # get a list of the location keys and sort alphabetically
    itinerary_location_keys = list(itinerary_locations.keys())
    itinerary_location_keys.sort()

    return itinerary_location_keys


# create a class for requests
class GetRequests:
    def make_get_requests(self, url):
        resp = requests.get(url=url)
        if resp.status_code == 200:
            return resp.headers
        else:
            return resp.status_code
