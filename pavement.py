import os
from paver.easy import *
from os import listdir

from nose_xml_reader import read_nose_xml
from dsl_file_generator import generate_dsl_file
from balanced_partition import balanced_partition
from utils.db_utils import get_data_from_db, bulk_write_data_to_db, get_db_dict_connection
from utils.chart_utils import generate_top_slow_trend, generate_scatter
from settings import TEST_CASE_ROOT, DEFAULT_TEST_CASE_DURATION, PARTITION_DEPTH, NOSE_CFG_FILE, TOP_SLOW_COUNT, \
    TREND_CHART, SCATTER_CHART


@task
def controller_main():
    current_test_case_list = collect_all_test_cases(TEST_CASE_ROOT)
    current_test_case_duration_dict = get_test_cases_mapping_from_db()
    new_test_cases = set(current_test_case_list).difference(set(current_test_case_duration_dict.keys()))
    new_test_cases_dict = insert_new_test_cases(new_test_cases)
    current_test_case_duration_dict.update(new_test_cases_dict)
    current_test_case_dict = {
        test_case: current_test_case_duration_dict[test_case]
        for test_case in current_test_case_list
    }
    partitions = [test_case_duration_dict_to_partition(current_test_case_dict)]
    for i in xrange(PARTITION_DEPTH):
        _partitions = []
        while partitions:
            partition = partitions.pop()
            sub_partitions = balanced_partition(partition)
            _partitions.extend(sub_partitions)
        partitions = _partitions
    id_partitions = convert_test_case_to_ids(partitions, current_test_case_duration_dict)
    partition_ids = write_partitions_to_db(id_partitions)
    generate_dsl_file(partition_ids)


@task
@cmdopts([
    ('partition_id=', 'p', 'specific partition for nosetests.'),
])
def runner_main(options):
    if not hasattr(options, 'partition_id'):
        raise RuntimeError("partition_id are not specified")
    partition_id = int(options.partition_id)
    cases = generate_test_case_list_file(partition_id)
    run_test_cases(get_nose_cfg_file_name(partition_id))
    with open(get_xunit_file_name(partition_id), 'r') as xml_file:
        xml_text = xml_file.read()
        test_case_result_dict = read_nose_xml(xml_text)
    write_test_cases_result(cases, test_case_result_dict)


@task
def analyser_main():
    xml_files = [f for f in listdir('./') if f.endswith('.xml')]
    test_set_list = {}
    test_list = []
    for xml_file in xml_files:
        with open(xml_file, 'r') as xml_file:
            xml_text = xml_file.read()
            test_case_result_dict_list = read_nose_xml(xml_text)
            test_set_list[xml_file.name] = test_case_result_dict_list
            test_list.extend(test_case_result_dict_list)
    summary_dict = {}
    for file_name, test_set in test_set_list.iteritems():
        summary_time = sum([test['time'] for test in test_set])
        build_id = get_long_from_str(file_name)
        summary_dict[build_id] = {'time': summary_time, 'count': len(test_set)}

    summary_id_list = sorted(summary_dict.keys())
    print "Execution Summary:"
    for summary_id in summary_id_list:
        print "\tBUILD ID: {:<10d} Duration: {:<10g}    Case #: {}".format(
            summary_id, summary_dict[summary_id]['time'], summary_dict[summary_id]['count'])

    sorted_test_list = sorted(test_list, lambda x, y: cmp(x['time'], y['time']), reverse=True)
    top_slow_test_list = [sorted_test_list[idx] for idx in range(TOP_SLOW_COUNT)]
    top_slow_case_ids = [get_case_id(case_info['classname'], case_info['name']) for case_info in top_slow_test_list]
    print "Top Slow Tests"
    for test_case_info in top_slow_test_list:
        test_name = '.'.join([test_case_info['classname'], test_case_info['name']])
        print "\tTest: {:<60s} Duration: {}".format(test_name, test_case_info['time'])
    generate_top_slow_trend(top_slow_case_ids)
    print 'file:///{}/{}'.format(get_base_dir(), TREND_CHART)
    generate_scatter(sorted_test_list)
    print 'file:///{}/{}'.format(get_base_dir(), SCATTER_CHART)



def run_test_cases(nose_config_file):
    base_command = "nosetests -sv -c {}".format(nose_config_file)
    sh(base_command, cwd=get_base_dir())


def generate_test_case_list_file(partition_id):
    sql_script = "SELECT case_ids FROM aa_test_partitions WHERE id = %s"
    case_ids = get_data_from_db(sql_script, [partition_id])
    case_id_str = [str(case_id) for case_id in case_ids[0]['case_ids']]
    sql_script = "SELECT id, classname, name FROM aa_test_cases WHERE id in %s"
    cases = get_data_from_db(sql_script, (tuple(case_id_str),))

    with open(get_nose_cfg_file_name(partition_id), 'w') as file:
        template = "[nosetests]\nwith-xunit=1\nxunit-file={}\n".format(get_xunit_file_name(partition_id))
        file.write(template)
        noodles = []
        for item in cases:
            class_name = ':'.join(item.get('classname').rsplit('.', 1))
            case_name = item.get('name')
            noodle = '{class_name}.{case_name}'.format(
                class_name=class_name, case_name=case_name
            )
            noodles.append(noodle)
        noodles = "tests=" + ','.join(noodles)
        file.write(noodles)
    return cases


