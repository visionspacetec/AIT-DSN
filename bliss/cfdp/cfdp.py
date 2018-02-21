import os
import socket
import time
import gevent
import gevent.socket
import gevent.queue
from bliss.cfdp.mib import MIB
from bliss.cfdp.machines.sender1 import Sender1
from bliss.cfdp.machines.receiver1 import Receiver1
from bliss.cfdp.primitives import RequestType, TransmissionMode, FileDirective, Role
from bliss.cfdp.events import Event
from bliss.cfdp.request import create_request_from_type
from bliss.cfdp.pdu import make_pdu_from_bytes, Header
from bliss.cfdp.util import write_pdu_to_file

import traceback
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)-10s %(message)-100s %(filename)s:%(lineno)s',
                    datefmt='%m-%d %H:%M')

class CFDP(object):
    """
    CFDP class to manage connection handler, routing handler, Txs
    """

    mib = MIB()
    transaction_counter = 0
    outgoing_pdu_queue = gevent.queue.Queue()
    incoming_pdu_queue = gevent.queue.Queue()

    def __init__(self, entity_id):
        # State machines for current transactions (basically just transactions. Can be Class 1 or 2 sender or receiver
        self._machines = {}
        # temporary handler for getting pdus from directory and putting into incoming queue
        self._read_pdu_handler = gevent.spawn(read_pdus, self)
        # Spawn handlers for incoming and outgoing data
        self._receiving_handler = gevent.spawn(receiving_handler, self)
        self._sending_handler = gevent.spawn(sending_handler, self)

        self._transaction_handler = gevent.spawn(transaction_handler, self)

        # set entity id in MIB
        self.mib.set_local_entity_id(entity_id)

        # temporary list for holding PDUs that have been read from file
        self.received_pdu_files = []


    def connect(self):
        """Connect with TC here"""
        self._socket = gevent.socket.socket()

        # Connect to localhost:8000 for now
        try:
            self._socket.connect(('127.0.0.1', 8000))
            print 'Connected', self._socket
        except socket.error as e:
            raise e

    def disconnect(self):
        """Disconnect TC here"""
        self._socket.close()
        self._receiving_handler.kill()
        self._sending_handler.kill()

    def _increment_tx_counter(self):
        self.transaction_counter += 1
        return self.transaction_counter

    def send(self, pdu):
        logging.debug('Adding pdu ' + str(pdu) + ' to queue')
        self.outgoing_pdu_queue.put(pdu)

    def put(self, destination_id, source_path, destination_path, transmission_mode=TransmissionMode.NO_ACK):
        """Put request initiated. This means we are creating a Sender. For now Class 1 Sender"""
        # TODO other parameters for a put request
        # Put request creates a new state machine/transaction
        transaction_num = self._increment_tx_counter()
        request = create_request_from_type(RequestType.PUT_REQUEST,
                          destination_id=destination_id,
                          source_path=source_path,
                          destination_path=destination_path,
                          transmission_mode=transmission_mode)
        # if transmission_mode == TransmissionMode.ACK:
        #     # TODO sender 2
        #     machine = Sender1(self, transaction_num, request=request)
        # else:
        machine = Sender1(self, transaction_num)
        # Update state table to begin stuff
        machine.update_state(event=Event.RECEIVED_PUT_REQUEST, request=request)
        # Add transaction to list
        self._machines[transaction_num] = machine

    def report(self, transaction_id):
        """Report.request -- user request for status report of transaction"""
        request = create_request_from_type(RequestType.REPORT_REQUEST, transaction_id=transaction_id)

    def cancel(self, transaction_id):
        """Cancel.request -- user request to cancel transaction"""
        request = create_request_from_type(RequestType.CANCEL_REQUEST, transaction_id=transaction_id)

    def suspend(self, transaction_id):
        """Suspend.request -- user request to suspend transaction"""
        request = create_request_from_type(RequestType.SUSPEND_REQUEST, transaction_id=transaction_id)

    def resume(self, transaction_id):
        """Resume.request -- user request to resume transaction"""
        request = create_request_from_type(RequestType.RESUME_REQUEST, transaction_id=transaction_id)

PDU_TMP_PATH = '/tmp/cfdp/pdu/'

def read_pdus(instance):
    while True:
        gevent.sleep(0)
        try:
            # logging.debug('Looking for PDUs to read with entity id ' + str(instance.mib.get_local_entity_id()))
            for pdu_filename in os.listdir(PDU_TMP_PATH):
                if pdu_filename.startswith(instance.mib.get_local_entity_id() + '_'):
                    if pdu_filename not in instance.received_pdu_files:
                        # cache file so that we know we read it
                        instance.received_pdu_files.append(pdu_filename)
                        # add to incoming so that receiving handler can deal with it
                        pdu_full_path = os.path.join(PDU_TMP_PATH, pdu_filename)
                        logging.debug('Possible file ' + pdu_filename)
                        with open(pdu_full_path, 'rb') as pdu_file:
                            # add raw file contents to incoming queue
                            pdu_file_bytes = pdu_file.read()
                            instance.incoming_pdu_queue.put(pdu_file_bytes)
                        break
        except Exception as e:
            pass
            # logging.debug("EXCEPTION: " + e.message)
            # logging.debug(traceback.format_exc())
        gevent.sleep(2)


