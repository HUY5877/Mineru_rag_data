import socket
import numpy as np
s = socket.socket()
s.connect(('127.0.0.1', 7000))

s.sendall(b'set SPK threshold channel 1 2 value 60 30')   # 或者尝试 b'stop ACQ;\n'
response = s.recv(1024)
print('Response:', response.decode())
s.sendall(b'start ACQ')   # 或者尝试 b'stop ACQ;\n'
response = s.recv(1024)
print('Response:', response.decode())

s.sendall(b'search VOL channel 1 2')   # 或者尝试 b'stop ACQ;\n'
response = s.recv(1024)
arr = np.frombuffer(response, dtype='<u2')  # '<u2' 表示小端 uint16
print(arr)


s.close()