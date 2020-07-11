# Need a utility to draw a map of NYC cases
import statistics
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn import preprocessing
#import geopandas as gpd
import Graphics
from Parameters import SimulationParams
import codecs
import csv


def draw_severity_by_region(location='NYC', file_location='Data/NYC/Case_Death_Recovery/compiled_test_by_zcta.csv'):
    #ugh. best not to ask for file location I guess TODO
    #this is just for pop data retrieval
    file_to_open = Path('Data/NYC/Case_Death_Recovery/data-by-modzcta.csv')
    zip_pop_dict = {}
    with open(file_to_open, 'r') as f:
        """MODIFIED_ZCTA	NEIGHBORHOOD_NAME	BOROUGH_GROUP	COVID_CASE_COUNT	COVID_CASE_RATE	POP_DENOMINATOR	COVID_DEATH_COUNT	COVID_DEATH_RATE	PERCENT_POSITIVE	TOTAL_COVID_TESTS"""
        next(f)
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # MODIFIED_ZCTA
            _ = row_data[1]
            _ = row_data[2]
            _ = row_data[3]
            _ = row_data[4]
            population = float(row_data[5])  # POP_DENOMINATOR
            zip_pop_dict[s_modzcta] = population

    file_to_open = Path(file_location)
    with open(file_to_open, 'r') as f:
        """modzcta	Positive	Total	date"""
        """I'm going to rely on the data being in order. Though some dates may be skipped"""
        """2020-04-01T04:00:00.000Z"""
        # TODO: python has no dynamic matrices wololo
        #  think about how to make this dynamic (pd time series), but not too hard
        case_data = np.zeros((177, 65))
        date_index = []
        zip_index = []
        ignore_zip = ['NA','99999', '10020', '10110', '10111', '10162', '10165', '10170', '10171',
                      '10278', '11005', '11040', '11424', '11430', '' ]  # NYC Y U DO THIS? 10020 has only one entry
        next(f)
        current_date = datetime(2020, 3, 1, 0, 0).date()  # TODO: too lazy to look up right syntax
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # a string for now
            positive_cases = row_data[1] # positive cases
            total_cases = row_data[2]
            date_raw = row_data[3]

            date_raw = date_raw.split('T')[0]
            date = datetime.strptime(date_raw, '%Y-%m-%d').date()

            if s_modzcta in ignore_zip:
                continue

            #increment date if new day
            if date != current_date:
                current_date = date
                date_index.append(current_date.strftime('%Y-%m-%d'))

            if s_modzcta not in zip_index:
                zip_index.append(s_modzcta)
            pop_denom = zip_pop_dict[s_modzcta]

            #TODO: try 7-step MA new cases?
            cur_date_idx = date_index.index(date.strftime('%Y-%m-%d'))
            cur_zip_idx = zip_index.index(s_modzcta)
            case_data[cur_zip_idx][cur_date_idx] = int(positive_cases) / pop_denom

    #print('dates', len(date_index))
    #print('zips', len(zip_index))

    Graphics.draw_geographical_hotspots(data_matrix=case_data, zip_list=zip_index, date_list=date_index)

    return None


