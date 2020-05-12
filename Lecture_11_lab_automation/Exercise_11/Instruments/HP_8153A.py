
import socket
import struct


class HP_8153A:
    # allowed averaging times: 20, 50, 100, 200, 500ms, 1,2,5,10,20,30s,... see manual for more.
    def __init__(self, host='ief-lab-prologix-1b23.ee.ethz.ch', measurement_points = 100,  averaging_time_ms = 20,  gpib_address = 2  ):   # old: 'ief-lab-hp8153a-1.ee.ethz.ch'
        self.host = host
        self.measurement_points=measurement_points
        self.averaging_time_ms=averaging_time_ms
        self.gpib_address = gpib_address
        
#    def __del__(self):
#        self.socket.close()
#        print('Connection at ',  self.url, 'closed and object deleted.')


    # just a function to avoid to convert to utf-8 all the times and to set the termination.
    def send_string(self, string):
        self.socket.sendall(string.encode('utf-8')+b'\n')
        
    def open(self):
        self.socket = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        port = 1234  # the default Prologix port
        self.socket.connect((self.host,  port))
        self.socket.settimeout(1000)
        print('Connected to ',  self.host)    

        # All commands beginning with "++" are read by the Proligix    
        #self.socket.sendall(b'++mode 1\n')	# equiavalent to below, but with without using "send_string"
        self.send_string('++mode 1')	# set the Prologix to device mode (0) or controller mode (1)
        self.send_string('++auto 1')	# set the intrument to listen (0) or to talk (1)
        self.send_string('++addr '+str(self.gpib_address))	# set the GPIB address
        self.send_string('++read_tmo_ms 3000') # set the read timeout in ms
        self.send_string('++ver')	# ask for version
        msg = self.socket.recv(1024)
        print('Prologix version: ', msg)
        self.socket.sendall(b'*RST\n')
        self.socket.sendall(b'*IDN?\n')
        msg = self.socket.recv(1024)
        print('Device IDN: ', msg)
        self.send_string(':SENS:POW:RANG -30DBM')	# set power range to 0 dBm  (allowed: from -110dBm to 30dBm steps of 10)
        self.send_string(':SENS:POW:UNIT DBM')	# setting units to dBm
        self.send_string('SENS:POW:ATIME '+str(self.averaging_time_ms)+'MS')
        self.socket.sendall(b':SENS:POW:ATIME?\n')	# check the settings
        msg = self.socket.recv(1024) 
        print('Averaging time: ', msg, 'dBm')


#    def start_logging(self):
#        self.socket.sendall(b':SENS1:FUNC:STAT LOGG,STAR\n') # trigger one sequence of measurements



    def read_power(self):
        self.send_string('READ:POW?')
        msg = self.socket.recv(1024) 
        print('Power: ', msg, 'ms')



'''        
    def receive_data(self):
        # Receiving all data:
        keep_receiving = True	# initialization
        block = b''  # initializing as empty byte string
        self.socket.sendall(b':SENS1:FUNC:RES?\n')	# ask to read out the RESults
        while keep_receiving:
            block = block+self.socket.recv(1024)   # ieee binary data block. # Obs: one call is not enought to get 1000 datapoints out!    
            #print('******: ',block)
            #if not(block.find(b'\n\x0b')==-1): # keep receiving untill the termination string is found.
            if block[len(block)-2:len(block)]==b'\n\x0b': # keep receiving untill the termination string is found.
                #print('Found x0b:', block.find(b'\n\x0b') )
                keep_receiving = False  
        #print('Data received.')
        # DECODING IEEE binary data block    
        begin = block.find(b'#')  # should be zero
        #end=block.find(b'\n\x0b')  # the block ends with this
        end=len(block)-2    # the block ends with b'\n\x0b'
        header_length = int(block[begin+1:begin+2])
        offset = begin + 2 + header_length
        data_length = int(block[begin+2:offset])  
       #print('data_length',  int(data_length/4))
        format = str(int(data_length/4))+'f'
        block_cropped = block[offset:end]
        decoded_data = list(struct.unpack(format, block_cropped))
        #print(decoded_data)
        return decoded_data
        
'''
