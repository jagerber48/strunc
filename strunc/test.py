import sys
from dataclasses import dataclass
import logging

import numpy as np

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
        result_str = None
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
                       '': '123.5+/-0.8',
                       'd': '123.5+/-0.8',
                       'e': '(1.235+/-0.008)e+02',
                       'r': '(123.5+/-0.8)e+00',
                       'R': '(0.1235+/-0.0008)e+03',
                       'S': '123.5(8)',
                       'dS': '123.5(8)',
                       'eS': '1.235(8)e+02',
                       'rS': '123.5(8)e+00',
                       'RS': '0.1235(8)e+03',
                       '.3': '123.456+/-0.789',
                       '.3d': '123.456+/-0.789',
                       '.3e': '(1.23456+/-0.00789)e+02',
                       '.3r': '(123.456+/-0.789)e+00',
                       '.3R': '(0.123456+/-0.000789)e+03',
                       '+': '+123.5+/-0.8',
                       '+d': '+123.5+/-0.8',
                       '+e': '(+1.235+/-0.008)e+02',
                       '+r': '(+123.5+/-0.8)e+00',
                       '+R': '(+0.1235+/-0.0008)e+03',
                       ' ': ' 123.5+/-0.8',
                       ' d': ' 123.5+/-0.8',
                       ' e': '( 1.235+/-0.008)e+02',
                       ' r': '( 123.5+/-0.8)e+00',
                       ' R': '( 0.1235+/-0.0008)e+03',
                   })
    ,
    FormatTestCase(val=12.34,
                   unc=np.nan,
                   fmt_str_dict={'': '12.34+/-nan',
                                 'S': '12.34(nan)'}) # TODO Is the the expected/desired behavior?
    ,
    FormatTestCase(val=12.34,
                   unc=np.inf,
                   fmt_str_dict={'': '12.34+/-inf',
                                 'S': '12.34(inf)'})
    ,
    FormatTestCase(val=np.nan,
                   unc=12.34,
                   fmt_str_dict={'': 'nan+/-12',
                                 'S': 'nan+/-12'})
    # TODO Is the the expected/desired behavior?
    ,
    FormatTestCase(val=np.inf,
                   unc=12.34,
                   fmt_str_dict={'': 'inf+/-12',
                                 'S': 'inf+/-12'})
    ,
    FormatTestCase(val=np.nan,
                   unc=np.nan,
                   fmt_str_dict={'': 'nan+/-nan',
                                 'S': 'nan+/-nan'})
)


def main():
    for logger_name, loglevel in {'strunc': logging.ERROR,
                                  '__main__': logging.WARNING}.items():
        other_logger = logging.getLogger(logger_name)
        handler = logging.StreamHandler(stream=sys.stderr)
        formatter = logging.Formatter(
            fmt=f'%(levelname)s | %(funcName)s | %(lineno)s | %(message)s')
        handler.setFormatter(formatter)
        other_logger.addHandler(handler)
        other_logger.setLevel(loglevel)

    for test_case in test_cases:
        validate_test_case(test_case)


if __name__ == "__main__":
    main()
