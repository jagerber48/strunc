import sys
from math import log10
import numpy as np


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
    scale = magnitude + precision
    top_digit = scale - precision - 1
    bottom_digit = -precision
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
            prec=0

        base_format = f'{grouping_option}.{prec}f'
        float_str_base = format(np.abs(val), base_format)

        if force_decimal_point:
            if '.' not in float_str_base:
                float_str_base += '.'

        if top_digit_target > val_top_digit:
            num_top_digit_pad = top_digit_target - val_top_digit
            float_str_padded = '0'*num_top_digit_pad + float_str_base
        else:
            float_str_padded = float_str_base
    else:
        float_str_padded = str(val)

    return float_str_padded


def get_sign_symbol(float_sign, sign_symbol_rule):
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
                            float_sign,
                            fill=None,
                            align=None,
                            sign_symbol_rule='-',
                            sign_aware_fill=False,
                            min_width=0):
    if sign_aware_fill:
        if align is None:
            align = '='
        if fill is None:
            fill = '0'
    if align is None:
        align = '>'
    if fill is None:
        fill = ' '


    sign_symbol = get_sign_symbol(float_sign, sign_symbol_rule)
    width_init = len(float_str) + len(sign_symbol)
    num_fill = width_init - min_width
    if num_fill <= 0:
        filled_str = float_str
    else:
        fill_str = f'{fill}' * num_fill
        if align == '<':
            filled_str = f'{sign_symbol}{float_str}{fill_str}'
        elif align == '>':
            filled_str = f'{fill_str}{sign_symbol}{float_str}'
        elif align == '=':
            filled_str = f'{sign_symbol}{fill_str}{float_str}'
        else:
            raise ValueError
    return filled_str


VAL = 'val'
UNC = 'unc'


def get_prec_driver(val, unc, prec, force_unc_prec):
    if unc == 0 or not np.isfinite():
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
    top_three_dig = round(unc_rounded_1*10**(-top_digit +2), 0)
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
        raise ValueError(f'Unable to parse number of sig figs from {unc}. Top three digits calculated as '
                         f'{top_three_dig}')
    return num_sig_figs, updated_unc


def get_val_unc_str(val, unc,
                    fill, align, sign, sign_aware_fill, min_width, grouping_option,
                    prec, prec_type, force_unc_prec, alternative_mode=False):
    prec_driver = get_prec_driver(val, unc, prec, force_unc_prec)

    # prec_types: fFeEgGr%
    # fF: normal (no exponent), digits_after_decimal - defaults 6 digits after decimal
    # eE: scientific notation, digits_after_decimal -default 6 digits after decimal
    # gG: scientific notation, Just uses logic to parse between f or e and set p.

    if prec_driver == UNC:
        top_unc_digit, bottom_unc_digit = get_top_and_bottom_digit(unc)
        if prec is None:
            num_sig_figs, unc_rounded = get_pdg_num_sig_figs_and_rounded_unc(unc)
        else:
            num_sig_figs = prec
            unc_rounded = round(unc, -top_unc_digit + num_sig_figs - 1)
        val_rounded = round(val, -top_unc_digit + num_sig_figs - 1)



        top_unc_digit, bottom_unc_rounded_digit = get_top_and_bottom_digit(unc_rounded)
        top_val_digit, bottom_val_rounded_digit = get_top_and_bottom_digit(val_rounded)
        top_digit_target = max(top_val_digit, top_unc_digit)
        bottom_digit_target = min(bottom_val_rounded_digit, bottom_unc_rounded_digit)
        val_base_str = float_to_numeral_str(val, top_digit_target,
                                            bottom_digit_target=bottom_digit_target,
                                            grouping_option=grouping_option,
                                            force_decimal_point=)
            val_str = float_to_str(val, fill, align, sign, sign_aware_fill,
                                   min_width, grouping_option, False, False)
            unc_str = float_to_str(val, fill, align, '-', sign_aware_fill,
                                   min_width, grouping_option, False, False)
        elif prec_type in 'eE':



