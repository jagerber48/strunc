import sys
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import re
from math import log10, floor, isfinite
import logging


logger = logging.getLogger(__name__)


def get_top_and_bottom_digit(num: float) -> tuple[int, int]:
    if not isfinite(num):
        return 0, 0

    num = abs(num)
    max_digits = sys.float_info.dig
    int_part = int(num)
    if int_part == 0:
        magnitude = 1
    else:
        magnitude = int(log10(int_part)) + 1

    if magnitude >= max_digits:
        return magnitude, 0

    frac_part = num - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    precision = int(log10(frac_digits))

    bottom_digit = -precision
    if num != 0:
        top_digit = floor(log10(num))
    else:
        top_digit = 0

    logger.debug(f'{top_digit=}')
    logger.debug(f'{bottom_digit=}')
    return top_digit, bottom_digit


class FormatType(Enum):
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    ENGINEERING = 'engineering'
    ENGINEERING_SHIFTED = 'engineering_shifted'

    @staticmethod
    def from_flag(flag: str) -> 'FormatType':
        if flag == 'd':
            return FormatType.DECIMAL
        elif flag == 'e':
            return FormatType.SCIENTIFIC
        elif flag == 'r':
            return FormatType.ENGINEERING
        elif flag == 'R':
            return FormatType.ENGINEERING_SHIFTED
        else:
            raise ValueError(f'Invalid format type flag {flag}.')


def get_exp(top_digit: int, format_type: FormatType) -> int:
    if format_type is FormatType.SCIENTIFIC:
        return top_digit
    elif format_type is FormatType.ENGINEERING:
        return (top_digit // 3) * 3
    elif format_type is FormatType.ENGINEERING_SHIFTED:
        return ((top_digit + 1) // 3) * 3
    else:
        raise TypeError(f'Unhandled format type: {format_type}')


class SignMode(Enum):
    ALWAYS = 'always'
    NEGATIVE = 'negative'
    SPACE = 'space'

    @staticmethod
    def from_flag(flag: str):
        if flag == '-':
            return SignMode.NEGATIVE
        elif flag == '+':
            return SignMode.ALWAYS
        elif flag == ' ':
            return SignMode.SPACE
        else:
            raise ValueError(f'Invalid sign mode flag {flag}.')


def get_sign_str(num: float, sign_mode: SignMode) -> str:
    if num < 0:
        sign_str = '-'
    else:
        if sign_mode is SignMode.ALWAYS:
            sign_str = '+'
        elif sign_mode is SignMode.SPACE:
            sign_str = ' '
        elif sign_mode is SignMode.NEGATIVE:
            sign_str = ''
        else:
            raise ValueError(f'Invalid sign mode {sign_mode}.')
    return sign_str


class PrecType(Enum):
    SIG_FIG = 'sig_fig'
    PREC = 'prec'

    @staticmethod
    def from_flag(flag: str):
        if flag == '_':
            return PrecType.SIG_FIG
        elif flag == '.':
            return PrecType.PREC
        else:
            raise ValueError(f'Invalide precision type flag {flag}.')


def get_round_digit(top_digit: int, bottom_digit: int,
                    prec: int, prec_type: PrecType) -> int:
    if prec_type is PrecType.SIG_FIG:
        if prec is None:
            prec = top_digit - bottom_digit + 1
        round_digit = top_digit - (prec - 1)
    elif prec_type is PrecType.PREC:
        if prec is None:
            round_digit = bottom_digit
        else:
            round_digit = -prec
    else:
        raise TypeError(f'Unhandled precision type: {prec_type}.')
    return round_digit


def get_pad_str(top_digit: int, top_padded_digit: int) -> str:
    if top_padded_digit is not None:
        if top_padded_digit > top_digit:
            pad_len = top_padded_digit - max(top_digit, 0)
            pad_str = '0'*pad_len
        else:
            pad_str = ''
    else:
        pad_str = ''
    return pad_str


@dataclass
class FormatSpec:
    """
    Design decision:
    - explicitly specify format type
    - Only padding available is zeros between the sign and number
    - precision can be either a direction specification of what digit to
        display/round to (precision mode) or number of sig figs (sig fig mode)
    - exp always includes sign
    - exp is min width 3 (following python float formatting)
    # TODO: separation character (seperate every 3 digits with space?)
    """
    precision: Optional[int] = None
    prec_type: PrecType = PrecType.SIG_FIG
    format_type: FormatType = FormatType.DECIMAL
    top_padded_digit: Optional[int] = None
    sign_mode: SignMode = SignMode.NEGATIVE


pattern = re.compile(r'''
                         ^
                         (?P<sign_mode>[-+ ])?  
                         (?P<top_pad_digit>\d+)?                         
                         (?:(?P<prec_type>[._])(?P<prec>\d+))?
                         (?P<format_type>[derR])?
                         $
                      ''', re.VERBOSE)


def parse_format_spec(fmt: str) -> FormatSpec:
    match = pattern.match(fmt)

    sign_mode_flag = match.group('sign_mode') or '-'
    sign_mode = SignMode.from_flag(sign_mode_flag)

    top_pad_digit = match.group('top_pad_digit')
    if top_pad_digit:
        top_pad_digit = int(top_pad_digit)
    prec_type_flag = match.group('prec_type') or '_'
    prec_type = PrecType.from_flag(prec_type_flag)

    prec = match.group('prec')
    if prec:
        prec = int(prec)

    format_type_flag = match.group('format_type') or 'd'
    format_type = FormatType.from_flag(format_type_flag)

    format_spec = FormatSpec(prec, prec_type, format_type, top_pad_digit,
                             sign_mode)

    return format_spec


def pformat_float(num: float, fmt: str) -> str:
    if not isfinite(num):
        return str(num)

    format_spec = parse_format_spec(fmt)
    prec_type = format_spec.prec_type
    prec = format_spec.precision
    format_type = format_spec.format_type
    top_padded_digit = format_spec.top_padded_digit
    sign_mode = format_spec.sign_mode

    top_digit, bottom_digit = get_top_and_bottom_digit(num)

    '''
    Get exponent and mantissa. Rescale top and bottom digits to be relative to
    mantissa instead of num.
    '''
    if format_type is not FormatType.DECIMAL:
        exp = get_exp(top_digit, format_type)
        top_digit -= exp
        bottom_digit -= exp
        mantissa = num * 10**-exp
        exp_str = f'e{exp:+03d}'
    else:
        mantissa = num
        exp_str = ''

    round_digit = get_round_digit(top_digit, bottom_digit,
                                  prec, prec_type)
    mantissa_rounded = round(mantissa, -round_digit)

    print_prec = max(0, -round_digit)
    abs_mantissa_str = f'{abs(mantissa_rounded):.{print_prec}f}'

    sign_str = get_sign_str(num, sign_mode)
    pad_str = get_pad_str(top_digit, top_padded_digit)

    full_mantissa_str = f'{sign_str}{pad_str}{abs_mantissa_str}'

    full_str = f'{full_mantissa_str}{exp_str}'
    return full_str


class pfloat(float):
    def __format__(self, format_spec):
        return pformat_float(self, format_spec)


def main():
    num = pfloat(0)
    fmt = '+3.5R'
    print(f'{num=}')
    print(f'{fmt=}')
    print(f'{num:{fmt}}')


if __name__ == "__main__":
    main()
