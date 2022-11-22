import sys
from math import log10, floor, ceil
import numpy as np
import re


def get_top_and_bottom_digit(val):
    val = abs(val)
    max_digits = sys.float_info.dig
    int_part = int(val)
    if int_part == 0:
        magnitude = 1
    else:
        magnitude = int(log10(int_part)) + 1

    if magnitude >= max_digits:
        return magnitude, 0

    frac_part = val - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    precision = int(log10(frac_digits))

    bottom_digit = -precision
    if val != 0:
        top_digit = floor(log10(val))
    else:
        top_digit = 0

    return top_digit, bottom_digit


def float_to_numeral_str(val,
                         top_digit_target=None,
                         bottom_digit_target=None,
                         grouping_option='',
                         force_decimal_point=False):
    if np.isfinite(val):
        val_top_digit, val_bottom_digit = get_top_and_bottom_digit(val)
        if bottom_digit_target is None:
            bottom_digit_target = -val_bottom_digit
        if bottom_digit_target < 0:
            prec = -bottom_digit_target
        else:
            prec = 0

        base_format = f'{grouping_option}.{prec}f'
        float_str_base = format(np.abs(val), base_format)

        if force_decimal_point:
            if '.' not in float_str_base:
                float_str_base += '.'

        if top_digit_target > val_top_digit and top_digit_target > 0:
            if val_top_digit > 0:
                num_top_digit_pad = top_digit_target - val_top_digit
            else:
                num_top_digit_pad = top_digit_target
            float_str_padded = '0'*num_top_digit_pad + float_str_base
        else:
            float_str_padded = float_str_base
    else:
        float_str_padded = str(val)

    return float_str_padded


def get_sign_symbol(float_sign=+1, sign_symbol_rule='-'):
    if float_sign < 0:
        sign_symbol = '-'
    else:
        if sign_symbol_rule == '-':
            sign_symbol = ''
        elif sign_symbol_rule == '+':
            sign_symbol = '+'
        elif sign_symbol_rule == ' ':
            sign_symbol = ' '
        else:
            raise ValueError
    return sign_symbol


def float_str_to_filled_str(float_str,
                            float_sign=+1,
                            fill='',
                            align='>',
                            sign_symbol_rule='-',
                            sign_aware_fill=False,
                            min_width=0):
    if align == '' and sign_aware_fill is True:
        align = '='
        fill = '0'

    sign_symbol = get_sign_symbol(float_sign, sign_symbol_rule)
    width_init = len(float_str) + len(sign_symbol)
    num_fill = min_width - width_init
    if num_fill <= 0:
        filled_str = f'{sign_symbol}{float_str}'
    else:
        fill_str = fill * num_fill
        if align == '<':
            filled_str = f'{sign_symbol}{float_str}{fill_str}'
        elif align == '>':
            filled_str = f'{fill_str}{sign_symbol}{float_str}'
        elif align == '=':
            filled_str = f'{sign_symbol}{fill_str}{float_str}'
        elif align == '^':
            l_num_fill = floor(num_fill / 2)
            r_num_fill = ceil(num_fill / 2)
            l_fill_str = fill * l_num_fill
            r_fill_str = fill * r_num_fill
            filled_str = f'{l_fill_str}{sign_symbol}{float_str}{r_fill_str}'
        else:
            raise ValueError
    return filled_str


VAL = 'val'
UNC = 'unc'


def get_prec_driver(val, unc, prec=None, force_unc_prec=True):
    if unc == 0 or not np.isfinite(unc):
        # unc is invalid
        if np.isfinite(val):
            # Choose val if val is valid
            prec_driver = VAL
        else:
            # Otherwise precision not meaningful
            prec_driver = None
    else:
        # unc is valid
        if force_unc_prec:
            # Choose unc if forced
            prec_driver = UNC
        elif prec is None:
            # Choose unc by default if precision is not supplied
            prec_driver = UNC
        elif np.isfinite(val):
            # If not forcing unc precision AND precision is explicitly supplied then choose val.
            prec_driver = VAL
        else:
            # Otherwise revert to unc.
            prec_driver = UNC
    return prec_driver


