import re

from strunc import pfloat


si_val_to_prefix_dict = {30: 'Q',
                         27: 'R',
                         24: 'Y',
                         21: 'Z',
                         18: 'E',
                         15: 'P',
                         12: 'T',
                         9: 'G',
                         6: 'M',
                         3: 'k',
                         0: '',
                         -3: 'm',
                         -6: 'u',
                         -9: 'n',
                         -12: 'p',
                         -15: 'f',
                         -18: 'a',
                         -21: 'z',
                         -24: 'y',
                         -27: 'r',
                         -30: 'q'}

iec_val_to_prefix_dict = {0: '',
                          10: 'K',
                          20: 'M',
                          30: 'G',
                          40: 'T',
                          50: 'P',
                          60: 'E'}


def replace_prefix(num_str: str):
    match = re.match(r'''
                         ^
                         (?P<mantissa>\d+\.?\d*)
                         ((?P<exp_type>[be])(?P<exp_val>[+-]?\d+))?
                         $
                      ''', num_str, re.VERBOSE)

    mantissa = match.group('mantissa')
    exp_type = match.group('exp_type')
    if not exp_type:
        return num_str
    exp_val = match.group('exp_val') or 0
    exp_val = int(exp_val)

    if exp_type == 'e':
        val_to_prefix_dict = si_val_to_prefix_dict
    else:
        val_to_prefix_dict = iec_val_to_prefix_dict
    try:
        prefix = val_to_prefix_dict[exp_val]
        return f'{mantissa} {prefix}'
    except KeyError:
        return num_str


class prefix_float(float):
    def __format__(self, format_spec: str):
        pfloat_num = pfloat(self)
        if format_spec.endswith('p'):
            pfloat_format_spec = format_spec[:-1]
            pfloat_str = f'{pfloat_num:{pfloat_format_spec}}'
            return replace_prefix(pfloat_str)
        else:
            return f'{pfloat_num:{format_spec}}'


def main():
    num = prefix_float(1563e14)
    fmt = '_3Bp'
    print(f'{num=}')
    print(f'{fmt=}')
    num_fmted = f'{num:{fmt}}'
    print(num_fmted)


if __name__ == "__main__":
    main()