#TODO: sure reuses a lot of code from the draw utility
def nyc_case_data_by_modzcta_dict(normalized=True, smoothing=0):
    forecast_dict = {}
    file_to_open = Path('Data/NYC/Case_Death_Recovery/data-by-modzcta.csv')
    zip_pop_dict = {}
    with open(file_to_open, 'r') as f:
        """MODIFIED_ZCTA	NEIGHBORHOOD_NAME	BOROUGH_GROUP	COVID_CASE_COUNT	COVID_CASE_RATE	POP_DENOMINATOR	COVID_DEATH_COUNT	COVID_DEATH_RATE	PERCENT_POSITIVE	TOTAL_COVID_TESTS"""
        next(f)
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # MODIFIED_ZCTA
            _ = row_data[1]
            _ = row_data[2]
            _ = row_data[3]
            _ = row_data[4]
            population = float(row_data[5])  # POP_DENOMINATOR
            zip_pop_dict[s_modzcta] = population

    file_to_open = Path('Data/NYC/Case_Death_Recovery/compiled_test_by_zcta.csv')
    with open(file_to_open, 'r') as f:
        """modzcta	Positive	Total	date"""
        """I'm going to rely on the data being in order. Though some dates may be skipped"""
        """2020-04-01T04:00:00.000Z"""
        case_data = np.zeros((177, 65))
        date_index = []
        zip_index = []
        ignore_zip = ['NA','99999', '10020', '10110', '10111', '10162', '10165', '10170', '10171',
                      '10278', '11005', '11040', '11424', '11430', '' ]  # NYC Y U DO THIS? 10020 has only one entry
        #should also ignore zip where there are no subway stations
        next(f)
        current_date = datetime(2020, 3, 31, 0, 0).date()  # TODO: too lazy to look up right syntax
        stop_date = datetime(2020, 6, 8, 0, 0).date() #100 days from march 1

        skip_date_1 = datetime(2020, 4, 26, 0, 0).date() #The data from april 26 is faulty.

        max_idx = 0
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # a string for now
            positive_cases = row_data[1]  # positive cases
            total_cases = row_data[2]
            date_raw = row_data[3]

            if s_modzcta in ignore_zip:
                continue

            if s_modzcta not in forecast_dict.keys():
                forecast_dict[s_modzcta]=[]
            date_raw = date_raw.split('T')[0]
            date = datetime.strptime(date_raw, '%Y-%m-%d').date()

            if date == skip_date_1:
                continue

            if date > current_date + timedelta(days=1): #timeskip
                delta = date - current_date
                for i in range(1, delta.days):
                    for key in forecast_dict:
                        last_entry = forecast_dict[key][-1]
                        forecast_dict[key].append(last_entry)
                current_date = date
                max_idx += delta.days
            # use yesterday's date as time series
            elif date == current_date + timedelta(days=1): #new day
                current_date = date
                max_idx += 1

            if len(forecast_dict[s_modzcta]) >= max_idx: #already had an entry for today
                continue

            pop_denom = zip_pop_dict[s_modzcta]
            case_rate = int(positive_cases) / pop_denom
            if normalized:
                forecast_dict[s_modzcta].append(case_rate)
            else:
                forecast_dict[s_modzcta].append(int(positive_cases))

    return forecast_dict

def calculate_MAPE(actual=[],forecast=[], min_interval = 30): #TODO: very little validation
    total_err = 0.00
    interval = len(actual)
    if interval > min_interval:
        for i in range(min_interval, interval):
            val_actual = actual[i]
            val_forecast = forecast[i]
            err = abs(val_actual - val_forecast) / val_actual
            total_err += err

        return total_err / (interval - min_interval)
    else:
        return 0.00

def calculate_MAPE_by_zip(actual={}, forecast={}, offset=32, print_results=False):
    mape_dict = {}
    for key in actual.keys():
        if key in forecast.keys():
            actual_values = actual[key]
            forecast_values = forecast[key][offset:] #31 days of march + initial
            if len(actual_values) != len(forecast_values):
                print('sizing error for', key, len(actual_values), len(forecast_values))
            else:
                total_err = 0
                for i in range(0, len(actual_values)):
                    val_actual = actual_values[i]
                    val_forecast = forecast_values[i]
                    if val_actual == 0:
                        print('bad key-val:', key, i, val_actual, val_forecast)
                        val_actual += 1e-9
                    err = abs(val_actual - val_forecast) / val_actual
                    total_err += err
                mape_dict[key] = total_err / len(actual_values)
    if print_results:
        print('Mean Regional MAPE:', sum(mape_dict.values()) / len(mape_dict.keys()))
        print('Median MAPE:', statistics.median(mape_dict.values()))
    return mape_dict


