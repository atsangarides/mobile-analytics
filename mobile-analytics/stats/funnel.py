import pandas as pd


def create_funnel_df(df, steps, from_date=None, to_date=None, step_interval=0):
    """
    Function used to create a dataframe that can be passed to functions for generating funnel plots

    :param df: (pd.DataFrame)
                    events df having 'distinct_id' and 'name' columns

    :param steps: (list)
                    list containing funnel steps as strings

    :param from_date: (str)
                    date with format "yyyy-mm-dd"

    :param to_date: (str)
                    date with format "yyyy-mm-dd"

    :param step_interval: (pd.Timedelta)
                    for more info:
                    https://pandas.pydata.org/pandas-docs/version/0.23.4/generated/pandas.Timedelta.html

    :return: (pd.DataFrame)
                df with 'step', 'val', 'pct', 'val-1' columns
    """
    assert isinstance(steps, list), '"steps" should be a list of strings'

    if step_interval != 0:
        assert isinstance(step_interval, pd.Timedelta), \
            '"step_interval" should be a valid pd.Timedelta object. For more info visit:' \
            'https://pandas.pydata.org/pandas-docs/version/0.23.4/generated/pandas.Timedelta.html'

    # filter df for only events in the steps list
    df = df[['distinct_id', 'name', 'time']]
    df = df[df['name'].isin(steps)]

    values = []
    # create a dict to hold the filtered dataframe of each step
    dfs = {}
    # for each step, create a df and filter only for that step
    for i, step in enumerate(steps):
        if i == 0:

            # filter for users that did the 1st event and find the minimum time
            dfs[step] = df[df['name'] == step] \
                .sort_values(['distinct_id', 'time'], ascending=True) \
                .drop_duplicates(subset=['distinct_id', 'name'], keep='first')

            # filter df of 1st step according to dates
            # this will allow the 1st step to have started during the defined period
            # but subsequent steps are allowed to occur at a later date so that the funnel
            # is not penalised unfairly
            if from_date:
                dfs[step] = dfs[step][(dfs[step]['time'] >= from_date)]

            if to_date:
                dfs[step] = dfs[step][(dfs[step]['time'] <= to_date)]

        else:
            # filter for specific event
            dfs[step] = df[df['name'] == step]

            # left join with previous step
            # this ensures only rows for which the distinct_ids appear in the previous step
            merged = pd.merge(dfs[steps[i - 1]], dfs[step], on='distinct_id', how='left')

            # keep only events that happened after previous step and sort by time
            merged = merged[merged['time_y'] >=
                            (merged['time_x'] + step_interval)].sort_values('time_y', ascending=True)

            # take the minimum time of the valid ones for each user
            merged = merged.drop_duplicates(subset=['distinct_id', 'name_x', 'name_y'], keep='first')

            # keep only the necessary columns and rename them to match the original structure
            merged = merged[['distinct_id', 'name_y', 'time_y']].rename({'name_y': 'name',
                                                                         'time_y': 'time'}, axis=1)

            # include the df in the df dictionary so that it can be joined to the next step's df
            dfs[step] = merged

        # append number of users to the "values" list
        values.append(len(dfs[step]))

    # create dataframe
    funnel_df = pd.DataFrame({'step': steps, 'val': values})

    return funnel_df


def group_funnel_dfs(events, steps, col):
    """
    Function used to create a dict of funnel dataframes used to generate a stacked funnel plot


    :param events: (DataFrame)
                    events dataframe

    :param steps: (list)
                    list containing funnel steps as strings

    :param col: (str)
                    column to be used for grouping the funnel dataframes

    :return: (dict)
                    dict of dataframes
    """
    assert isinstance(events, pd.DataFrame), '"events" should be a pandas dataframe'
    assert isinstance(col, str), '"col" should be a string'
    assert hasattr(events, col), '"col" should be a column in "events"'

    dict_ = {}
    # get the distinct_ids for each property that we are grouping by
    ids = dict(events.groupby([col])['distinct_id'].apply(set))

    for entry in events[col].dropna().unique():
        ids_list = ids[entry]
        df = events[events['distinct_id'].isin(ids_list)].copy()
        if len(df[df['name'] == steps[0]]) > 0:
           dict_[entry] = create_funnel_df(df, steps)

    return dict_
