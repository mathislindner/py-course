
import socket
import struct


class Keysight_N7744A:
    def __init__(self, host='ief-lab-n7744a-2.ee.ethz.ch', measurement_points = 100,  averaging_time_us = 1000,  channel = 1,  power_range_dBm = 0  ):
        self.host = host
        self.measurement_points=measurement_points
        self.averaging_time_us=averaging_time_us
        self.channel = channel
        self.power_range_dBm = power_range_dBm

        
    def __del__(self):
        self.socket.close()
        print('Connection at ',  self.host, 'closed and object deleted.')

        
    # just a function to avoid to convert to utf-8 all the times and to set the termination.
    def send_string(self, string):
        self.socket.sendall(string.encode('utf-8')+b'\n')
        
    
    def logging_finished(self):        
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':FUNC:RES:INDex?\n')  # Operation Complete query
        msg = self.socket.recv(1024)  # returns  b'+0\n' when busy and b'+1\n' when finished 
        if msg==b'+1\n':
            return True
        else:
            return False

            
    def reset_and_ID(self):
        self.socket.sendall(b'*RST\n')
        self.socket.sendall(b'*IDN?\n')
        msg = self.socket.recv(1024)
        print('Device IDN: ', msg)
               
        
    def open(self):
        self.socket = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        port = 5025  # 5025 standard Keysignt SCPI socket port #1234 is the default Prologix port
        self.socket.connect((self.host,  port))
        self.socket.settimeout(1000)
        print('Connected to ',  self.host)    


        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':POW:RANG '+str(int(self.power_range_dBm)).encode('utf-8')+b'DBM\n')	# set power range
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':POW:RANG?\n')	# set power range        
        msg = self.socket.recv(1024) 
        print('Range settings: ', msg)
        #self.socket.sendall(b':SENS1:FUNC:PAR:LOGG 1000,1ms\n')  # set the number of measurement POINTS and averaging time.
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':FUNC:PAR:LOGG '+str(int(self.measurement_points)).encode('utf-8')+b','+str(int(self.averaging_time_us)).encode('utf-8')+b'us\n')  # set the number of measurement POINTS and averaging time.
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':FUNC:PAR:LOGG?\n')	# check the settings
        msg = self.socket.recv(1024) 
        print('LOGG settings (number of points, averaging time): ', msg)


    def start_logging(self):
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':FUNC:STAT LOGG,STAR\n') # trigger one sequence of measurements

        
    def receive_data(self):
        # Receiving all data:
        keep_receiving = True	# initialization
        block = b''  # initializing as empty byte string
        self.socket.sendall(b':SENS'+str(int(self.channel)).encode('utf-8')+b':FUNC:RES?\n')	# ask to read out the RESults
        counter=0
        while keep_receiving:
            counter=counter+1
            block = block+self.socket.recv(1024)   # ieee binary data block. # Obs: one call is not enought to get 1000 datapoints out!    
            begin = 0 # block.find(b'#')  # should be zero
            end=len(block)-1    # the block ends with b'\n\x0b'
            header_length = int(block[begin+1:begin+2])
            offset = begin + 2 + header_length
            data_length = int(block[begin+2:offset]) 
            if len(block)-3-header_length==data_length:
                keep_receiving = False  
        format = str(int(data_length/4))+'f'
        block_cropped = block[offset:end]
        decoded_data = list(struct.unpack(format, block_cropped))
        return decoded_data
        

