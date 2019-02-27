# Advanced Multi-Mission Operations System (AMMOS) Instrument Toolkit (AIT)
# Bespoke Link to Instruments and Small Satellites (BLISS)
#
# Copyright 2017, by the California Institute of Technology. ALL RIGHTS
# RESERVED. United States Government Sponsorship acknowledged. Any
# commercial use must be negotiated with the Office of Technology Transfer
# at the California Institute of Technology.
#
# This software may be subject to U.S. export control laws. By accepting
# this software, the user agrees to comply with all applicable U.S. export
# laws and regulations. User has the responsibility to obtain export licenses,
# or other export authority as may be required before exporting such
# information to foreign countries or providing access to foreign persons.

import binascii


def hexint(b):
    if not b:
        return int()
    else:
        return int(binascii.hexlify(b), 16)


def print_dict(dictionary, add_dashes, print_data=False):
    """Prints the content of a dict
    :param dictionary: The dict to print
    :type dictionary: dict
    :param add_dashes: Set True for dashes at the end
    :type add_dashes: bool
    :param print_data: Set True to print the 'data' field
    :type print_data: bool
    :return:
    """
    max_len = 0
    offset = 10
    if "data" in dictionary and not print_data:
        dictionary.pop("data")
    for key in dictionary:
        if len(key) > max_len:
            max_len = len(key)
    for key in dictionary:
        print(key + " " * (max_len - len(key) + offset) + str(dictionary[key]))
    if add_dashes:
        print("-" * max_len)


def extract_header(data):
    return format(int(data[:12], 16), '048b')