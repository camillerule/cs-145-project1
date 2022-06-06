import socket
from struct import pack
import sys
import hashlib
import time
from math import ceil

def compute_checksum(packet):
    return hashlib.md5(packet.encode('utf-8')).hexdigest()

#Initialize parameters from terminal command
#-f path/to/file.txt -a SERVER IP ADDR -s SERVER PORT -c STUDENT PORT -i STUDENT ID
comms = sys.argv[1:]
fn, UDP_IP_ADDRESS, UDP_PORT_NO, CLIENT_PORT, ID = comms[1], comms[3], comms[5], comms[7], comms[9]
UDP_IP_PORT = (UDP_IP_ADDRESS, UDP_PORT_NO)

#Create socket for receiving packets from server 
clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSock.bind(('', 6745))
clientSock.settimeout(100)

"""
LEVEL 1 IMPLEMENTATION:
- append "ID" to student ID 
- encode intent message and send to server using server IP and port 
- server sends transaction ID back
- decode and store in trans_id variable
"""

intent = "ID"+ID
clientSock.sendto(intent.encode(), UDP_IP_PORT)

trans_id, addr = clientSock.recvfrom(1024)
trans_id = trans_id.decode()


"""
LEVEL 2 IMPLEMENTATION:
"""
f = open(fn,"rb")
dp = f.read()
dp = dp.decode()

Z = seq = charsent = 0
dp_size = len(dp)
accepted = 0
packet_size = int(ceil(0.25 * dp_size)) #set 1/4 of size as best guess packet size

print(f"Length: {dp_size}")

#start sending
while charsent < dp_size:
    #last packet
    if (charsent + packet_size >= dp_size):
        rem = dp - (charsent + packet_size)
        if rem == 0:
            Z = 1
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:dp_size]}")
        elif rem > 0:
            packet_size = rem
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+packet_size]}")
    else:
        payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+packet_size]}")
    checksum = compute_checksum(payload)
    sentTime = time.time()
    clientSock.sendto(payload.encode(), UDP_IP_PORT)
    try:
        response, addr = clientSock.recvfrom(1024) 
        accepted = 1
        rescheck = response.decode()
        rescheck = rescheck[23:]

        if rescheck != checksum:
            print("Checksum error")
            break 

        charsent += packet_size 
        seq += 1
        packet_size += int(ceil(.25*(dp_size-packet_size)))

    except socket.timeout:
        print("Server NACKed")
        packet_size -= int(ceil(.25*(packet_size)))

