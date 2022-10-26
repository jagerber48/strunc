from math import floor, log10
import re
import sys
from enum import Enum


class BottomDigMode(Enum):
    SIGDIG = 'SIGNIFICANT_DIGITS'
    PREC = 'PRECISION'


class DisplayMode(Enum):
    PM = 'PLUSMINUS'
    PAREN = 'PARENTHESES'


VAL = 'val'
UNC = 'unc'


def precision_and_scale(x):
    max_digits = sys.float_info.dig
    int_part = int(abs(x))
    if int_part == 0:
        magnitude = 1
    else:
        magnitude = int(log10(int_part)) + 1

    if magnitude >= max_digits:
        return magnitude, 0

    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    precision = int(log10(frac_digits))
    scale = magnitude + precision
    return precision, scale


def get_top_digit_place(number, round_digit_place=None):
    if number == 0:
        return 0
    if round_digit_place is not None:
        number = round(number, -round_digit_place)
    top_digit_place = floor(log10(number))
    return top_digit_place


def float_to_str(number, round_digit_place=None, bottom_digit_place=None, top_digit_place=None,
                 lpad_char='0',
                 force_plus=True):
    print(bottom_digit_place)
    if number >= 0:
        if force_plus:
            sign_str = '+'
        else:
            sign_str = ''
    else:
        sign_str = '-'
    number = abs(number)
    if round_digit_place is None:
        precision, scale = precision_and_scale(number)
        round_digit_place = -precision
    if bottom_digit_place is None:
        bottom_digit_place = round_digit_place
    if bottom_digit_place > round_digit_place:
        raise ValueError(f'\'bottom_digit_place\' ({bottom_digit_place}) must be less or equal to '
                         f'\'round_digit_place\' ({round_digit_place})')
    number = float(number)
    number = round(number, -round_digit_place)
    if bottom_digit_place >= 0:
        number_string = str(int(number))
    else:
        number_string = f'{number:.{-bottom_digit_place}f}'

    if top_digit_place is not None:
        number_top_digit_place = get_top_digit_place(number, round_digit_place=round_digit_place)
        if top_digit_place > number_top_digit_place:
            if number_top_digit_place < 0:
                num_lpad_char = top_digit_place
            else:
                num_lpad_char = top_digit_place - number_top_digit_place
            lpad_str = lpad_char * num_lpad_char
            number_string = sign_str + lpad_str + number_string
    else:
        number_string = sign_str + number_string

    return number_string


def get_val_unc_exp_strs(val, unc,
                         bottom_digit_mode=BottomDigMode.SIGDIG, bottom_digit_spec=2,
                         bottom_digit_driver=UNC,
                         exp_mode='eng_low', exp_driver=VAL,
                         top_digit_place=None, lpad_char='0',
                         force_plus=True):
    abs_val = abs(val)
    unc = abs(unc)

    if bottom_digit_driver == UNC:
        bottom_digit_number = unc
    elif bottom_digit_driver == VAL:
        bottom_digit_number = abs_val
    else:
        raise ValueError

    if bottom_digit_mode == BottomDigMode.SIGDIG:
        if bottom_digit_spec < 1:
            raise ValueError(
                f'is \'sigdig\' mode \'bottom_digit_spec\' must be >= 1, not {bottom_digit_spec}.')
        number_top_digit_place = get_top_digit_place(bottom_digit_number)
        guess_round_digit_place = number_top_digit_place - bottom_digit_spec + 1
        number_top_digit_place = get_top_digit_place(bottom_digit_number, guess_round_digit_place)
        round_digit_place = number_top_digit_place - bottom_digit_spec + 1
    elif bottom_digit_mode == BottomDigMode.PREC:
        round_digit_place = -bottom_digit_spec
    else:
        raise ValueError

    if exp_mode != 'none':
        if exp_driver == UNC:
            exp_digit_number = unc
        else:
            exp_digit_number = abs_val

        exp = floor(log10(exp_digit_number))

        if exp_mode == 'eng_low':
            exp = exp + 1 - (exp + 1) % 3
        elif exp_mode == 'eng_high':
            exp = exp - exp % 3

        val = val * 10 ** -exp
        unc = unc * 10 ** -exp
        print(round_digit_place, exp)
        round_digit_place -= exp
        if bottom_digit_mode == BottomDigMode.PREC:
            round_digit_place = min(round_digit_place, 0)

        if top_digit_place is not None:
            top_digit_place -= exp
    else:
        exp = 0

    exp_str = f'{exp:+03d}'

    val_str = float_to_str(val, round_digit_place, round_digit_place, top_digit_place, lpad_char,
                           force_plus=force_plus)
    unc_str = float_to_str(unc, round_digit_place, round_digit_place, top_digit_place, lpad_char,
                           force_plus=False)
    return val_str, unc_str, exp_str


