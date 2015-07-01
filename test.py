from balanced_partition import balanced_partition
from nose_xml_reader import read_nose_xml

with open('/tmp/nosetests.xml') as f:
    test_result = read_nose_xml(f.read())

p1, p2 = balanced_partition([
    (testcase['classname'] + '.' + testcase['name'], testcase['time'])
    for testcase in test_result if testcase['status'] == 'ok'
])
p3, p4 = balanced_partition(p1[0])
p5, p6 = balanced_partition(p2[0])
print len(p1[0]), p1[1]
print len(p2[0]), p2[1]
print len(p3[0]), p3[1]
print len(p4[0]), p4[1]
print len(p5[0]), p5[1]
print len(p6[0]), p6[1]
