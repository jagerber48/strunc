import sys
from math import log10, floor
import re
from dataclasses import dataclass
from enum import Enum
import logging

import numpy as np


logger = logging.getLogger(__name__)

AUTO_SIG_FIGS = object()


@dataclass
class MathSymbs:
    pm: str
    l_paren: str
    r_paren: str
    times: str


latex_symbs = MathSymbs(pm=r'\pm',
                        l_paren=r'\left(',
                        r_paren=r'\right)',
                        times=r'\times')

pretty_print_symbs = MathSymbs(pm=u'±',
                               l_paren='(',
                               r_paren=')',
                               times=u'×')
standard_symbs = MathSymbs(pm='+/-',
                           l_paren='(',
                           r_paren=')',
                           times='e')


TO_SUPERSCRIPT = {
    0x2b: u'⁺',
    0x2d: u'⁻',
    0x30: u'⁰',
    0x31: u'¹',
    0x32: u'²',
    0x33: u'³',
    0x34: u'⁴',
    0x35: u'⁵',
    0x36: u'⁶',
    0x37: u'⁷',
    0x38: u'⁸',
    0x39: u'⁹'
    }


class DisplayMode(Enum):
    STANDARD = 'standard'
    PRETTY_PRINT = 'pretty_print'
    LATEX = 'latex'


class FormatType(Enum):
    DECIMAL = 'decimal'
    SCIENTIFIC = 'scientific'
    ENGINEERING = 'engineering'
    ENGINEERING_UPPER = 'engineering_upper'

    @classmethod
    def from_format_type_str(cls, format_type_str):
        str_to_enum_dict = {'d': cls.DECIMAL,
                            'e': cls.SCIENTIFIC,
                            'r': cls.ENGINEERING,
                            'R': cls.ENGINEERING_UPPER}
        return str_to_enum_dict[format_type_str]


@dataclass
class FormatSpecData:
    top_digit: int = 0
    sign_symbol_rule: str = '-'
    grouping_char: str = ''
    num_sig_figs: int = AUTO_SIG_FIGS
    val_sets_sig_figs: bool = False
    unc_sets_exp: bool = False
    format_type: FormatType = FormatType.DECIMAL
    short_form: bool = False
    display_mode: DisplayMode = DisplayMode.STANDARD


def get_top_and_bottom_digit(num: float) -> tuple[int, int]:
    if num == np.nan or num == np.inf or num == -np.inf:
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


pattern = re.compile(r'''
                         ^
                         (?P<top_digit>\d+)?
                         (?P<sign_symbol_rule>[-+ ])?  
                         (?P<grouping_char>[,_])?
                         (?:\.(?P<num_sig_figs>\d+))?
                         (?P<val_sets_sig_figs>v)?
                         (?P<unc_sets_exp>u)?
                         (?P<format_type>[derR])?
                         (?P<format_options>S?[P|L]?)?
                         $
                      ''', re.VERBOSE)


def parse_format_spec(format_spec: str) -> FormatSpecData:
    match = pattern.match(format_spec)

    top_digit = match.group('top_digit')
    if top_digit is not None:
        top_digit = int(top_digit)
    else:
        top_digit = 0
    sign_symbol_rule = match.group('sign_symbol_rule') or '-'
    grouping_char = match.group('grouping_char') or ''
    num_sig_figs = match.group('num_sig_figs')
    if num_sig_figs is not None:
        num_sig_figs = int(num_sig_figs)
    else:
        num_sig_figs = AUTO_SIG_FIGS
    val_sets_sig_figs = match.group('val_sets_sig_figs') == 'v'
    unc_sets_exp = match.group('unc_sets_exp') == 'u'
    format_type_str = match.group('format_type') or 'd'
    format_options = match.group('format_options') or ''

    format_type = FormatType.from_format_type_str(format_type_str)

    short_form = 'S' in format_options

    if 'P' in format_options:
        display_mode = DisplayMode.PRETTY_PRINT
    elif 'L' in format_options:
        display_mode = DisplayMode.LATEX
    else:
        display_mode = DisplayMode.STANDARD

    format_spec_data = FormatSpecData(top_digit=top_digit,
                                      sign_symbol_rule=sign_symbol_rule,
                                      grouping_char=grouping_char,
                                      num_sig_figs=num_sig_figs,
                                      val_sets_sig_figs=val_sets_sig_figs,
                                      unc_sets_exp=unc_sets_exp,
                                      format_type=format_type,
                                      short_form=short_form,
                                      display_mode=display_mode)

    return format_spec_data


