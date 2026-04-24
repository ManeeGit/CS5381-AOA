# Matrix multiply optimised template — loop order ijk → ikj (cache-friendly)
# ikj order: inner loop accesses b[i][j] sequentially → better cache locality.


def matmul3(a, b):
    # a and b are 3x3 lists — ikj loop order (cache-friendly)
    n = 3
    res = [[0] * n for _ in range(n)]
    for i in range(n):
        for k in range(n):
            aik = a[i][k]
            for j in range(n):
                res[i][j] += aik * b[k][j]
    return res
