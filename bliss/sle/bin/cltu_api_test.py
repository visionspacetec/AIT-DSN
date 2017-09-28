#!/usr/bin/env python
#
# Usage:
#   python cltu_api_test.py
#
# SSPSim Config:
# 1. Open "MISSION MANAGERS" >  "Test" > "FCLTU - PLOP1"
# 2. Open "PRODUCTION" > "TestBaseband2"
# 3. Activate the production interface by clicking the
#       green arrow labelled "TC"
# 4. Activate the Mission Manager interface by clicking the
#       green arrow labelled "SVC"
#
# Run the script per the usage instructions above. You should see
# logging informing you of the various steps in the script. If all
# runs as expected you should see confirmations back from the sim
# indicating which cltu id was last processed. These will also be
# mirrored in the sim GUI where you'll be informed when a particular
# cltu id has been successfully radiated.

import datetime as dt
import time

import bliss.sle

cltu_mngr = bliss.sle.CLTU(
    hostname='atb-ocio-sspsim.jpl.nasa.gov',
    port=5100,
    inst_id='sagr=LSE-SSC.spack=Test.fsl-fg=1.cltu=cltu1'
)

cltu_mngr.connect()
time.sleep(2)

cltu_mngr.bind()
time.sleep(2)

cltu_mngr.start()
time.sleep(2)

junk_data = bytearray('\x00'*79)
cltu_mngr.upload_cltu(junk_data)
time.sleep(4)
cltu_mngr.upload_cltu(junk_data)
time.sleep(4)
cltu_mngr.upload_cltu(junk_data)
time.sleep(4)

cltu_mngr.stop()
time.sleep(2)

cltu_mngr.unbind()
time.sleep(2)

cltu_mngr.disconnect()
time.sleep(2)