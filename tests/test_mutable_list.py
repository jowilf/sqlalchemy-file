from sqlalchemy_file.mutable_list import MutableList


def test_init_value() -> None:
    arr: MutableList[int] = MutableList()
    assert arr == []
    arr = MutableList([1, 2, 3])
    assert arr == [1, 2, 3]


def test_keep_traced_when_pop() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3])
    removed_item = arr.pop(1)
    assert removed_item == 2
    assert len(arr) == 2
    assert arr._removed == [2]
    arr.extend([4, 5, 6])
    assert arr == [1, 3, 4, 5, 6]
    arr.pop(3)
    assert arr._removed == [2, 5]


def test_keep_traced_when_replace() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3, 4, 5])
    arr[1] = 9
    arr[2] = 7
    assert arr == [1, 9, 7, 4, 5]
    assert arr._removed == [2, 3]


def test_keep_traced_when_slice_replace() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3, 4, 5, 6, 7])
    arr[2:4] = [1]
    assert arr == [1, 2, 1, 5, 6, 7]
    assert arr._removed == [3, 4]


def test_keep_traced_when_remove() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3, 5, 6, 7])
    arr.remove(2)
    arr.remove(6)
    assert arr == [1, 3, 5, 7]
    assert arr._removed == [2, 6]


def test_keep_traced_when_del() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3, 5, 6, 7])
    del arr[2]
    del arr[4]
    assert arr == [1, 2, 5, 6]
    assert arr._removed == [3, 7]


def test_keep_traced_when_del_slice() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3, 5, 6, 7])
    del arr[2:4]
    assert arr == [1, 2, 6, 7]
    assert arr._removed == [3, 5]


def test_keep_traced_when_clear() -> None:
    arr: MutableList[int] = MutableList([1, 2, 3])
    arr.clear()
    assert arr == []
    assert arr._removed == [1, 2, 3]


def test_other() -> None:
    arr: MutableList[int] = MutableList([1, 2])
    arr.insert(0, 5)
    assert arr == [5, 1, 2]
    arr.sort()
    assert arr == [1, 2, 5]
    arr.reverse()
    assert arr == [5, 2, 1]
