from plotly import graph_objs as go
from ..stats.funnel import create_funnel_df, group_funnel_dfs


def plot_stacked_funnel(events, steps, col=None, from_date=None, to_date=None, step_interval=0):
    """
    Function used for producing a funnel plot

    :param events: (DataFrame)
                    events dataframe

    :param steps: (list)
                    list containing funnel steps as strings

    :param col: (str)
                    column to be used for grouping the funnel dataframes

    :return: (plt.figure) funnel plot
    """

    # create list to append each trace to
    # this will be passed to "go.Figure" at the end
    data = []

    # if col is provided, create a funnel_df for each entry in the "col"
    if col:
        # generate dict of funnel dataframes
        dict_ = group_funnel_dfs(events, steps, col)
        title = 'Funnel plot per {}'.format(col)
    else:
        funnel_df = create_funnel_df(events, steps, from_date=from_date, to_date=to_date, step_interval=step_interval)
        dict_ = {'Total': funnel_df}
        title = 'Funnel plot'

    for t in dict_.keys():
        trace = go.Funnel(
            name=t,
            y=dict_[t].step.values,
            x=dict_[t].val.values,
            textinfo="value+percent previous"
        )
        data.append(trace)

    layout = go.Layout(margin={"l": 180, "r": 0, "t": 30, "b": 0, "pad": 0},
                       funnelmode="stack",
                       showlegend=True,
                       hovermode='closest',
                       title='Funnel plot per {}'.format(col),
                       legend=dict(orientation="v",
                                   bgcolor='#E2E2E2',
                                   xanchor='left',
                                   font=dict(
                                       size=12)
                                   )
                       )

    return go.Figure(data, layout)