class DriverType(Enum):
    NONE = 'none'
    VALUE = 'value'
    UNCERTAINTY = 'uncertainty'


def get_sig_fig_driver(val: float, unc: float,
                       val_sets_sig_figs: bool = False) -> DriverType:
    val_warned = False
    if val_sets_sig_figs:
        if np.isfinite(val):
            return DriverType.VALUE
        else:
            logger.warning('Cannot use infinite value to set the number of '
                           'significant figures for value/uncertainty string '
                           'formatting.')
            val_warned = True

    if np.isfinite(unc) and unc != 0:
        return DriverType.UNCERTAINTY
    else:
        logger.warning('Cannot use infinite or zero uncertainty to set the '
                       'number of significant figures for value/uncertainty '
                       'string formatting')
        if np.isfinite(val):
            return DriverType.VALUE
        elif not val_warned:
            logger.warning('Cannot use infinite value to set the number of '
                           'significant figures for value/uncertainty string '
                           'formatting.')
    return DriverType.NONE


def get_pdg_num_sig_figs_and_rounded_unc(unc: float) -> (int, float):
    top_digit, _ = get_top_and_bottom_digit(unc)
    unc_rounded_1 = round(unc, -top_digit + 2)
    top_digit, _ = get_top_and_bottom_digit(unc_rounded_1)
    top_three_dig = round(unc_rounded_1*10**(-top_digit + 2), 0)
    if 100 <= top_three_dig <= 354:
        num_sig_figs = 2
        updated_unc = round(unc, -top_digit + 1)
    elif 355 <= top_three_dig <= 949:
        num_sig_figs = 1
        updated_unc = round(unc, -top_digit)
    elif 950 <= top_three_dig <= 999:
        num_sig_figs = 2
        updated_unc = 1000 * 10**(top_digit - 2)
    else:
        logger.debug(f'Top three digits calculated as {top_three_dig}')
        raise ValueError(f'Unable to parse number of sig figs from {unc}.')

    return num_sig_figs, updated_unc


def round_val_unc_to_sig_figs(val: float, unc: float,
                              sig_fig_driver: DriverType,
                              num_sig_figs: int) -> (float, float, int):
    logger.debug(f'{num_sig_figs=}')
    if sig_fig_driver == DriverType.UNCERTAINTY:
        if num_sig_figs == AUTO_SIG_FIGS:
            num_sig_figs, unc = get_pdg_num_sig_figs_and_rounded_unc(unc)
        top_digit, _ = get_top_and_bottom_digit(unc)
        bottom_digit = top_digit - num_sig_figs + 1
    elif sig_fig_driver == DriverType.VALUE:
        if num_sig_figs == AUTO_SIG_FIGS:
            if val != 0:
                _, bottom_digit = get_top_and_bottom_digit(val)
            else:
                bottom_digit = 0
        else:
            top_digit, _ = get_top_and_bottom_digit(val)
            logger.debug(f'{top_digit=}')
            bottom_digit = top_digit - num_sig_figs + 1
    else:
        bottom_digit = 0

    logger.debug(f'{bottom_digit=}')
    val_rounded = round(val, -bottom_digit)
    unc_rounded = round(unc, -bottom_digit)

    return val_rounded, unc_rounded, bottom_digit


