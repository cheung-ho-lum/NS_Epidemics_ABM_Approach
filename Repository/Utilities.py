# Need a utility to draw a map of NYC cases
from datetime import datetime
from pathlib import Path
import numpy as np

import Graphics


def draw_severity_by_region(location='NYC', file_location='Data/NYC/Case_Death_Recovery/compiled_test_by_zcta.csv'):
    file_to_open = Path(file_location)
    with open(file_to_open, 'r') as f:
        """modzcta	Positive	Total	date"""
        """I'm going to rely on the data being in order. Though some dates may be skipped"""
        """2020-04-01T04:00:00.000Z"""
        # TODO: python has no dynamic matrices wololo
        #  think about how to make this dynamic (pd time series), but not too hard
        case_data = np.zeros((178, 65))
        date_index = []
        zip_index = []
        ignore_zip = ['99999', '10020', '10110', '10111', '10162', '10165', '10170', '10171',
                      '10278', '11005', '11040', '11424', '11430', '' ]  # NYC Y U DO THIS? 10020 has only one entry
        next(f)
        current_date = datetime(2020, 3, 1, 0, 0).date() # TODO: too lazy to look up right syntax
        for row in f:
            row_data = row.split(',')
            s_modzcta = row_data[0]  # a string for now
            _ = row_data[1] # positive cases
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

            case_data[zip_index.index(s_modzcta)][date_index.index(date.strftime('%Y-%m-%d'))] = int(total_cases)

    #print('dates', len(date_index))
    #print('zips', len(zip_index))

    Graphics.draw_geographical_hotspots(data_matrix=case_data, zip_list=zip_index, date_list=date_index)

    return None