PM_SYMBOLS = {'pretty-print': u'±', 'latex': r' \pm ', 'default': '+/-'}


def format_val_unc_exp_str(val_str, unc_str, exp_str, disp_mode='pm', force_exp=False,
                           exp_char='e'):
    if disp_mode == 'pm':
        val_unc_str = f'{val_str} +/- {unc_str}'
    elif disp_mode == 'paren':
        reg_str = r'(?:^0*\.?0*)([1-9][\d\.]*)$'
        match = re.match(reg_str, unc_str)
        if match is not None:
            unc_str = match.groups()[0]
        else:
            unc_str = 0

        val_unc_str = f'{val_str}({unc_str})'
    else:
        raise ValueError

    if not force_exp:
        try:
            exp = int(exp_str)
        except ValueError:
            exp = 0
        if exp != 0:
            use_exp = True
        else:
            use_exp = False
    else:
        use_exp = True

    if use_exp:
        val_unc_exp_str = f'({val_unc_str}){exp_char}{exp_str}'
    else:
        val_unc_exp_str = val_unc_str

    return val_unc_exp_str


LPAD_CHAR = 'lpad_char'
TOP_DIG_PLACE = 'top_dig_place'
BOT_DIG_MODE = 'bot_dig_mode'
BOT_DIG_SPEC = 'bot_dig_spec'
BOT_DIG_DRIVER = 'bot_dig_driver'
EXP_MODE = 'exp_mode'
EXP_DRIVER = 'exp_driver'
FORCE_PLUS = 'force_plus'
EXP_CHAR = 'exp_char'
DISP_MODE = 'disp_mode'


