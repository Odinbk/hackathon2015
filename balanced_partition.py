def balanced_partition(testcases):
    a_list = sorted(testcases, key=lambda (case_name, t): t)
    subset1, sum1 = [], 0
    subset2, sum2 = [], 0
    for case_name, t in reversed(a_list):
        if sum1 > sum2:
            subset2.append((case_name, t))
            sum2 += t
        else:
            subset1.append((case_name, t))
            sum1 += t
    return subset1, subset2
