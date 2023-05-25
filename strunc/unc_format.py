import re

from strunc.modes import PrecMode
from strunc.formatting import get_round_digit, get_top_and_bottom_digit, get_top_digit
from strunc.pfloat_format import parse_format_spec, pattern, FormatSpec
from strunc import pfloat


def format_val_unc(val: float, unc: float, fmt: str):
    format_spec = parse_format_spec(fmt)
    match = re.match(pattern, fmt)
    if match.group('width'):
        match_widths = True
    else:
        match_widths = False

    pval = pfloat(val)
    punc = pfloat(unc)

    unc_top_digit, unc_bottom_digit = get_top_and_bottom_digit(unc)
    round_digit = get_round_digit(unc_top_digit, unc_bottom_digit, format_spec.precision,
                                  PrecMode.SIG_FIG)

    prec = -round_digit

    user_top_digit = format_spec.width

    if match_widths:
        val_top_digit = get_top_digit(val)
        new_top_digit = max(user_top_digit, val_top_digit, unc_top_digit)
    else:
        new_top_digit = user_top_digit

    val_format_spec = FormatSpec(format_spec.fill_char,
                                 sign_mode=format_spec.sign_mode,
                                 force_zero_positive=format_spec.force_zero_positive,
                                 alternate_mode=format_spec.alternate_mode,
                                 width=format_spec.width,
                                 grouping_option_1=format_spec.grouping_option_1,
                                 grouping_option_2=format_spec.grouping_option_2,
                                 prec_mode=PrecMode.PREC,
                                 precision=prec,
                                 format_mode=format_spec.format_mode,
                                 capital_exp_char=format_spec.capital_exp_char,
                                 percent_mode=False,
                                 # exp=
                                 )




