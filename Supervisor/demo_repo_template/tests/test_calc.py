from buggy_calc.calc import average


def test_average_float():
    # Fails before the patch (// returns 2), passes after (/ returns 2.5)
    assert average([1, 2, 3, 4]) == 2.5
