def matmul3(a, b):
    # a and b are 3x3 lists
    res = [[0, 0, 0] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            s = 0
            for k in range(3):
                s += a[i][k] * b[k][j]
            res[i][j] = s
    return res
