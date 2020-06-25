# Need a utility to draw a map of NYC cases
from datetime import datetime
from datetime import timedelta
from pathlib import Path
import numpy as np

import Graphics


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
def nyc_case_data_to_modzcta_forecast_dict():
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
        max_idx = 0
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # a string for now
            positive_cases = row_data[1] # positive cases
            total_cases = row_data[2]
            date_raw = row_data[3]

            if s_modzcta in ignore_zip:
                continue


            if s_modzcta not in forecast_dict.keys():
                forecast_dict[s_modzcta]=[]
            date_raw = date_raw.split('T')[0]
            date = datetime.strptime(date_raw, '%Y-%m-%d').date()

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
            forecast_dict[s_modzcta].append(case_rate)

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
            actual_values = actual[key][offset:]
            forecast_values = forecast[key]
            if len(actual_values) != len(forecast_values):
                print('sizing error for', key, len(actual_values), len(forecast_values))
            else:
                total_err = 0
                for i in range(0, len(actual_values)):
                    val_actual = actual_values[i]
                    val_forecast = forecast_values[i]
                    err = abs(val_actual - val_forecast) / val_actual
                    total_err += err
                mape_dict[key] = total_err / len(actual_values)
    if print_results:
        total_mape = 0
        for k in mape_dict:
            total_mape += mape_dict[k]
        print('Average Regional MAPE:', total_mape / len(mape_dict.keys()))
    return mape_dict