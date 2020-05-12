
import socket
import struct


class Agilent_B2912A:
    def __init__(self, host='ief-lab-b2912a-2.ee.ethz.ch'):
        self.host = host
        
    def __del__(self):
        self.socket.close()
        print('Connection at ',  self.host, 'closed and object deleted.')

        
    def send_string(self, string):
        """
        Just a function to avoid to convert to utf-8 all the times, and to set the termination character "\n".
        """
        self.socket.sendall(string.encode('utf-8')+b'\n')
        
    def open(self):
        self.socket = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        port = 5025  # 5025 standard Keysignt SCPI socket port #1234 is the default Prologix port
        self.socket.connect((self.host,  port))
        self.socket.settimeout(1000)
        print('Connected to ',  self.host)   
        self.socket.sendall(b'*RST\n')
        self.socket.sendall(b'*IDN?\n')
        msg = self.socket.recv(1024)
        print('Device IDN: ', msg)

    def enable(self, enable_output = False, channel = 1):
        if enable_output:
            self.send_string(':OUTP{} ON'.format(channel))
        else:
            self.send_string(':OUTP{} OFF'.format(channel))

    def set_current(self, current = 0, channel = 1): # current in amperes, channel 1 or 2.
        self.send_string(':SOUR{}:FUNC:MODE CURR'.format(channel))   # This is equivalent to ':SOUR'+str(channel)':FUNC:MODE CURR'
        self.send_string(':SOUR{}:VOLT:MODE FIX'.format(channel))
        self.send_string(':SOUR{}:VOLT {}'.format(channel, current))


    def set_compliance_voltage(self, voltage = 0, channel = 1):
        self.send_string(':SENS{}:VOLT:PROT {}'.format(channel, voltage))


    def set_voltage(self, voltage = 0, channel = 1): # voltage in volt, channel 1 or 2.
        self.send_string(':SOUR{}:FUNC:MODE VOLT'.format(channel))
        self.send_string(':SOUR{}:VOLT:MODE FIX'.format(channel))
        self.send_string(':SOUR{}:VOLT {}'.format(channel, voltage))        


    def set_compliance_current(self, current = 0, channel = 1):
        self.send_string(':SENS{}:CURR:PROT {}'.format(channel, current))


    def spot_measurement(self, channel):
        """
        Executes a spot measurement.
        Returns a 3-element list containing [measured Voltage, measured Current, source setting (either [V] or [A])]
        """
        self.send_string(':FORM:ELEM:SENS VOLT,CURR,SOUR')
        self.send_string(':MEAS? (@{})'.format(channel))
        block = self.socket.recv(1024)   # ieee binary data block. 
        # Decoding the binary string, for example b'+1.934080E-03\n'--> '+1.934080E-03'
        decoded_data_string = block.decode('ascii')
        return [float(number_str) for number_str in decoded_data_string.split(',')]



# "Fill this part" section
# ========================
# --> TO DO.
    def stop_output(self,channel):  #stops the soure output
        self.send_string(":OUTP OFF".format(channel))


# Below: advanced functionality for illustration
#===============================================
        
    def set_current_measurement_sweep(self, constant_voltage = 1, current_limit = 0.0001,  measurement_points = 100,  averaging_time_us = 1000):
        # Setting the voltage source
        self.send_string(':SOUR:FUNC:MODE VOLT')
        self.send_string(':SOUR:VOLT:MODE FIX')  # this sets it to fixed voltage mode, as opposed to sweep or pulse mode
        self.send_string(':SOUR:VOLT '+str(constant_voltage))  # Set voltage outputted when triggered. Pg. 19 prog. manual.        
        # Set fixed-range current measurement
        self.send_string(':SENS:FUNC "CURR"')  # ! Careful: using double " around ""CURR"" gives ERR (but is used in the manual)
        self.send_string(':SENS:CURR:RANG:AUTO OFF')
        self.send_string(':SENS:CURR:RANG '+str(current_limit))  # set current range in Ampere
        #self.send_string(':SENS:CURR:APER 10')  # aperture time in seconds. Corresponds to "long",..."short" on display under "Measurement speed"
        self.send_string(':SENS:CURR:PROT '+str(current_limit))  # set current protection (compliance)
        self.send_string(':SENS:REM OFF')  # OFF sets 2-wire rather than 4-wire
        # Adjust trigger timing parameters 
        self.send_string(':TRIG:ACQ:DEL 0')  # set aquire (measurement) delay time (measured from trigger)
        # Generate N triggers in certain time period
        self.send_string(':TRIG:SOUR TIM')
        self.send_string(':TRIG:TIM '+str(averaging_time_us*1E-6))
        self.send_string(':TRIG:COUN '+str(measurement_points))
        
    def set_list_sweep(self, voltage_list = '0.1,0.2,0.3, 0.4', current_limit = 0.0001,  measurement_points = 100,  averaging_time_us = 1000):
        self.send_string(':SOUR:VOLT:MODE LIST')
        self.send_string(':SOUR:LIST:VOLT '+voltage_list)
        # setint current limit
        self.send_string(':SENS:CURR:PROT '+str(current_limit))  # set current protection (compliance)
        # setting the trigger
        self.send_string(':TRIG:SOUR TIM')
        self.send_string(':TRIG:TIM '+str(averaging_time_us*1E-6))
        self.send_string(':TRIG:COUN '+str(measurement_points))
        self.send_string(':TRIG:TRAN:DEL 0')  # delay from trigger

    def trigger_start(self):
        # start the measurements above with timed triggers
        self.send_string(':INIT (@1)')

    def receive_data(self):
        # Retrieve measurement results. The B2012A sends data in plain text and it terminates it with "\n"
        keep_receiving = True	# initialization
        block = b''  # initializing as empty byte string
        self.socket.sendall(b':FETCH:ARR:CURR? (@1)\n')
        counter=0
        while keep_receiving:
            counter=counter+1
            block = block+self.socket.recv(1024)   # ieee binary data block.    
            if block[len(block)-1:len(block)]==b'\n': # keep receiving untill the termination string is found. BAD IDEA: it can appear as data!
                keep_receiving = False  
        # Decoding the binary string, for example b'+1.934080E-03\n'--> '+1.934080E-03'
        decoded_data_string = block.decode('ascii')  
        decoded_data = [float(i) for i in decoded_data_string.split(',')] # first splits the single long string into multple strings, then converts to float
        #print(decoded_data)
        return decoded_data
        

