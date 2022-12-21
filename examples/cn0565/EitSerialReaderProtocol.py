#TODO: Implement HDLC protocol
"""
Loosely Based on https://github.com/pyserial/pyserial/blob/master/examples/at_protocol.py
"""
import logging
import serial
import serial.threaded
import serial.tools.list_ports
import threading
import numpy as np
import struct
import adi

try:

    import queue
except ImportError:
    import Queue as queue

class EitSerialReaderException(Exception):
    pass

class EitSerialReaderProtocol(serial.threaded.LineReader):
    TERMINATOR = b'\n'

    def __init__(self):
        super(EitSerialReaderProtocol,self).__init__()
        self.alive = True
        self.responses = queue.Queue()
        self.events = queue.Queue()
        self._event_thread = threading.Thread(target=self.process_event)
        self._event_thread.daemon = True
        self._event_thread.name = 'eitSerial-event'
        self._event_thread.start()
        self.lock= threading.Lock()

    def stop(self):
        """
        Stop the event processing thread and abort pending commands
        """
        self.alive=False
        self.events.put(None)
        self.events.put('<exit>')

    def process_event(self):
        """
        Process events separately in another thread. 
        """
        while self.alive:
            try:
                self.handle_event(self.events.get())
            except:
                logging.exception("process_event")
    
    def handle_line(self, line):
        """
        Handle input from serial port and check for events.
        """
        
        if line.startswith("!"):
            self.events.put(line)
        else:
            self.responses.put(line)

    def command(self,command,response="OK",timeout=5):
        with self.lock:
            self.write_line(command)
            lines=[]
            while True:
                try:
                    line = self.responses.get(timeout=timeout)
                    if line == response:
                        return lines
                    else:
                        lines.append(line)
                except queue.Empty:
                    raise EitSerialReaderException('EIT command timeout({!r})'.format(command))

    def get_connected_serial(self):
        return serial.tools.list_ports.comports()
        
def int32(x):
  if x>0xFFFFFFFF:
    raise OverflowError
  if x>0x7FFFFFFF:
    x=int(0x100000000-x)
    if x<2147483648:
      return -x
    else:
      return -2147483648
  return x

class EIT(EitSerialReaderProtocol):
    """
    A simple serial protocol for communicating with the Bio Impedance Measurement firmware 
    in the ADICUP3029/SDP-K1.

    An event starts with '!'. Events could be errors during measurements or events triggered by 
    the firmware

    A response is the response from the command sent.
    """
    def __init__(self):
        super(EIT, self).__init__()
        self.device_messages = queue.Queue()
        self.readings = queue.Queue()
        self._awaiting_response_for = None
        self.v_sent= False
        self.q_sent= False
        self.mode = 'V'

    def connection_made(self, transport):
        super(EIT,self).connection_made(transport)
        self.transport.serial.reset_input_buffer()
        self.transport.serial.reset_output_buffer()

    def handle_event(self, event):
        """
        Handle events here
        """
        # readings are arranged in [real, imaginary]
        if (event.startswith('!V') and self._awaiting_response_for.startswith('V')):
            line = event[2:]
            boundary_readings = np.array([int32(int(i,16)) for i in line.split(',')])
            count = len(boundary_readings)
            print(boundary_readings)
            self._awaiting_response_for = None
            self.v_sent=False
            self.readings.put(boundary_readings.reshape(int(count/2),2))
        elif (event.startswith('!Q') and self._awaiting_response_for.startswith('Q')):
            line = event[2:]
            if(self.mode=='Z'):
                print(line)
                measurements = np.array([struct.unpack(">f",bytes.fromhex(i)) for i in line.split(',')])
            else:
                measurements = np.array([int32(int(i,16)) for i in line.split(',')])
            count = len(measurements)
            self._awaiting_response_for = None
            self.q_sent=False
            
            self.readings.put(complex(measurements[0],measurements[1]))
        
        elif (event.startswith('!B') and self._awaiting_response_for.startswith('B')):
            line = event[2:]
            supported_electrode_count = np.array([int32(int(i,16)) for i in line.split(',')])
            #self._awaiting_response_for = None
            self.readings.put(supported_electrode_count)
        elif (event.startswith('!C ') and self._awaiting_response_for.startswith('C')):
            line = event[2:]
            self.readings.put(np.array([0,0]))
        elif (event.startswith('!O ') and self._awaiting_response_for.startswith('O')):
            line = event[2:]
            self.readings.put(np.array([0,0]))
        else:
            print(event)
            self.device_messages.put(event)
            

    def send_command_with_response(self,command):
        """
        Sends a command with expected response
        """
        with self.lock:
            self._awaiting_response_for = command
            if((not command.startswith("V")) and (not command.startswith("X")) and (not command.startswith("Q"))):
                print("Command Sent: "+command)
                self.write_line(command)
                
            elif command.startswith("V") and not self.v_sent:
                #print("Command Sent: "+command)
                self.write_line(command)
                self.v_sent=True

            elif command.startswith("Q") and not self.q_sent:
                print("Command Sent: "+command)
                self.write_line(command)
                self.q_sent=True
            
            response=None
            
            if command.startswith("V"):
                try:
                    response = self.readings.get(False)
                except queue.Empty:
                    response=None
                    pass
                    
            else:
                response = self.readings.get()
                self._awaiting_response_for = None
            return response


    def get_boundary_voltage(self):
        """
        Sends a command to serial to start reading
        """
        command = ("V ")
        self.mode='V'
        return self.send_command_with_response(command)

    def set_eit_mode(self, freq=10, electrode_count=8, force_distance=1, sense_distance=1, fixed_ref=False):
        """
        Sends a command to serial to configure hardware
        ---------
        freq: int
            frequency in kHz.
        electrode_count : int
            the number of electrodes in the EIT hardware
        force_distance : int
            distance between the two force electrodes. For adjacent method force_distance == 1.
            for opposite method, force_distance = electrode_count/2
        sense_distance : int
            distance between the two sense electrodes. For adjacent method force_distance == 1.
            for opposite method, force_distance = electrode_count/2
        fixed_ref : boolean
            (Reserved) Fix one sense electrode for every stimulation combination. sense distance will be ignored.
        
        """
        if fixed_ref:
            fref = 1
        else:
            fref = 0
        command = "C " + str(freq) + "," + str(electrode_count) + "," + str(force_distance) + "," + str(sense_distance) + "," + str(fref)
        self.mode='V'
        return self.send_command_with_response(command)

    def get_board_supported_electrode_count(self):
        """
        Sends a command to serial to read the board supported electrode count.
        ---------       
        """
        command = ("B ")
        return self.send_command_with_response(command)

    def stop_eit(self):
        """
        Sends a command to serial to stop the hardware.
        ---------       
        """
        command = ("O ")
        return self.send_command_with_response(command)

    def query(self, freq,f_plus, f_minus, s_plus, s_minus,mode):
        command = ("Q " + str(freq) + "," + str(f_plus) + "," + str(f_minus) + "," + str(s_plus) + ","+ str(s_minus) +","+ str(mode))
        self.mode=mode
        return self.send_command_with_response(command)

