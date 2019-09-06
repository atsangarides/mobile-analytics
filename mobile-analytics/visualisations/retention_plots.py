import seaborn as sns
import matplotlib.pyplot as plt


def retention_heatmap(df, figsize=(12, 6), type='val'):
    """
    Function used to plot retention heatmaps.

    :param df: (dataframe)
                dataframe resembling the retention table

    :param figsize: (tuple)
                    (width, height)

    :param type: (str)
                    either "val" or "perc"

    :return:
    """
    sns.set()

    # used to set the number format (values vs percentages)
    if type == 'val':
        values_fmt = '.0f'
    else:
        values_fmt = '.0%'

    plt.figure(figsize=figsize)
    h = sns.heatmap(df,
                    cmap='Blues',
                    annot=True,
                    yticklabels=list(zip(df.index.get_level_values(0).strftime('%Y-%m-%d').values,
                                         df.index.get_level_values(1))),
                    annot_kws={'fontsize': 14},
                    fmt=values_fmt)
    plt.yticks(rotation=0, fontsize=14)
    plt.xticks(rotation=0, fontsize=14)
    plt.xlabel('\nCohort Period', fontsize=16)
    plt.ylabel('(Cohort, Cohort Size)\n', fontsize=16)
    plt.title('Retention', fontsize=20)
    plt.show()

    return h
