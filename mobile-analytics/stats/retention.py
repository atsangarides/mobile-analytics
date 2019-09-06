import pandas as pd
import numpy as np
from .acquisition import acquisition_events_cohort


def cohort_period(df):
    """
    Creates a `cohort_period` column, which is the Nth period based on the user's acquisition date.
    """
    df['cohort_period'] = np.arange(len(df))
    return df


def mask_retention_table(dim):
    """
    Function used to fill NaN values with 0 above the diagonal line of the retention table and force
    the rest to be NaN.

    :param dim: (tuple)
                shape of retention dataframe (rows,columns)

    :return: (np.array)
                array used to mask which elements of the retention table can have values
    """
    # create an array of the same shape as the df and assign all elements =True
    mask = np.full(dim, True)

    # assign False where period for each row would no exist
    # i.e. if we have 10 weeks, the 1st week would have data for the next 9 weeks but the 2nd week would
    # only have data for the next 8 weeks, etc...
    for row in range(mask.shape[0]):
        mask[row, :mask.shape[0] - row] = False

    return mask


def retention_table(events, period='w', month_fmt='period', event_filter=None):
    """
    Function used to generate retention stats split into weekly cohorts

    :param events: (DataFrame)
                    Mixpanel events dataframe

    :param period: (str)
                    str denoting period for cohort breakdown. use 'w' for weekly and 'm' for monthly

    :param month_fmt: (str)
                    str denoting format for monthly date. Use 'period' for %Y-%m and 'datetime' for datetime like.

    :param event_filter: (str)
                    mixpanel event to filter for

    :return: (DataFrame)
    """
    assert period in ['w', 'm'], '"period" should be either "w" or "m"'
    if event_filter:
        assert event_filter in events['name'].unique(), '"event_filter" should be a valid event present in "events"'

    # filter out internal testers and get acquisition time of each user
    # create an event_period column for each event
    # determine if each event happened at least 1 day after the user acquisition
    events = acquisition_events_cohort(events, period=period, month_fmt=month_fmt)

    # calculate size of each users cohort
    cohort_sizes = events.drop_duplicates(subset=['distinct_id', 'cohort']).cohort.value_counts() \
        .to_frame() \
        .rename({'cohort': 'size'}, axis=1)
    cohort_sizes.index.rename('cohort', inplace=True)

    # filter only for events after acquisition date
    events = events[events['plan_user_active']]
    # filter for event of interest
    if event_filter:
        events = events[events['name'] == event_filter]

    grouped = events.groupby(['cohort', 'event_period'])

    # count the unique users per Group + Period
    cohorts = grouped.agg({'distinct_id': pd.Series.nunique})
    # reindex the "cohort" (and "event_period" columns) to avoid empty weeks causing misalignment
    # grab the minimum 'cohort' date and maximum 'event_period' date
    start, end = cohorts.index.get_level_values('cohort').min(), \
                 cohorts.index.get_level_values('event_period').max()

    # TODO: if more periods will be considered need to add more here
    if period == 'w':
        full_index = pd.date_range(start=start, end=end, freq='W-MON', name='cohort')
    elif period == 'm':
        if month_fmt == 'period':
            full_index = pd.date_range(start=start.to_timestamp(), end=end.to_timestamp(), freq='MS')
        elif month_fmt == 'datetime':
            full_index = pd.date_range(start=start, end=end, freq='MS')
    cohorts.reset_index(inplace=True)

    # create all possible combinations of possible date periods
    # date_period needs to be equal to or greater than cohort
    possible_dates = []
    for i in range(len(full_index)):
        for j in range(len(full_index)):
            if i <= j:
                possible_dates.append((i, j))

    # fill in missing combinations of cohort and event_period
    # add a new row in the df for a combination of possible dates with value=0
    for combo in possible_dates:
        if len(cohorts[(cohorts['cohort'] == full_index[combo[0]]) &
                       (cohorts['event_period'] == full_index[combo[1]])]) < 1:
            cohorts = cohorts.append({'cohort': full_index[combo[0]],
                                      'event_period': full_index[combo[1]],
                                      'distinct_id': 0},
                                     ignore_index=True) \
                .sort_values(['cohort', 'event_period'])
    cohorts = cohorts.set_index(['cohort', 'event_period'])

    # create 'cohort_period' column
    cohorts = cohorts.astype(str).groupby(level=0).apply(cohort_period)

    # reindex the DataFrame
    cohorts.reset_index(inplace=True)
    cohorts.set_index(['cohort', 'cohort_period'], inplace=True)

    # create user_retention df
    user_retention = cohorts['distinct_id'].unstack(0).T
    # include the cohort size as a secondary index
    user_retention = user_retention.join(cohort_sizes, how='outer', sort=False)
    user_retention['size'].fillna(0, inplace=True)
    user_retention['size'] = user_retention['size'].astype(int)
    user_retention.set_index('size', append=True, inplace=True)
    user_retention.columns.name = 'cohort_period'
    # convert float to Int64
    user_retention = user_retention[user_retention.columns].replace('NaN', np.NaN) \
        .astype('float64')
    # .astype('Int64')

    # convert to percentages
    user_retention_pct = user_retention.divide(user_retention.index.get_level_values('size'), axis='rows')

    # fill NaNs with 0 where a value is possible to exist
    mask_array = mask_retention_table(user_retention.shape)
    user_retention = user_retention.fillna(0).mask(mask_array)
    user_retention_pct = user_retention_pct.fillna(0).mask(mask_array)

    return user_retention, user_retention_pct