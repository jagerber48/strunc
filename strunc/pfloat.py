from strunc.pfloat_format import parse_format_spec, pformat_float


class pfloat(float):
    def __format__(self, format_spec: str):
        format_spec_data = parse_format_spec(format_spec)
        return pformat_float(self, format_spec_data)


def main():
    num = pfloat(20750042)
    fmt = '__r'
    print(f'{num=}')
    print(f'{fmt=}')
    num_fmted = f'{num:{fmt}}'
    print(num_fmted)


if __name__ == "__main__":
    main()
