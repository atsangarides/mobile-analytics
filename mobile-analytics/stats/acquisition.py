from pandas import DataFrame
import numpy as np


def user_acquisition_dict(events, acquisition_event_name):
    """
    Function used to generate a dict with "distinct_id": "acquisition_time" key:value pairs.

    :param events: (DataFrame)
                        events dataframe

    :param acquisition_event_name: (str)
                        event name defining the user acquisition point

    :return acquisition: (dict)
                        "distinct_id": "acquisition_time" pairs
    """
    if not isinstance(events, DataFrame):
        raise TypeError('"events" should be a pandas dataframe')

    if not isinstance(acquisition_event_name, str):
        raise TypeError('"acquisition_event_name" should be a string')

    if acquisition_event_name not in events['name'].unique():
        raise ValueError('"acquisition_event_name" should be a valid event present in the events dataframe')

    # get the acquisition time for eah distinct_id
    acquisition = events[events['name'] == acquisition_event_name] \
        .sort_values('time') \
        .drop_duplicates(subset='distinct_id', keep='first')[['distinct_id', 'time']]

    # convert df to a dict
    acquisition = dict(zip(acquisition['distinct_id'], acquisition['time']))

    return acquisition


def acquisition_events_cohort(events, acquisition_event_name, period='w', month_fmt='period'):
    """
    Function used to add "cohort", "event_period", "user_active" and "user_returns" columns.
    "cohort" is the weekly/monthly period that the user generated a successful plan (user acquired).
    "event_period" is the cohort that any event belongs in.
    "user_active" is True if the event took place at or after the user's acquisition time, False otherwise.
    "user_returns" is True if the event took place during a period subsequent to the acquisition cohort,
    False otherwise.

    :param events: (DataFrame)
                        events dataframe

    :param acquisition_event_name: (str)
                        event name defining the user acquisition point

    :param period: (str)
                        str denoting period for cohort breakdown.
                        Use 'd' for daily, 'w' for weekly or 'm' for monthly

    :param month_fmt: (str)
                        str denoting format for monthly date.
                        Use 'period' for %Y-%m and 'datetime' for datetime like.

    :return events: (DataFrame)
    """
    assert period in ['d', 'w', 'm'], '"period" should be either "d", "w" or "m"'

    if month_fmt:
        assert month_fmt in ['period', 'datetime'], '"month_fmt" should be either "period" or "datetime"'

    # create user acquisition dict and get all unique acquired users
    acquisition_dict = user_acquisition_dict(events, acquisition_event_name)
    acquired_users = acquisition_dict.keys()

    # filter events dataframe for only acquired users (filter out leads)
    events = events[events['distinct_id'].isin(acquired_users)].copy()

    # get acquisition time for each user and create a "cohort" column
    events['acquisition_time'] = events['distinct_id'].map(acquisition_dict)

    # create the "cohort" and "event_period" columns, based on the period defined
    if period == 'd':
        events['cohort'] = events['acquisition_time'].dt.date
        events['event_period'] = events['time'].dt.date

    elif period == 'w':
        events['cohort'] = (events['acquisition_time'] - events['acquisition_time'] \
                            .dt.weekday.astype('timedelta64[D]')).astype('datetime64[D]')

        events['event_period'] = (events['time'] - events['time'] \
                                  .dt.weekday.astype('timedelta64[D]')).astype('datetime64[D]')

    else:
        # if monthly period, choose between pandas period type and datetime type
        # period type has a nice monthly format and is fine for aggregations
        # datetime would show up as first/last day of the month (yyyy-mm-dd),
        # but easier to work with for further manipulations
        # datetime type will be more useful later
        if month_fmt == 'period':
            events['cohort'] = events['acquisition_time'].dt.to_period('M')
            events['event_period'] = events['time'].dt.to_period('M')

        elif month_fmt == 'datetime':
            events['cohort'] = events['acquisition_time'].dt.date.astype('datetime64[M]')
            events['event_period'] = events['time'].dt.date.astype('datetime64[M]')

    # indicate if the user did any action at or after his/her acquisition time
    # if you do not want to count same-day activity replace following line with:
    # events['user_active'] = (events['time'].dt.date > events['acquisition_time'].dt.date)
    events['user_active'] = (events['time'] >= events['acquisition_time'])

    # indicate if the user returned in any period subsequent to his/her acquisition cohort
    events['user_returns'] = (events['event_period'] > events['cohort'])

    return events


def users_per_period(events, acquisition_event_name, user_source_col, period='w', month_fmt='period'):
    """
    Function used to group new users into period cohorts.
    The first time a user generates a plan is treated as the acquisition time.

    :param events: (DataFrame)
`                       Mixpanel events dataframe

    :param acquisition_event_name: (str)
                        event name defining the user acquisition point

    :param user_source_col: (str)
                        name of column defining if user is an Organic/Non-organic acquisition

    :param period: (str)
                    str denoting period for cohort breakdown. use 'w' for weekly and 'm' for monthly

    :param month_fmt: (str)
                    str denoting format for monthly date. Use 'period' for %Y-%m and 'datetime' for datetime like.

    :return:
    """
    if user_source_col:
        assert hasattr(events, user_source_col), '"user_source_col" should be a column in the events dataframe'

    # calculate the cohort for each user and period for each event
    events = acquisition_events_cohort(events, acquisition_event_name, period=period, month_fmt=month_fmt)

    # will be used to rename the period column of each groupby result
    period_name = {'w': 'Week Starting',
                   'm': "Month"}

    # calculate size of each users cohort
    new_users = events.drop_duplicates(subset=['distinct_id', 'cohort']) \
        .groupby(['cohort']).size() \
        .reset_index() \
        .rename({0: 'New Users (Total)', 'cohort': period_name[period]}, axis=1) \
        .set_index(period_name[period])

    # break down new users into Organic/Non-organic
    if user_source_col:
        source = events[events['name'] == acquisition_event_name] \
            .groupby(['cohort', 'user_source'])['distinct_id'] \
            .nunique() \
            .reset_index() \
            .rename({'distinct_id': 'New Users', 'cohort': period_name[period]}, axis=1) \
            .set_index(period_name[period])

        source = source.pivot(columns='user_source', values='New Users')[['Organic', 'Non-organic']] \
            .rename({'Organic': 'New Organic Users', 'Non-organic': 'New Paid Users'}, axis=1)

    # calculate number of active users per period
    active_users = events[events['user_active']] \
        .groupby(['event_period'])['distinct_id'].nunique() \
        .reset_index() \
        .rename({'distinct_id': 'Active Users', 'event_period': period_name[period]}, axis=1) \
        .set_index(period_name[period])

    # calculate number of returning users per period
    returning_users = events[events['user_returns']] \
        .groupby(['event_period'])['distinct_id'].nunique() \
        .reset_index() \
        .rename({'distinct_id': 'Returning Users', 'event_period': period_name[period]}, axis=1) \
        .set_index(period_name[period])

    # merge into a single dataframe
    if user_source_col:
        df = new_users.join([source, active_users, returning_users], how='outer', sort=False).astype('Int64').copy()
    else:
        df = new_users.join([active_users, returning_users], how='outer', sort=False).astype('Int64').copy()
    df.fillna(0, inplace=True)

    # calculate period-on-period growth
    df['W/W Growth'] = df['New Users (Total)'].pct_change().apply(lambda x: "{0:.2f}%".format(x * 100))
    df['N/R Ratio'] = (df['New Users (Total)'] / df['Returning Users']) \
        .fillna(0) \
        .replace(np.inf, np.nan) \
        .apply(lambda x: "{0:.1f}".format(x))

    return df

