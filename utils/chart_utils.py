import random
from pandas import DataFrame, Series
import matplotlib.pyplot as plt
from settings import TREND_CHART, SCATTER_CHART
from utils.db_utils import get_db_connection


def get_random_color():
    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
    return random.choice(colors)


def generate_top_slow_trend(case_ids):

    sql_script = """SELECT start_time, case_id, duration
                    FROM aa_test_stats
                    WHERE case_id in %s"""

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql_script, (tuple(case_ids),))

    df = DataFrame(cursor.fetchall(), columns=['start_time', 'case_id','duration'])

    fig, ax = plt.subplots()
    labels = []
    for key, grp in df.groupby(['case_id']):
        color = get_random_color()
        ax = grp.plot(ax=ax, kind='line', x='start_time', y='duration', c=color)
        labels.append(key)
    lines, _ = ax.get_legend_handles_labels()
    ax.legend(lines, labels, loc=2, prop={'size': 5})
    plt.savefig(TREND_CHART)


def generate_scatter(test_list):
    test_list = test_list.sort(key=lambda x: x['classname'])
    df = DataFrame(test_list, columns=['classname', 'name', 'time'])
    df['id'] = Series(range(10000))
    fig, ax = plt.subplots()
    for key, grp in df.groupby('classname'):
        color = get_random_color()
        ax = grp.plot(ax=ax, kind='scatter', x='id', y='time', c=color)
    lines, _ = ax.get_legend_handles_labels()
    plt.savefig(SCATTER_CHART)


if __name__ == '__main__':
    generate_top_slow_trend([506, 507])
