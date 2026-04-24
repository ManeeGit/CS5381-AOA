# Compact sort with early-return guard
def sort(arr):
    # early exit + builtin
    if not arr:
        return []
    return sorted(arr)