def write_test_cases_result(cases, test_case_results):
    sql_script = "INSERT INTO aa_test_stats (case_id, duration) VALUES (%(case_id)s, %(duration)s)"
    case_map = {}
    for case in cases:
        class_name = case.get('classname')
        case_name = case.get('name')
        id = case.get('id')
        case_map[(class_name, case_name)] = id

    result_map = {}
    for result in test_case_results:
        class_name = result.get('classname')
        case_name = result.get('name')
        duration = result.get('time')
        status = result.get('status')
        if status.lower() == "ok":
            result_map[(class_name, case_name)] = duration
    results = []
    for k, v in result_map.iteritems():
        if k in case_map:
            results.append({'case_id': case_map[k], 'duration': v})
    bulk_write_data_to_db(sql_script, results)


def collect_all_test_cases(test_case_root):
    output = sh('nosetests -sv --collect-only cases 2>&1', cwd=test_case_root, capture=True)
    test_cases = []
    for line in output.split('\n'):
        try:
            test_name, test_classname, _, status = line.split()
        except ValueError:
            continue
        test_classname = test_classname.strip('()')
        test_cases.append(test_classname + '.' + test_name)
    return test_cases


def get_test_cases_mapping_from_db():
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute(
        'select c.id, c.classname, c.name, s1.duration from aa_test_cases c '
        'left join aa_test_stats s1 on c.id = s1.case_id '
        'left join (select max(id) as mid from aa_test_stats group by case_id) s2 on s1.id = s2.mid'
    )
    return {
        row['classname'] + '.' + row['name']: (row['id'], row['duration'] or DEFAULT_TEST_CASE_DURATION)
        for row in cursor
    }


def get_case_id(class_name, test_name):
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    cursor.execute(
        'select id from aa_test_cases where classname=%s and name=%s',
        (class_name, test_name)
    )
    return cursor.fetchone()['id']


def insert_new_test_cases(new_test_cases):
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    new_test_case_dict = {}
    for test_case in new_test_cases:
        test_classname, test_name = test_case.rsplit('.', 1)
        try:
            cursor.execute(
                'insert into aa_test_cases (classname, name) values (%s, %s) returning id',
                (test_classname, test_name)
            )
            test_case_id = cursor.fetchone()['id']
            conn.commit()
        except:
            conn.rollback()
            cursor.execute(
                'select id from aa_test_cases where classname=%s and name=%s',
                (test_classname, test_name)
            )
            test_case_id = cursor.fetchone()['id']
        new_test_case_dict[test_case] = (test_case_id, DEFAULT_TEST_CASE_DURATION)
    return new_test_case_dict


def compose_test_case_duration_dict(current_test_case_list, historical_test_case_duration_dict):
    for test_case in current_test_case_list:
        if test_case not in historical_test_case_duration_dict:
            historical_test_case_duration_dict[test_case] = DEFAULT_TEST_CASE_DURATION
    return historical_test_case_duration_dict


def test_case_duration_dict_to_partition(test_case_dict):
    return [
        (test_case, test_case_duration)
        for test_case, (test_case_id, test_case_duration) in test_case_dict.iteritems()
    ]


def convert_test_case_to_ids(partitions, current_test_case_duration_dict):
    for i in xrange(len(partitions)):
        partitions[i] = [
            current_test_case_duration_dict[test_case[0]][0]
            for test_case in partitions[i]
        ]
    return partitions


def write_partitions_to_db(partitions):
    conn = get_db_dict_connection()
    cursor = conn.cursor()
    try:
        partition_ids = []
        for partition in partitions:
            cursor.execute(
                'insert into aa_test_partitions (case_ids) values (%s) returning id',
                (partition, )
            )
            partition_id = cursor.fetchone()['id']
            partition_ids.append(partition_id)
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return partition_ids


def get_base_dir():
    return os.path.dirname(os.path.realpath(__file__))


def get_xunit_file_name(partition_id):
    return 'xunit-{}.xml'.format(partition_id)


def get_nose_cfg_file_name(partition_id):
    return NOSE_CFG_FILE.format(partition_id)


def get_distribution_count():
    return pow(2, PARTITION_DEPTH)


def get_long_from_str(str_num):
    if isinstance(str_num, (int, long)):
        return long(str_num)
    s = filter(lambda ch: ch in '0123456789', str_num)
    return long(s) if s else 0L