def NYC_turnstile_script():
    dirpath = "Data/NYC/Subway/"
    # Combine it all into one dataframe
    filenames = ['turnstile_200222.txt', 'turnstile_200229.txt', 'turnstile_200307.txt']

    file_list = []
    for file in filenames:
        file_to_open = Path(dirpath + file)
        df = pd.read_csv(file_to_open, index_col=None, header=0)
        file_list.append(df)
    turnstile_data = pd.concat(file_list, axis=0, ignore_index=True)

    # Remove extraneous data and remove non Subway lines like the PATH and Staten Island Railway
    turnstile_data.drop(["C/A", "SCP", "DESC", "LINENAME"], axis=1, inplace=True)
    turnstile_data.columns = ['UNIT', 'STATION', 'DIV', 'DATE', 'TIME', 'ENTRIES', 'EXITS']
    turnstile_data = turnstile_data[turnstile_data.DIV != "SRT"]
    turnstile_data = turnstile_data[turnstile_data.DIV != "RIT"]
    turnstile_data = turnstile_data[turnstile_data.DIV != "PTH"]
    turnstile_data.drop(["DIV"], axis=1, inplace=True)

    # Reformat the date and time creating a Pandas datetime
    turnstile_data['DATETIME'] = turnstile_data.DATE + ' ' + turnstile_data.TIME
    turnstile_data['DATETIME'] = pd.to_datetime(turnstile_data['DATETIME'], format='%m/%d/%Y %H:%M:%S')
    turnstile_data.drop(["DATE", "TIME", "STATION"], axis=1, inplace=True)

    # Because the exits and entries are cumulative, difference them
    turnstile_data.ENTRIES = turnstile_data.ENTRIES.diff()
    turnstile_data.EXITS = turnstile_data.EXITS.diff()

    # Remove negative numbers and extreme outliers
    turnstile_data = turnstile_data[turnstile_data.ENTRIES >= 0]
    turnstile_data = turnstile_data[turnstile_data.EXITS >= 0]
    turnstile_data = turnstile_data[turnstile_data.ENTRIES <= turnstile_data.ENTRIES.quantile(.99)]
    turnstile_data = turnstile_data[turnstile_data.EXITS <= turnstile_data.EXITS.quantile(0.99)]

    # Write out cleaned data to csv
    turnstile_data.to_csv(dirpath + "nonaveraged_turnstile_data.csv", index=False)

    turnstile_data['DATETIME'] = pd.to_datetime(turnstile_data['DATETIME'], format='%Y/%m/%d %H:%M:%S')
    turnstile_data = turnstile_data.groupby(['UNIT', 'DATETIME'], as_index=True).aggregate('sum')

    # Because the readings are every few hours, there are gaps in time. Moreover the timings don't match for each station. Thus we should interpolate and fill in the gaps.
    turnstile_data = turnstile_data.groupby(level=0).apply(
        lambda x: x.reset_index(level=0, drop=True).resample("1H").interpolate(method='linear'))

    # Group and average the times so instead of days over years, we have an average for every hour of the day of week
    turnstile_data.reset_index(inplace=True)
    turnstile_data['HOUR'] = turnstile_data.DATETIME.dt.hour
    turnstile_data['DAYOFWEEK'] = turnstile_data.DATETIME.dt.dayofweek
    turnstile_data = turnstile_data.drop(['DATETIME'], axis=1)
    turnstile_data = turnstile_data.groupby(['UNIT', 'DAYOFWEEK', 'HOUR'], as_index=False).mean()

    # Normalize the Data across the Averaged Times as we don't want things like general population density to interfere
    entries = turnstile_data[['ENTRIES']].values.astype(float)
    entries_min_max_scaler = preprocessing.MinMaxScaler()
    entries_scaled = entries_min_max_scaler.fit_transform(entries)
    turnstile_data['NORMALIZED_ENTRIES'] = entries_scaled

    exits = turnstile_data[['EXITS']].values.astype(float)
    exits_min_max_scaler = preprocessing.MinMaxScaler()
    exits_scaled = exits_min_max_scaler.fit_transform(exits)
    turnstile_data['NORMALIZED_EXITS'] = exits_scaled

    turnstile_data['INTENSITY'] = turnstile_data['NORMALIZED_EXITS'] - turnstile_data['NORMALIZED_ENTRIES']
    turnstile_data = turnstile_data.drop(['NORMALIZED_ENTRIES', 'NORMALIZED_EXITS', 'ENTRIES', 'EXITS'], axis=1)

    # Merge the data with the Stations data to get geometry
    station_ids_with_unit_ids = pd.read_csv("data/station_data/stations.csv")
    turnstile_data = turnstile_data.merge(station_ids_with_unit_ids, on="UNIT")
    turnstile_data = turnstile_data.drop(['UNIT'], axis=1)
    turnstile_data = turnstile_data.drop_duplicates()

    # Write out the data to csv
    turnstile_data.to_csv(dirpath + "averaged_turnstile_data.csv", index=False)


