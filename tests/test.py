import unittest

from strunc.pformat_float import pfloat


cases: dict[float, dict[str, str]] = {
    123.456: {'': '123.456',
              'd': '123.456',
              'e': '1.23456e+02',
              'r': '123.456e+00',
              'R': '0.123456e+03',
              '.3': '123.456',
              '.3d': '123.456',
              '.3e': '1.235e+02',
              '.3r': '123.456e+00',
              '.3R': '0.123e+03',
              '_3': '123',
              '_3d': '123',
              '_3e': '1.23e+02',
              '_3r': '123e+00',
              '_3R': '0.123e+03',
              '+': '+123.456',
              '+d': '+123.456',
              '+e': '+1.23456e+02',
              '+r': '+123.456e+00',
              '+R': '+0.123456e+03',
              ' ': ' 123.456',
              ' d': ' 123.456',
              ' e': ' 1.23456e+02',
              ' r': ' 123.456e+00',
              ' R': ' 0.123456e+03',
              '4': '00123.456',
              '4d': '00123.456',
              '4e': '00001.23456e+02',
              '4r': '00123.456e+00',
              '4R': '00000.123456e+03',
              },
    -0.031415: {'': '-0.031415',
                'd': '-0.031415',
                'e': '-3.1415e-02',
                'r': '-31.415e-03',
                'R': '-31.415e-03',
                '.3': '-0.031',
                '.3d': '-0.031',
                '.3e': '-3.141e-02',
                '.3r': '-31.415e-03',
                '.3R': '-31.415e-03',
                '_3': '-0.0314',
                '_3d': '-0.0314',
                '_3e': '-3.14e-02',
                '_3r': '-31.4e-03',
                '_3R': '-31.4e-03',
                '+': '-0.031415',
                '+d': '-0.031415',
                '+e': '-3.1415e-02',
                '+r': '-31.415e-03',
                '+R': '-31.415e-03',
                ' ': '-0.031415',
                ' d': '-0.031415',
                ' e': '-3.1415e-02',
                ' r': '-31.415e-03',
                ' R': '-31.415e-03',
                '4': '-00000.031415',
                '4d': '-00000.031415',
                '4e': '-00003.1415e-02',
                '4r': '-00031.415e-03',
                '4R': '-00031.415e-03',
                },
    0: {'': '0',
        'd': '0',
        'e': '0e+00',
        'r': '0e+00',
        'R': '0e+00',
        '.3': '0.000',
        '.3d': '0.000',
        '.3e': '0.000e+00',
        '.3r': '0.000e+00',
        '.3R': '0.000e+00',
        '_3': '0.00',
        '_3d': '0.00',
        '_3e': '0.00e+00',
        '_3r': '0.00e+00',
        '_3R': '0.00e+00',
        '2.3': '000.000',
        '2.3d': '000.000',
        '2.3e': '000.000e+00',
        '2.3r': '000.000e+00',
        '2.3R': '000.000e+00',
        '2_3': '000.00',
        '2_3d': '000.00',
        '2_3e': '000.00e+00',
        '2_3r': '000.00e+00',
        '2_3R': '000.00e+00'},
    float('nan'): {'': 'nan'},
    float('inf'): {'': 'inf'},
    float('-inf'): {'': '-inf'}
}

    # ,
    # FormatTestCase(val=12.34,
    #                unc=np.nan,
    #                fmt_str_dict={'': '12.34+/-nan',
    #                              'u': '12.34+/-nan',
    #                              'S': '12.34(nan)'}) # TODO Is the the expected/desired behavior?
    # ,
    # FormatTestCase(val=12.34,
    #                unc=np.inf,
    #                fmt_str_dict={'': '12.34+/-inf',
    #                              'u': '12.34+/-inf',
    #                              'S': '12.34(inf)'})
    # ,
    # FormatTestCase(val=np.nan,
    #                unc=12.34,
    #                fmt_str_dict={'': 'nan+/-12',
    #                              'u': 'nan+/-12',
    #                              'S': 'nan+/-12'})
    # # TODO Is the the expected/desired behavior?
    # ,
    # FormatTestCase(val=np.inf,
    #                unc=12.34,
    #                fmt_str_dict={'': 'inf+/-12',
    #                              'u': 'inf+/-12',
    #                              'S': 'inf+/-12',
    #                              'v': 'inf+/-12'})
    # ,
    # FormatTestCase(val=np.nan,
    #                unc=np.nan,
    #                fmt_str_dict={'': 'nan+/-nan',
    #                              'u': 'nan+/-nan',
    #                              'S': 'nan+/-nan'})


class TestFormatting(unittest.TestCase):
    def test(self):
        for num, fmt_dict in cases.items():
            for format_spec, expected_num_str in fmt_dict.items():
                pnum = pfloat(num)
                pnum_str = f'{pnum:{format_spec}}'
                with self.subTest(num=num, format_spec=format_spec,
                                  expected_num_str=expected_num_str,
                                  actual_num_str=pnum_str):
                    assert pnum_str == expected_num_str


if __name__ == '__main__':
    unittest.main()
