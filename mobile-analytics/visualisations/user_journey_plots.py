from stats.user_journey import sankey_df


def plot_user_flow(events, starting_step, n_steps=3, events_per_step=5, title='Sankey Diagram'):
    """
    Function used to generate the sankey plot for user journeys.

    :param events: (DataFrame)
                    Mixpanel events dataframe

    :param starting_step: (str)
                    the event which should be considered as the starting point of the user journey.

    :param n_steps: (int)
                    number of events to return

    :param events_per_step: (int)
                    number of events to show per step.
                    The rest (less frequent) events will be grouped together into an "Other" block.

    :param title: (str)
                    Title for the plot

    :return: (plotly fig)
    """
    # transform raw events dataframe into  source:target pairs including node ids and count of each combination
    label_list, colors_list, source_target_df = sankey_df(events, starting_step, n_steps, events_per_step)

    # creating the sankey diagram
    data = dict(
        type='sankey',
        node=dict(
            pad=20,
            thickness=20,
            color=colors_list,
            line=dict(
                color="black",
                width=0.5
            ),
            label=label_list
        ),
        link=dict(
            source=source_target_df['source_id'].values.tolist(),
            target=source_target_df['target_id'].values.tolist(),
            value=source_target_df['count'].astype(int).values.tolist(),
            hoverlabel=dict(
                bgcolor='#C2C4C7')
        )
    )

    # set window width
    if n_steps < 5:
        width = None
    else:
        width = n_steps * 250

    layout = dict(
        height=600,
        width=width,
        margin=dict(t=30, l=0, r=0, b=30),
        #         autosize=True,
        title=title,
        font=dict(
            size=10
        )
    )

    fig = dict(data=[data], layout=layout)
    return fig
