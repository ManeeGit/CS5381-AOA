# Pseudocode / Algorithm Description – Base Template
# Task: implement a sorting algorithm.
# The function must be named 'sort' and accept a list, returning a sorted list.

def sort(arr):
    # Bubble sort baseline – correct but not optimal
    n = len(arr)
    result = arr[:]
    for i in range(n):
        for j in range(0, n - i - 1):
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
    return result