def receiving_handler(instance):
    """
    GREENLET: Handles routing of incoming PDUs
    :param instance: CFDP instance
    :return:
    """

    # For now, read PDUs from ROOT directory and route to transactions
    while True:
        gevent.sleep(0)
        try:
            # data = instance._socket.recv(8)
            # print "Current Data:", data

            pdu_bytes = instance.incoming_pdu_queue.get(block=False)
            pdu = read_incoming_pdu(pdu_bytes)
            logging.debug('Incoming PDU Type: ' + str(pdu.header.pdu_type))

            machine = None
            transaction_num = pdu.header.transaction_seq_num
            if transaction_num in instance._machines:
                machine = instance._machines[transaction_num]

            if pdu.header.pdu_type == Header.FILE_DATA_PDU:
                # If its file data we'll concat to file
                logging.debug('Received File Data Pdu')
                if machine is None:
                    logging.debug(
                        'Ignoring File Data for transaction that doesn\'t exist: {}'.format(transaction_num))
                else:
                    machine.update_state(Event.RECEIVED_FILEDATA_PDU, pdu=pdu)
            elif pdu.header.pdu_type == Header.FILE_DIRECTIVE_PDU:
                logging.debug('Received File Directive Pdu: ' + str(pdu.file_directive_code))
                if pdu.file_directive_code  == FileDirective.METADATA:
                    # If machine doesn't exist, create a machine for this transaction
                    if machine is None:
                        machine = Receiver1(instance, transaction_num)
                        instance._machines[transaction_num] = machine

                    machine.update_state(Event.RECEIVED_METADATA_PDU, pdu=pdu)
                elif pdu.file_directive_code  == FileDirective.EOF:
                    if machine is None:
                        logging.debug('Ignoring EOF for transaction that doesn\'t exist: {}'.format(transaction_num))
                    else:
                        machine.update_state(Event.RECEIVED_EOF_NO_ERROR_PDU, pdu=pdu)
        except gevent.queue.Empty:
            pass
        except Exception as e:
            logging.debug("EXCEPTION: " + e.message)
            logging.debug(traceback.format_exc())
        gevent.sleep(1)


def read_incoming_pdu(pdu):
    # Transform into bytearray because that is how we wrote it out
    # Will make it an array of integer bytes
    pdu_bytes = [b for b in bytearray(pdu)]
    logging.debug('PDU Bytes: ' + str(pdu_bytes))
    return make_pdu_from_bytes(pdu_bytes)


def write_outgoing_pdu(pdu, pdu_filename=None, output_directory=PDU_TMP_PATH):
    """
    Temporary fcn to write pdu to file, in lieu of sending over some TC
    :param pdu:
    :param destination_id:
    :return:
    """
    # encode pdu to bits or something and deliver
    # in actuality, for now we will just write to file
    pdu_bytes = pdu.to_bytes()
    # make a filename of destination id + time
    if pdu_filename is None:
        pdu_filename = pdu.header.destination_entity_id + '_' + str(int(time.time())) + '.pdu'
    pdu_file_path = os.path.join(output_directory, pdu_filename)
    logging.debug('PDU file path ' + str(pdu_file_path))
    # https://stackoverflow.com/questions/17349918/python-write-string-of-bytes-to-file
    # pdu_bytes is an array of integers that need to be converted to hex
    write_pdu_to_file(pdu_file_path, bytearray(pdu_bytes))


def sending_handler(instance):
    """
    GREENLET: Handles sending PDUs over UT layer
    :param instance: CFDP instance
    :return:
    """
    # For now, write PDUs to ROOT directory
    while True:
        gevent.sleep(0)
        try:
            pdu = instance.outgoing_pdu_queue.get(block=False)
            logging.debug('Got PDU from outgoing queue: ' + str(pdu))
            write_outgoing_pdu(pdu)
            logging.debug('PDU transmitted: ' + str(pdu))
        except gevent.queue.Empty:
            pass
        except Exception as e:
            logging.debug('Sending handler exception: ' + e.message)
            logging.debug(traceback.format_exc())
        gevent.sleep(1)


def transaction_handler(instance):
    while True:
        gevent.sleep(0)
        try:
            # TODO add more events here e.g. timer checks, etc

            # Loop through once to prioritize sending file directives
            for trans_num, machine in instance._machines.items():
                machine.update_state(Event.SEND_FILE_DIRECTIVE)

            # Loop again to send file data
            for trans_num, machine in instance._machines.items():
                if machine.role == Role.CLASS_1_SENDER:
                    machine.update_state(Event.SEND_FILE_DATA)
        except:
            pass
        # Evaluate every 3 sec
        gevent.sleep(3)

