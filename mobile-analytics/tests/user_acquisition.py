import sys
import pandas as pd

sys.path.append("..")
from stats.acquisition import user_acquisition_dict


df = pd.DataFrame({'distinct_id': [1, 1, 2, 3, 4],
                   'name': ['download', 'signUp', 'logIn', 'UpdateAddress', 'CheckOut'],
                   'properties': ['{}', '{}', '{}', '{}', '{}'],
                   'time': ['2019-01-01 13:00:00', '2019-01-01 13:01:10', '2019-01-01 13:15:00', '2019-01-06 16:39:42',
                            '2019-01-06 17:00:00']})
df['time'] = pd.to_datetime(df['time']).astype('datetime64')


if __name__ == '__main__':
    dict_ = user_acquisition_dict(df, acquisition_event_name='signUp')
    df['acq_time'] = df['distinct_id'].map(dict_)
    print(dict_)
    print(df.to_string())
    print(df.dtypes)

