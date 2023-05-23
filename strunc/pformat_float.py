import sys
from typing import Optional
from dataclasses import dataclass
from enum import Enum
import re
from math import log10, log2, floor, isfinite
import logging


logger = logging.getLogger(__name__)


def get_top_digit(num: float) -> int:
    num = abs(num)
    int_part = int(num)
    if int_part == 0:
        magnitude = 1
    else:
        magnitude = int(log10(int_part)) + 1
    max_digits = sys.float_info.dig
    if magnitude >= max_digits:
        return magnitude

    try:
        top_digit = floor(log10(num))
    except ValueError:
        top_digit = 0
    return top_digit


def get_bottom_digit(num: float) -> int:
    num = abs(num)
    max_digits = sys.float_info.dig
    int_part = int(num)
    if int_part == 0:
        magnitude = 1
    else:
        magnitude = int(log10(int_part)) + 1

    if magnitude >= max_digits:
        return 0

    frac_part = num - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    precision = int(log10(frac_digits))

    bottom_digit = -precision

    return bottom_digit


def get_top_and_bottom_digit(num: float) -> tuple[int, int]:
    return get_top_digit(num), get_bottom_digit(num)


class FormatType(Enum):
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    ENGINEERING = 'engineering'
    ENGINEERING_SHIFTED = 'engineering_shifted'
    BINARY = 'binary'
    BINARY_IEC = 'binary_iec'

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
        elif flag == 'b':
            return FormatType.BINARY
        elif flag == 'B':
            return FormatType.BINARY_IEC
        else:
            raise ValueError(f'Invalid format type flag {flag}.')


def get_mantissa_exp(num: float, format_type: FormatType) -> (float, int):
    if num == 0:
        mantissa = 0
        exp = 0
    elif format_type is FormatType.DECIMAL:
        mantissa = num
        exp = 0
    elif (format_type is FormatType.SCIENTIFIC
            or format_type is FormatType.ENGINEERING
            or format_type is FormatType.ENGINEERING_SHIFTED):
        exp = floor(log10(abs(num)))
        if format_type is FormatType.ENGINEERING:
            exp = (exp // 3) * 3
        elif format_type is FormatType.ENGINEERING_SHIFTED:
            exp = ((exp + 1) // 3) * 3
        mantissa = num * 10 ** -exp
    elif (format_type is FormatType.BINARY
            or format_type is FormatType.BINARY_IEC):
        exp = floor(log2(abs(num)))
        if format_type is FormatType.BINARY_IEC:
            exp = (exp // 10) * 10
        mantissa = num * 2**-exp
    else:
        raise ValueError(f'Unhandled format type {format_type}')

    return mantissa, exp


def get_exp_str(exp: int, format_type: FormatType) -> str:
    if format_type is format_type.DECIMAL:
        exp_str = ''
    elif (format_type is FormatType.SCIENTIFIC
          or format_type is FormatType.ENGINEERING
          or format_type is FormatType.ENGINEERING_SHIFTED):
        exp_str = f'e{exp:+03d}'
    elif (format_type is FormatType.BINARY
          or format_type is FormatType.BINARY_IEC):
        exp_str = f'b{exp:+03d}'
    else:
        raise ValueError(f'Unhandled format type {format_type}')
    return exp_str


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


def format_float_by_top_bottom_dig(num: float,
                                   target_top_digit: int,
                                   target_bottom_digit: int,
                                   sign_mode: SignMode) -> str:
    num_rounded = round(num, -target_bottom_digit)

    print_prec = max(0, -target_bottom_digit)
    abs_mantissa_str = f'{abs(num_rounded):.{print_prec}f}'

    num_top_digit, _ = get_top_and_bottom_digit(num_rounded)
    pad_str = get_pad_str(num_top_digit, target_top_digit)

    sign_str = get_sign_str(num, sign_mode)

    float_str = f'{sign_str}{pad_str}{abs_mantissa_str}'
    return float_str


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
                         (?P<trailing_decimal>\#)?                         
                         (?P<top_pad_digit>\d+)?
                         (?P<grouping_option>[,_v])?                     
                         (?:(?P<prec_type>\.|\.\.)(?P<prec>\d+))?
                         (?P<format_type>[deEhHkK]|sh|SH)?
                         (?P<prefix_mode>p)?
                         $
                      ''', re.VERBOSE)


pattern = re.compile(r'''
                         ^
                         (?P<sign_mode>[-+ ])?  
                         (?P<top_pad_digit>\d+)?                         
                         (?:(?P<prec_type>[._])(?P<prec>\d+))?
                         (?P<format_type>[derRbB])?
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


def pformat_float(num: float, format_spec: FormatSpec) -> str:
    if not isfinite(num):
        return str(num)

    prec_type = format_spec.prec_type
    prec = format_spec.precision
    format_type = format_spec.format_type
    top_padded_digit = format_spec.top_padded_digit
    sign_mode = format_spec.sign_mode

    mantissa, exp = get_mantissa_exp(num, format_type)
    exp_str = get_exp_str(exp, format_type)

    top_digit, bottom_digit = get_top_and_bottom_digit(mantissa)

    round_digit = get_round_digit(top_digit, bottom_digit,
                                  prec, prec_type)

    mantissa_str = format_float_by_top_bottom_dig(mantissa, top_padded_digit,
                                                  round_digit, sign_mode)

    full_str = f'{mantissa_str}{exp_str}'
    return full_str


class pfloat(float):
    def __format__(self, format_spec):
        format_spec_data = parse_format_spec(format_spec)
        return pformat_float(self, format_spec_data)


def main():
    num = pfloat(15000)
    fmt = '.2B'
    print(f'{num=}')
    print(f'{fmt=}')
    num_fmted = f'{num:{fmt}}'
    print(num_fmted)
    # print(replace_prefix(num_fmted))


if __name__ == "__main__":
    main()
