import sys
from dataclasses import dataclass
import logging

from strunc import format_val_unc_from_str


logger = logging.getLogger(__name__)


@dataclass
class FormatTestCase:
    val: float
    unc: float
    fmt_str_dict: dict[str, str]


def validate_test_case(test_case: FormatTestCase):
    val = test_case.val
    unc = test_case.unc
    for fmt_str, target_str in test_case.fmt_str_dict.items():
        try:
            result_str = format_val_unc_from_str(val, unc, fmt_str)
            assert result_str == target_str
        except (AssertionError, AttributeError):
            logger.warning(
                f'Test FAILED. \n\t{val=} \n\t{unc=} \n\t{fmt_str=} '
                f'\n\t{target_str=} \n\t{result_str=}')
        else:
            logger.info(f'Test PASSED: \n\t{val=} \n\t{unc=} \n\t{fmt_str=} '
                        f'\n\t{target_str=} \n\t{result_str=}')


test_cases = (
    FormatTestCase(val=123.456,
                   unc=0.789,
                   fmt_str_dict={
                       '': '123.5+/-000.8',
                       'd': '123.5+/-000.8',
                       'e': '(1.235+/-0.008)e+02',
                       'r': '(123.5+/-000.8)e+00',
                       'R': '(0.1235+/-0.0008)e+03',
                       'S': '123.5(8)',
                       'dS': '123.5(8)',
                       'eS': '1.235(8)e+02',
                       'rS': '123.5(8)e+00',
                       'RS': '0.1235(8)e+03',
                       '.3': '123.456+/-000.789',
                       '.3d': '123.456+/-000.789',
                       '.3e': '(1.23456+/-0.00789)e+02',
                       '.3r': '(123.456+/-000.789)e+00',
                       '.3R': '(0.123456+/-0.000789)e+03',
                       '+': '+123.5+/-000.8',
                       '+d': '+123.5+/-000.8',
                       '+e': '(+1.235+/-0.008)e+02',
                       '+r': '(+123.5+/-000.8)e+00',
                       '+R': '(+0.1235+/-0.0008)e+03',
                       ' ': ' 123.5+/-000.8',
                       ' d': ' 123.5+/-000.8',
                       ' e': '( 1.235+/-0.008)e+02',
                       ' r': '( 123.5+/-000.8)e+00',
                       ' R': '( 0.1235+/-0.0008)e+03',
                       'vdS': '123.456(789)',
                       'veS': '1.23456(789)e+02',
                       'vrS': '123.456(789)e+00',
                       'vRS': '0.123456(789)e+03',
                       '.3v': '123+/-001',
                       '.3vd': '123+/-001',
                       '.3ve': '(1.23+/-0.01)e+02',
                       '.3vr': '(123+/-001)e+00',
                       '.3vR': '(0.123+/-0.001)e+03',
                       'udS': '123.5(8)',
                       'ueS': '1.235(8)e+02',
                       'urS': '123.5(8)e+00',
                       'uRS': '0.1235(8)e+03',
                       '.3u': '123.456+/-000.789',
                       '.3ud': '123.456+/-000.789',
                       '.3ue': '(1234.56+/-0007.89)e-01',
                       '.3ur': '(123456+/-000789)e-03',
                       '.3uR': '(123.456+/-000.789)e+00',
                   })
    ,)


def main():
    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(
        fmt=f'%(levelname)s | %(funcName)s | %(lineno)s | %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)

    for test_case in test_cases:
        validate_test_case(test_case)


if __name__ == "__main__":
    main()