class EIT_Interface():
    def __init__(self, port, baudrate, iio=False):
        self._serial = port
        self._baudrate = baudrate
        self._iio = iio
        self._sercom = None
        self._switch_sequence = None
        self.electrode_count = 16

        if iio:
            self._afe = adi.ad5940(uri=f"serial:{port},{baudrate},8n1")
            self._cps = adi.adg2128(uri=f"serial:{port},{baudrate},8n1")
            self._cps.add(0x71)
            self._cps.add(0x70)
        else:
            sercom = serial.Serial(port, baudrate, timeout=300)
            rt = serial.threaded.ReaderThread(sercom, EIT)
            rt.start()
            rt._connection_made.wait()
            self._eit = rt.protocol
            self._sercom = sercom

    def generate_switch_sequence(self):
        seq = 0
        ret = []
        for i in range(self.electrode_count):
            f_plus = i
            f_minus = (i + self.force_distance) % self.electrode_count
            for j in range(self.electrode_count):
                s_plus = j % self.electrode_count
                if s_plus == f_plus or s_plus == f_minus:
                    continue
                s_minus = (s_plus + self.sense_distance) % self.electrode_count
                if s_minus == f_plus or s_minus == f_minus:
                    continue
                ret.append((f_plus, s_plus, s_minus, f_minus))
                seq += 1
        return ret

    def stop(self):
        if not self._iio:
            return self._eit.stop()

    def stop_eit(self):
        if not self._iio:
            return self._eit.stop_eit()

    def get_boundary_voltage(self):
        if self._iio:
            if self._switch_sequence == None:
                self._switch_sequence = self.generate_switch_sequence()
            self._afe.impedance_mode = False
            ret = []
            for seq in self._switch_sequence:
                # reset cross point switch
                self._afe.gpio1_toggle = True

                # set new cross point switch configuration from pregenerated sequence
                self._cps[seq[0]][0] = True
                self._cps[seq[1]][1] = True
                self._cps[seq[2]][2] = True
                self._cps[seq[3]][3] = True

                # read impedance
                s = self._afe.channel["voltage0"].raw
                ret.append([s.real, s.imag])

            return np.array(ret).reshape(len(ret), 2)
        else:
            return self._eit.get_boundary_voltage()

    def set_eit_mode(self, freq, electrode_count, force_distance, sense_distance, fixed_ref):
        if self._iio:
            self._afe.frequency = freq
            self.electrode_count = electrode_count
            self.force_distance = force_distance
            self.sense_distance = sense_distance
            self.fixed_ref = fixed_ref
        else:
            return self._eit.set_eit_mode(freq, electrode_count, force_distance, sense_distance, fixed_ref)

    def get_board_supported_electrode_count(self):
        if self._iio:
            return np.array([8, 16, 32])
        else:
            return self._eit.get_board_supported_electrode_count()

    def query(self, freq, f_plus, f_minus, s_plus, s_minus, mode):
        if self._iio:
            self._afe.gpio1_toggle = True
            self._afe.impedance_mode = (mode == 'Z')

            self._cps[f_plus][0] = True
            self._cps[s_plus][1] = True
            self._cps[s_minus][2] = True
            self._cps[f_minus][3] = True

            return self._afe.channel["voltage0"].raw
        else:
            return self._eit.query(freq, f_plus, f_minus, s_plus, s_minus, mode)
    
    def close(self):
        if not self._iio:
            self._sercom.close()
