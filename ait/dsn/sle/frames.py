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

from util import *


class TMTransFrame(dict):
    def __init__(self, data=None):
        super(TMTransFrame, self).__init__()

        self._data = []
        self.is_idle = False
        self.has_no_pkts = False
        if data:
            self.decode(data)

    def decode(self, data):
        ''' Decode data as a TM Transfer Frame '''
        header = extract_header(data)
        self['version'] = '0b' + header[0:2]
        self['spacecraft_id'] = hex(int(header[2:12], 2))
        self['virtual_channel_id'] = int(header[12:15], 2)
        self['ocf_flag'] = header[15:16] == '1'
        self['master_chan_frame_count'] = int(header[16:24], 2)
        self['virtual_chan_frame_count'] = int(header[24:32], 2)
        self['sec_header_flag'] = header[32:33] == '1'
        self['sync_flag'] = header[33:34] == '1'
        self['pkt_order_flag'] = header[34:35] == '1'
        self['seg_len_id'] = '0b' + header[35:37]
        self['first_hdr_ptr'] = '0b' + header[37:]

        if self['first_hdr_ptr'] == b'11111111110':
            self.is_idle = True
            return

        if self['first_hdr_ptr'] == b'11111111111':
            self.has_no_pkts = True
            return

        # Process the secondary header. This hasn't been tested ...
        if self['sec_header_flag']:
            self['sec_hdr_ver'] = hexint(data[6]) & 0xC0
            sec_hdr_len = hexint(data[6]) & 0x3F
            sec_hdr_data = data[7:7+sec_hdr_len]
            pkt_data = data[8 + sec_hdr_len:]
        else:
            pkt_data = data[6:]

        # We're assuming that we're getting CCSDS packets w/o secondary
        # headers here. All of this needs to be fleshed out more
        while True:
            if len(pkt_data) == 0:
                break

            pkt_data_len = hexint(pkt_data[4:6])

            if pkt_data_len <= len(pkt_data[6:]):
                self._data.append(pkt_data[6:6 + pkt_data_len])

                try:
                    pkt_data = pkt_data[6 + pkt_data_len:]
                except:
                    break
            # We're not handling the case where packets are split
            # across TM frames at the moment.
            else:
                # print 'Pkt split across TM frames. AAAHHHHH!!!'
                break

    def encode(self):
        pass


class AOSTransFrame(object):
    ''''''
    # TODO: Implement
    pass


class TCTransFrame(object):
    ''''''
    # TODO: Implement
    # See C Space Data Link Protocol pg. 4-1 for further information
    pass