def get_pdg_num_sig_figs_and_rounded_unc(unc):
    top_digit, bottom_digit = get_top_and_bottom_digit(unc)
    unc_rounded_1 = round(unc, -top_digit + 2)
    top_three_dig = round(unc_rounded_1*10**(-top_digit + 2), 0)
    if 100 <= top_three_dig <= 354:
        num_sig_figs = 1
        updated_unc = round(unc, -top_digit)
    elif 355 <= top_three_dig <= 949:
        num_sig_figs = 2
        updated_unc = round(unc, -top_digit + 1)
    elif 950 <= top_three_dig <= 999:
        num_sig_figs = 2
        updated_unc = 1000 * 10**(top_digit - 2)
    else:
        raise ValueError(f'Unable to parse number of sig figs from {unc}. Top three digits '
                         f'calculated as {top_three_dig}')
    # print(f'{num_sig_figs=}')
    return num_sig_figs, updated_unc


def get_val_unc_str(val,
                    unc,
                    fill=None,
                    align=None,
                    sign_symbol_rule='-',
                    sign_aware_padding=False,
                    min_width=1,
                    grouping_option='',
                    prec=None,
                    prec_type='e',
                    force_unc_prec=True,
                    alternative_mode=False,
                    short_hand_notation=False,
                    pretty_print_mode=False,
                    latex_mode=False,
                    force_paren=False):
    prec_driver = get_prec_driver(val, unc, prec, force_unc_prec)

    val_abs = abs(val)
    # prec_types: fFeEgGr%
    # fF: normal (no exponent), digits_after_decimal - defaults 6 digits after decimal
    # eE: scientific notation, digits_after_decimal -default 6 digits after decimal
    # gG: scientific notation, Just uses logic to parse between f or e and set p.
    # print(f'{prec_driver=}')
    if prec_driver == UNC:
        top_unc_digit, bottom_unc_digit = get_top_and_bottom_digit(unc)
        if prec is None:
            num_sig_figs, unc_rounded = get_pdg_num_sig_figs_and_rounded_unc(unc)
            prec = num_sig_figs
        else:
            num_sig_figs = prec
            unc_rounded = round(unc, -top_unc_digit + num_sig_figs - 1)
        top_unc_digit, _ = get_top_and_bottom_digit(unc_rounded)
        bottom_digit_target = top_unc_digit - num_sig_figs + 1
        # print(f'{bottom_digit_target=}')

        if np.isfinite(val_abs):
            val_rounded = round(val_abs, -bottom_digit_target)
            top_val_digit, _ = get_top_and_bottom_digit(val_rounded)
            top_digit_target = max(top_val_digit, top_unc_digit)
        else:
            top_digit_target = top_unc_digit
            val_rounded = val_abs
        # print(f'{top_digit_target=}')

    elif prec_driver == VAL:
        top_val_digit, _ = get_top_and_bottom_digit(val_abs)
        # Note the prec is not None if prec_driver == VAL.
        if prec_type in 'fF':
            if prec is None:
                prec = 6
            bottom_digit_target = -prec
        elif prec_type in 'eE':
            if prec is None:
                prec = -6
            bottom_digit_target = top_val_digit - prec
        elif prec_type in 'gGrR':
            if prec is None:
                prec = -6
            bottom_digit_target = top_val_digit - prec + 1
        else:
            raise ValueError

        val_rounded = round(val_abs, -bottom_digit_target)
        if np.isfinite(unc):
            unc_rounded = round(unc, -bottom_digit_target)
            top_unc_digit, _ = get_top_and_bottom_digit(unc_rounded)
            top_digit_target = max(top_val_digit, top_unc_digit)
        else:
            top_digit_target = top_val_digit
            unc_rounded = unc
    else:
        top_digit_target = 0
        bottom_digit_target = 0
        val_rounded = val_abs
        unc_rounded = unc
    # at this point bottom_digit_target, top_digit_target, unc_rounded, val_rounded are defined

    if prec_driver is not None:
        if prec_type in 'fF':
            exp = 0
            use_exp = False
        elif prec_type in 'eE':
            exp = top_digit_target
            use_exp = True
        elif prec_type in 'gG':
            # print(f'{prec=}')
            if -4 <= top_digit_target < prec and prec_type in 'gG':
                # fF format
                exp = 0
                use_exp = False
            else:
                # eE format
                exp = top_digit_target
                use_exp = True
        elif prec_type in 'rR':
            if not alternative_mode:
                exp = top_digit_target - top_digit_target % 3
            else:
                exp = top_digit_target + 1 - (top_digit_target + 1) % 3
            use_exp = True
        elif prec_type == '%':
            exp = 0
            use_exp = False
        else:
            raise ValueError(f'Unhandled prec_type {prec_type}')
    else:
        exp = 0
        use_exp = False

    top_digit_target -= exp
    bottom_digit_target -= exp

    if sign_aware_padding:
        sign_aware_fill_symb = '0'
    else:
        sign_aware_fill_symb = ''

    if sign_aware_padding:
        if align is None:
            align = '='
        if fill is None:
            fill = '0'
    if align is None:
        align = '>'
    if fill is None:
        fill = ' '
    invalid_format_str = f'{fill}{align}{sign_aware_fill_symb}{min_width}'
    # print(f'{invalid_format_str=}')
    # print(f'{top_digit_target=}')

    if np.isfinite(val_rounded):
        val_mantissa = val_rounded * 10**-exp

        if val_mantissa == 0:
            if val == 0:
                force_decimal_point = False
            else:
                force_decimal_point = True
        else:
            force_decimal_point = False

        val_base_str = float_to_numeral_str(val_mantissa,
                                            top_digit_target=top_digit_target,
                                            bottom_digit_target=bottom_digit_target,
                                            grouping_option=grouping_option,
                                            force_decimal_point=force_decimal_point)
        # print(f'{val=}')
        val_print_str = float_str_to_filled_str(val_base_str,
                                                float_sign=np.sign(val),
                                                fill=fill,
                                                align=align,
                                                sign_symbol_rule=sign_symbol_rule,
                                                sign_aware_fill=sign_aware_padding,
                                                min_width=min_width)
    else:
        val_print_str = format(val_rounded, invalid_format_str)

    if np.isfinite(unc_rounded):
        unc_mantissa = unc_rounded * 10**-exp
        # print(f'{top_digit_target=}')
        # print(f'{bottom_digit_target=}')
        if unc_mantissa == 0:
            if unc == 0:
                force_decimal_point = False
            else:
                force_decimal_point = True
        else:
            force_decimal_point = False

        unc_base_str = float_to_numeral_str(unc_mantissa,
                                            top_digit_target=top_digit_target,
                                            bottom_digit_target=bottom_digit_target,
                                            grouping_option=grouping_option,
                                            force_decimal_point=force_decimal_point)
        if not short_hand_notation:
            unc_print_str = float_str_to_filled_str(unc_base_str, +1,
                                                    fill=fill,
                                                    align=align,
                                                    sign_symbol_rule='-',
                                                    sign_aware_fill=False,
                                                    min_width=min_width)
        else:
            reg_str = r'(?:^0*\.?0*)([1-9][\d\.]*)$'
            match = re.match(reg_str, unc_base_str)
            if match is not None:
                unc_print_str = match.groups()[0]
            else:
                unc_print_str = '0'
                if force_decimal_point:
                    unc_print_str += '.'
    else:
        unc_print_str = format(unc_rounded, invalid_format_str)

    if latex_mode:
        pm_symb = r'\pm'
        l_paren = r'\left('
        r_paren = r'\right)'
        mult_symb = r'\times'
    elif pretty_print_mode:
        pm_symb = u'±'
        l_paren = '('
        r_paren = ')'
        mult_symb = u'×'
    else:
        pm_symb = '+/-'
        l_paren = '('
        r_paren = ')'
        if prec_type in 'fFeEgGrR':
            if prec_type.isupper():
                mult_symb = 'E'
            else:
                mult_symb = 'e'
        else:
            mult_symb = 'e'

    if not short_hand_notation:
        val_unc_str = f'{val_print_str}{pm_symb}{unc_print_str}'
    else:
        val_unc_str = f'{val_print_str}{l_paren}{unc_print_str}{r_paren}'

    if use_exp:
        val_unc_str = f'{l_paren}{val_unc_str}{r_paren}'
        exp_str = f'{mult_symb}{exp:+03d}'
        return_str = f'{val_unc_str}{exp_str}'
    elif force_paren:
        return_str = f'{l_paren}{val_unc_str}{r_paren}'
    else:
        return_str = val_unc_str

    # print(f'{min_width=}')

    # print(f'{val_rounded=}')
    # print(f'{val_mantissa=}')
    # print(f'{val_print_str=}')
    # print(f'{val_base_str=}')

    # print(f'{unc_rounded=}')
    # print(f'{unc_mantissa=}')
    # print(f'{unc_base_str=}')
    # print(f'{unc_print_str=}')
    return return_str


