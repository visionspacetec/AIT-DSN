#!/usr/bin/env python

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

# Usage:
#   python rcf_api_test.py

import datetime as dt
import time
import ait.dsn.sle

hostname = '192.168.3.30'
port = 55529
inst_id = 'sagr=3.spack=NNO-PASS0001.rsl-fg=1.raf=onlt1'
spacecraft_id = 3
trans_frame_ver_num = 0
version = 2

raf_mngr = ait.dsn.sle.RAF(
    hostname=hostname,
    port=port,
    inst_id=inst_id,
    spacecraft_id=spacecraft_id,
    trans_frame_ver_num=trans_frame_ver_num,
    version=version,
    auth_level="none"
)

raf_mngr.connect()
time.sleep(2)

raf_mngr.bind()
time.sleep(2)

start = dt.datetime(2017, 01, 01)
end = dt.datetime(2019, 01, 01)
# raf_mngr.start(start, end, 250, 0, virtual_channel=6)
# raf_mngr.start(dt.datetime(1958, 1, 1), dt.datetime(2020, 1, 1), spacecraft_id, 0, master_channel=False, virtual_channel=1)
raf_mngr.start(None, None, frame_quality='allFrames')

try:
    while True:
        time.sleep(0)
except:
    pass
finally:

    raf_mngr.stop()
    time.sleep(2)

    raf_mngr.unbind(reason='other')
    time.sleep(2)

    raf_mngr.disconnect()
    time.sleep(2)