def get_benchmark_statistics(location, start_date, duration, case_data, valid_zip_codes):
    benchmark_stats = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 5))
    # don't have to kludge data... NICE
    if location == SimulationParams.MAP_TYPE_LONDON:
        for i in range(0, SimulationParams.RUN_SPAN):
            total_infected = 0
            for k,v in case_data.items():
                total_infected += v[i]
            time = i+1
            benchmark_stats[time, 0] = time
            benchmark_stats[time, 2] = total_infected - benchmark_stats[time-1, 3]
            benchmark_stats[time, 3] = total_infected

        #TODO: bit of a hack to get zeroth entry not so far off
        benchmark_stats[0, 2] = benchmark_stats[1, 2]
        benchmark_stats[0, 3] = benchmark_stats[1, 3]

        return benchmark_stats

    '''https://www1.nyc.gov/site/doh/covid/covid-19-data.page'''
    if location == 'NYC':
        # TODO: and the kludging starts here (by ignoring start date and just pulling data)
        # TODO: build benchmarking statistics from the same data source
        # (which is compiled_test_by_zcta w/o zip codes that have no subway stations
        # we can use the simple data divided by 6/7 (normalizing for population) until april 1

        file_to_open = Path('Data/NYC/Case_Death_Recovery/covid_nyc_simple.csv')
        with open(file_to_open, 'r') as f:
            next(f)  # skip header row
            time = 0
            total_infected = 0
            for row in f:
                if time == SimulationParams.RUN_SPAN + 1:
                    break
                infection_data = row.strip().split(',')
                date = infection_data[0]
                infected = int(infection_data[1]) / 2.5 # TODO: Note! /=2 to fit data
                total_infected += infected
                benchmark_stats[time, 0] = time
                benchmark_stats[time, 2] = infected
                benchmark_stats[time, 3] = total_infected
                time += 1

        for i in range(0, SimulationParams.RUN_SPAN - duration):
            time = i + duration + 1
            total_infected = 0

            for k,v in case_data.items():
                if k in valid_zip_codes:
                    total_infected += v[i]
            benchmark_stats[time, 0] = time
            benchmark_stats[time, 2] = total_infected - benchmark_stats[time-1, 3]
            benchmark_stats[time, 3] = total_infected

        pd.DataFrame(benchmark_stats).to_csv("debug.csv")
        return benchmark_stats
    return None

def london_case_data_by_borough_dict(normalized=True, smoothing=0):
    #Get Population Data
    borough_pop_dict = {}
    actual_case_rate_dict = {}

    file_to_open = Path('Data/London/Case Data/london_pop_by_borough.csv')
    with open(file_to_open, 'r') as f:
        next(f)
        for row in f:
            borough_data = row.replace('\n', '').split(',')
            borough_name = borough_data[0]
            borough_population = int(borough_data[1])

            borough_pop_dict[borough_name] = borough_population

    start_date = datetime(2020, 3, 1, 0, 0).date()
    end_date = datetime(2020, 6, 30, 0, 0).date()
    # Get Case Data\
    file_to_open = Path('Data/London/Case Data/london_case_data.csv')
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        csv_reader = csv.reader(f, delimiter=',', quotechar='"') #TODO, really this should be done everywhere
        # We assume the file is in date order
        # TODO: we're also going to just set the timespan to 31 + 30 + 31 + 30 = 122 days for now.
        """Area name,Area code,Area type,Specimen date,Daily lab-confirmed cases,Previously reported daily cases,
        Change in daily cases,Cumulative lab-confirmed cases,Previously reported cumulative cases,Change in cumulative cases,Cumulative lab-confirmed cases rate"""
        """England	E92000001	Nation	2020-01-30	2	2	0	2	2	0	0"""
        next(f)
        for area_data in csv_reader:
            area_name = area_data[0]
            _ = area_data[1]
            area_type = area_data[2]
            area_date_raw = area_data[3]
            _ = area_data[4]  # daily cases
            _ = area_data[5]  # previous cases
            _ = area_data[6]  # changes in cases
            area_cumulative_cases = int(area_data[7]) # cumulative cases
            current_date = datetime.strptime(area_date_raw, '%Y-%m-%d').date()
            if current_date < start_date or current_date > end_date:
                continue

            number_of_entries = (current_date - start_date).days + 1

            if area_type != 'Upper tier local authority':
                continue
            if area_name in ['Bexley', 'Bromley', 'Croydon', 'Kingston upon Thames', 'Sutton']: #skip areas with no stations
                continue

            if area_name == 'Hackney and City of London':
                area_name = 'Hackney'  # TODO: Eliminate city of London from calculations

            if area_name in borough_pop_dict.keys():
                actual_case_rate_dict.setdefault(area_name, [])
                entries = actual_case_rate_dict[area_name]
                if normalized:
                    entry_to_add = area_cumulative_cases / borough_pop_dict[area_name]
                else:
                    entry_to_add = area_cumulative_cases

                while len(entries) < number_of_entries:
                    entries.append(entry_to_add)

    for key in actual_case_rate_dict.keys():
        while len(actual_case_rate_dict[key]) < (end_date - start_date).days + 1:
            actual_case_rate_dict[key].append(actual_case_rate_dict[key][-1])

    return actual_case_rate_dict





    return None