def format_val_unc(val, unc, format_spec):
    match = re.match(r'''
        (?P<fill>[^{}]??)(?P<align>[<>=^]?)  # fill cannot be { or }
        (?P<sign_symbol_rule>[-+ ]?)
        (?P<alternate_form>\#?)
        (?P<sign_aware_padding>0?)
        (?P<min_width>\d*)
        (?P<grouping_option>[,_]?)
        (?:\.(?P<prec>\d+))?
        (?P<force_unc_prec>u?)  # Precision for the uncertainty?
         # The type can be omitted. Options must not go here:
        (?P<prec_type>[eEfFgGrR%]??)  # n not supported
        (?P<options>[PSLp]*)  # uncertainties-specific flags
         $''',
                     format_spec,
                     re.VERBOSE)

    # Does the format specification look correct?
    if not match:
        raise ValueError(f'Invalid format specification {format_spec}')

    fill = match.group('fill') or ''
    align = match.group('align') or '>'
    sign_symbol_rule = match.group('sign_symbol_rule') or '-'
    alternate_form = 'alternate_form' in match.groupdict()
    sign_aware_padding = 'zero_aware_padding' in match.groupdict()
    min_width = match.group('min_width') or 0
    grouping_option = match.group('grouping_option')
    prec = match.group('prec') or None
    force_unc_prec = 'force_unc_prec' in match.groupdict()
    prec_type = match.group('prec_type') or 'f'
    options = match.group('options') or ''

    short_hand_notation = 'S' in options
    pretty_print_mode = 'P' in options
    latex_mode = 'L' in options
    force_paren = 'p' in options

    return get_val_unc_str(val, unc,
                           fill=fill,
                           align=align,
                           sign_symbol_rule=sign_symbol_rule,
                           sign_aware_padding=sign_aware_padding,
                           min_width=min_width,
                           grouping_option=grouping_option,
                           prec=prec,
                           prec_type=prec_type,
                           force_unc_prec=force_unc_prec,
                           alternative_mode=alternate_form,
                           short_hand_notation=short_hand_notation,
                           pretty_print_mode=pretty_print_mode,
                           latex_mode=latex_mode,
                           force_paren=force_paren)


def main():
    val = 123
    unc = 4563
    print(format_val_unc(val, unc, 'r'))


if __name__ == "__main__":
    main()
