import random


imp_template = """from time import sleep
from unittest2 import TestCase
"""


cls_template = """
class TestCase{num}(TestCase):
"""


func_template = """    def test_function_{num}(self):
        print '\\nsleep {run_time} second(s)'
        sleep({run_time})
"""


def get_random_num():
    idx = random.uniform(0, 1)
    if idx > 0.95:
        return round(random.uniform(5000, 200000) / 100000, 4)
    elif idx > 0.8:
        return round(random.uniform(500, 5000) / 100000, 4)
    else:
        return round(random.uniform(100, 500) / 100000, 4)


def get_better_random_num():
    expo_max = 5
    left, right = 0.001, 2
    random.seed()
    n = random.expovariate(1)
    if n > expo_max:
        n = expo_max * (1 + random.uniform(0, 1) / 5)
    return max((n / expo_max) * right, left)


def generate_test_case(file_num):
    for i in range(file_num):
        file_name = 'cases/test_case_file_{id}.py'.format(id=i)
        time_consume = 0
        with open(file_name, 'w') as file:
            print >> file, imp_template
            print >> file, cls_template.format(num=i)
            for j in range(100):
                run_time = get_better_random_num()
                time_consume += run_time
                print >> file, func_template.format(num=j, run_time=run_time)
        print '{}: {}'.format(file_name, time_consume)

if __name__ == '__main__':
    generate_test_case(100)