def get_exp_driver(val: float, unc: float,
                   unc_sets_exp: bool = False) -> DriverType:
    unc_warned = False
    if unc_sets_exp:
        if np.isfinite(unc):
            return DriverType.UNCERTAINTY
        else:
            logger.warning('Cannot use infinite uncertainty to set the '
                           'exponent for value/uncertainty string formatting.')
            unc_warned = True

    if np.isfinite(val):
        return DriverType.VALUE
    else:
        logger.warning('Cannot use infinite value to set the exponent for '
                       'value/uncertainty string formatting.')
        if np.isfinite(unc):
            return DriverType.UNCERTAINTY
        elif not unc_warned:
            logger.warning('Cannot use infinite uncertainty to set the '
                           'exponent for value/uncertainty string formatting.')
    return DriverType.NONE


def get_exp(val: float, unc: float, exp_driver: DriverType,
            format_type: FormatType) -> int:
    if format_type is FormatType.DECIMAL:
        return 0

    if exp_driver is DriverType.VALUE:
        top_digit, _ = get_top_and_bottom_digit(val)
    elif exp_driver is DriverType.VALUE:
        top_digit, _ = get_top_and_bottom_digit(unc)
    else:
        return 0

    if format_type is FormatType.SCIENTIFIC:
        return top_digit
    elif format_type is FormatType.ENGINEERING:
        return (top_digit // 3) * 3
    elif format_type is FormatType.ENGINEERING_UPPER:
        return ((top_digit + 1) // 3) * 3

    return 0


def float_mantissa_to_str(mantissa, exp, bottom_digit, top_digit_target,
                          sign_symbol_rule, grouping_char):
    logger.debug('float_mantissa_to_str()')
    logger.debug(f'{mantissa=}')
    logger.debug(f'{top_digit_target=}')
    prec = max(-(bottom_digit - exp), 0)
    format_str = f'{grouping_char}.{prec}f'
    abs_mantissa_str = f'{abs(mantissa):{format_str}}'

    top_digit, _ = get_top_and_bottom_digit(mantissa*10**exp)
    top_digit = max(top_digit, 0)
    logger.debug(f'{top_digit=}')
    if top_digit_target > top_digit:
        zero_pad_str = '0'*(top_digit_target - top_digit)
        abs_mantissa_str = f'{zero_pad_str}{abs_mantissa_str}'

    if mantissa < 0:
        sign_str = '-'
    elif sign_symbol_rule == '+':
        sign_str = '+'
    elif sign_symbol_rule == ' ':
        sign_str = ' '
    else:
        sign_str = ''

    mantissa_str = f'{sign_str}{abs_mantissa_str}'

    return mantissa_str


def get_symbs(display_mode: DisplayMode) -> MathSymbs:
    if display_mode is DisplayMode.STANDARD:
        return standard_symbs
    elif display_mode is DisplayMode.LATEX:
        return latex_symbs
    elif display_mode is DisplayMode.PRETTY_PRINT:
        return pretty_print_symbs


def get_val_unc_exp_str(val_str: str, unc_str: str, exp: int,
                        short_form: bool,
                        format_type: FormatType,
                        display_mode: DisplayMode):
    if short_form:
        if unc_str != '0':
            unc_str = unc_str.lstrip('0')
            unc_str = unc_str.lstrip('.')
            unc_str = unc_str.lstrip('0')
        unc_str = f'({unc_str})'
        val_unc_str = f'{val_str}{unc_str}'
    else:
        symbs = get_symbs(display_mode)
        val_unc_str = f'{val_str}{symbs.pm}{unc_str}'
    if format_type is FormatType.DECIMAL:
        return val_unc_str
    else:
        symbs = get_symbs(display_mode)
        if display_mode is DisplayMode.PRETTY_PRINT:
            exp_str = f'{symbs.times}10{str(exp).translate(TO_SUPERSCRIPT)}'
        elif display_mode is DisplayMode.LATEX:
            exp_str = f'{symbs.times}10^{{{exp}}}'
        else:
            exp_str = f'{symbs.times}{exp:+03d}'
        if not short_form:
            val_unc_exp_str = (f'{symbs.l_paren}{val_unc_str}{symbs.r_paren}' 
                               f'{exp_str}')
        else:
            val_unc_exp_str = f'{val_unc_str}{exp_str}'

    return val_unc_exp_str


def format_val_unc(val: float, unc: float,
                   format_spec_data: FormatSpecData) -> str:
    logger.debug(f'{val=}')
    logger.debug(f'{unc=}')
    logger.debug(f'{format_spec_data=}')
    if np.isnan(val) or not np.isfinite(val) and format_spec_data.short_form:
        logger.warning(f'short form not valid for nan of inf vals. Disabling '
                       f'short form.')
        format_spec_data.short_form = False


    if unc < 0:
        logger.warning(f'Negative uncertainty {unc}, coercing to positive.')
        unc = abs(unc)

    sig_fig_driver = get_sig_fig_driver(
        val, unc,
        val_sets_sig_figs=format_spec_data.val_sets_sig_figs)

    val_rounded, unc_rounded, bottom_digit = round_val_unc_to_sig_figs(
        val, unc,
        sig_fig_driver=sig_fig_driver,
        num_sig_figs=format_spec_data.num_sig_figs)

    exp_driver = get_exp_driver(val, unc,
                                unc_sets_exp=format_spec_data.unc_sets_exp)
    exp = get_exp(val_rounded, unc_rounded, exp_driver=exp_driver,
                  format_type=format_spec_data.format_type)
    logger.debug(f'{exp=}')
    val_mantissa = val_rounded * 10**-exp
    logger.debug(f'{val_mantissa=}')
    unc_mantissa = unc_rounded * 10**-exp
    logger.debug(f'{unc_mantissa=}')

    val_top_digit, _ = get_top_and_bottom_digit(val_mantissa)
    unc_top_digit, _ = get_top_and_bottom_digit(unc_mantissa)
    top_digit_target = max(val_top_digit, unc_top_digit,
                           format_spec_data.top_digit)

    if val == np.nan:
        val_mantissa_str = 'nan'
    elif val == np.inf:
        val_mantissa_str = 'inf'
    elif val == -np.inf:
        val_mantissa_str = '-inf'
    else:
        val_mantissa_str = float_mantissa_to_str(val_mantissa, exp, bottom_digit,
                                                 top_digit_target,
                                                 format_spec_data.sign_symbol_rule,
                                                 format_spec_data.grouping_char)
    logger.debug(f'{val_mantissa_str=}')

    if unc_mantissa == np.nan:
        unc_mantissa_str = 'nan'
    elif unc_mantissa == np.inf:
        unc_mantissa_str = 'inf'
    else:
        unc_mantissa_str = float_mantissa_to_str(unc_mantissa, exp, bottom_digit,
                                                 top_digit_target,
                                                 '-',
                                                 format_spec_data.grouping_char)
    logger.debug(f'{unc_mantissa_str=}')

    val_unc_exp_str = get_val_unc_exp_str(val_mantissa_str,
                                          unc_mantissa_str,
                                          exp,
                                          format_spec_data.short_form,
                                          format_spec_data.format_type,
                                          format_spec_data.display_mode)

    return val_unc_exp_str


def format(val: float, unc: float, format_spec: str = ''):
    format_spec_data = parse_format_spec(format_spec)
    val_unc_exp_str = format_val_unc(val, unc, format_spec_data)
    return val_unc_exp_str


def main():
    val = 12349234
    unc = 2352
    fmt_spec = 'rS'
    val_unc_str = format(val, unc, fmt_spec)
    print(val_unc_str)


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s | %(funcName)s | %(lineno)s | %(message)s',
                        stream=sys.stdout)
    logger.setLevel(logging.WARNING)

    main()
