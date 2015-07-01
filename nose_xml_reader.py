from lxml import etree


def read_nose_xml(xml_text):
    root = etree.fromstring(xml_text)
    testcases = []
    for testcase in root:
        status = 'ok'
        if len(testcase):
            tag = testcase[0].tag
            if not tag.startswith('system'):
                status = tag
        testcases.append({
            'classname': testcase.get('classname'),
            'name': testcase.get('name'),
            'time': float(testcase.get('time')),
            'status': status,
        })
    return testcases

if __name__ == '__main__':
    from os import listdir
    xml_files = [f for f in listdir('./') if f.endswith('.xml')]
    test_set_list = {}
    for xml_file in xml_files:
        with open(xml_file, 'r') as xml_file:
            xml_text = xml_file.read()
            test_case_result_dict = read_nose_xml(xml_text)
            test_set_list[xml_file.name] = test_case_result_dict
    summary_dict = {}
    for file_name, test_set in test_set_list.iteritems():
        summary_time = sum([test['time'] for test in test_set])
        build_id = get_long_from_str(file_name)
        summary_dict[build_id] = {'time': summary_time, 'count': len(test_set)}

    summary_id_list = sorted(summary_dict.keys())
    for summary_id in summary_id_list:
        print "BUILD ID: {}, Time: {}, Case #: {}".format(
            summary_id, summary_dict[summary_id]['time'], summary_dict[summary_id]['count'])