def format_val_unc(val, unc, fmt_str=''):
    # TODO: Documentation
    # TODO: Handle 0, nan, and inf values for val and unc
    # TODO: Use particle datagroup uncertainty sig fig convention by default when appropriate
    # TODO: Address use of "magic strings" through, replace with enums?
    reg_str = (fr'(?:(?P<{LPAD_CHAR}>[0 ])(?P<{TOP_DIG_PLACE}>\d+))?'
               fr'(?:(?P<{BOT_DIG_MODE}>\.|_)(?P<{BOT_DIG_SPEC}>\d+)?)?'
               fr'(?P<{BOT_DIG_DRIVER}>[uv]?)'
               fr'(?P<{EXP_MODE}>[LHSN]?)'               
               fr'(?P<{EXP_DRIVER}>[uv]?)'
               fr'(?P<{FORCE_PLUS}>\+?)'
               fr'(?P<{EXP_CHAR}>[eE]?)'
               fr'(?P<{DISP_MODE}>P?)$')

    match = re.match(reg_str, fmt_str)

    if match is None:
        raise ValueError(f'invalid format string: \'{fmt_str}\'.')

    lpad_char = match[LPAD_CHAR]
    if lpad_char is None:
        lpad_char = '0'

    top_digit_place = match[TOP_DIG_PLACE]
    if top_digit_place is not None:
        top_digit_place = int(top_digit_place)

    bottom_digit_mode = match[BOT_DIG_MODE]
    if bottom_digit_mode is None:
        bottom_digit_mode = '_'
    if bottom_digit_mode == '.':
        bottom_digit_mode = BottomDigMode.PREC
    elif bottom_digit_mode == '_':
        bottom_digit_mode = BottomDigMode.SIGDIG
    else:
        raise ValueError

    bottom_digit_spec = match[BOT_DIG_SPEC]
    if bottom_digit_spec is not None:
        bottom_digit_spec = int(bottom_digit_spec)
    # Default handling below

    bottom_digit_driver = match[BOT_DIG_DRIVER]
    if bottom_digit_driver == '':
        unc_prec, _ = precision_and_scale(unc)
        val_prec, _ = precision_and_scale(val)
        if unc_prec > val_prec:
            bottom_digit_driver = UNC
        else:
            bottom_digit_driver = VAL
    elif bottom_digit_driver == 'u':
        bottom_digit_driver = UNC
    elif bottom_digit_driver == 'v':
        bottom_digit_driver = VAL
    else:
        raise ValueError

    exp_mode = match[EXP_MODE]
    if exp_mode == '':
        exp_mode = 'L'
    if exp_mode == 'L':
        exp_mode = 'eng_low'
    elif exp_mode == 'H':
        exp_mode = 'eng_high'
    elif exp_mode == 'S':
        exp_mode = 'sci'
    elif exp_mode == 'N':
        exp_mode = 'none'
    else:
        raise ValueError

    exp_driver = match[EXP_DRIVER]
    if exp_driver == '':
        if val > unc:
            exp_driver = VAL
        else:
            exp_driver = UNC
    elif exp_driver == 'u':
        exp_driver = UNC
    elif exp_driver == 'v':
        exp_driver = VAL
    else:
        raise ValueError

    if bottom_digit_spec is None:
        if bottom_digit_mode == BottomDigMode.SIGDIG:
            if bottom_digit_driver == UNC:
                unc_top_digit = get_top_digit_place(unc)
                unc_pdg_ref = unc * 10**(-unc_top_digit + 2)
                unc_pdg_ref = round(unc_pdg_ref, 0)
                if 100 <= unc_pdg_ref <= 354:
                    bottom_digit_spec = 2
                elif 355 <= unc_pdg_ref <= 949:
                    bottom_digit_spec = 1
                elif 950 <= unc_pdg_ref <= 999:
                    bottom_digit_spec = 2
                    unc = 1000 * 10**(unc_top_digit - 2)
                else:
                    raise ValueError('Error parsing particle data group uncertainty precision')
            elif bottom_digit_driver == VAL:
                val_precision, _ = precision_and_scale(val)
                val_top_digit = get_top_digit_place(val)
                bottom_digit_spec = val_top_digit + val_precision + 1
        elif bottom_digit_mode == BottomDigMode.PREC:
            if bottom_digit_driver == VAL:
                bottom_digit_spec, _ = precision_and_scale(val)
            elif bottom_digit_driver == UNC:
                bottom_digit_spec, _ = precision_and_scale(unc)
            else:
                raise ValueError
        else:
            raise ValueError

    force_plus = match[FORCE_PLUS]
    if force_plus == '':
        force_plus = False
    elif force_plus == '+':
        force_plus = True
    else:
        raise ValueError

    exp_char = match[EXP_CHAR]
    if exp_char == 'e' or exp_char == 'E':
        force_exp = True
    elif exp_char == '':
        exp_char = 'e'
        force_exp = False
    else:
        raise ValueError

    disp_mode = match[DISP_MODE]
    if disp_mode == '':
        disp_mode = 'pm'
    elif disp_mode == 'P':
        disp_mode = 'paren'
    else:
        raise ValueError

    val_str, unc_str, exp_str = get_val_unc_exp_strs(val, unc,
                                                     bottom_digit_mode=bottom_digit_mode,
                                                     bottom_digit_spec=bottom_digit_spec,
                                                     bottom_digit_driver=bottom_digit_driver,
                                                     exp_mode=exp_mode, exp_driver=exp_driver,
                                                     top_digit_place=top_digit_place,
                                                     lpad_char=lpad_char,
                                                     force_plus=force_plus)

    val_unc_err_str = format_val_unc_exp_str(val_str, unc_str, exp_str,
                                             disp_mode=disp_mode, force_exp=force_exp,
                                             exp_char=exp_char)

    return val_unc_err_str


class UfloatLight:
    def __init__(self, value, uncertainty):
        self.value = value
        self.uncertainty = uncertainty

    def __mul__(self, other):
        new_value = self.value * other
        new_uncertainty = self.uncertainty * other
        return UfloatLight(new_value, new_uncertainty)

    def __repr__(self):
        return f'{self.value} +/- {self.uncertainty}'

    def __format__(self, format_spec):
        return format_val_unc(self.value, self.uncertainty, format_spec)


def main():
    u = UfloatLight(34523, .0123)
    u *= 1e-0
    print(u)
    print(f'{u:.3vS}')


if __name__ == "__main__":
    main()
