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
for comm in range(len(comms)):
    if comms[comm] == '-f': #filename
        fn = comms[comm+1]
    elif comms[comm] == '-a': #IP address of server
        UDP_IP_ADDRESS = comms[comm+1]
    elif comms[comm] == '-s': #Server port
        UDP_PORT_NO = int(comms[comm+1]) 
    elif comms[comm] == '-c': #Client port
        CLIENT_PORT = int(comms[comm+1])
    elif comms[comm] == '-i': #Student ID
        ID = comms[comm+1]

UDP_IP_PORT = (UDP_IP_ADDRESS, UDP_PORT_NO)

#Create socket for receiving packets from server 
clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSock.bind(('', 6745))
clientSock.settimeout(15)

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
print(f"Trans ID: {trans_id}")


"""
LEVEL 2 IMPLEMENTATION:
"""
f = open(fn,"rb")
dp = f.read()
dp = dp.decode()

Z = seq = charsent = 0
dp_size = len(dp)
accepted = 0
increment = 0
maxed = 0
sent = ''
packet_size = int(ceil(0.03125 * dp_size)) #set 1/4 of size as best guess packet size

print(f"Length: {dp_size}")

startTime = time.time()
#start sending
while charsent < dp_size:
    #last packet
    if (charsent + packet_size >= dp_size):
        rem = dp_size - charsent
        if rem == 0:
            Z = 1
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:dp_size]}")
        elif rem > 0 and rem < packet_size:
            Z = 1
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+rem]}")
    else:
        payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+packet_size]}")
    print("Current payload", payload)
    checksum = compute_checksum(payload)
    
    clientSock.sendto(payload.encode(), UDP_IP_PORT)
    print("Packet sending...")
    try:
        response, addr = clientSock.recvfrom(1024) 
        accepted = 1
        sent += dp[charsent:charsent+packet_size] # concatenate sent packets
        print("ACK received...")
        rescheck = response.decode()
        rescheck = rescheck[23:]

        if rescheck != checksum:
            print(rescheck)
            print(checksum)
            print("Checksum error")
            break 

        charsent += packet_size 
        seq += 1
        if increment == 0:
            packet_size += int(ceil(0.02*(dp_size-packet_size)))
        if accepted == 1 and increment == 1:
            maxed = 1

        print(f"Current packet size {packet_size}, rem{dp_size-charsent}")

    except socket.timeout:
        print("Server NACKed")
        print(f"Size not accepted: {packet_size}")
        prev = packet_size
        if maxed == 1:
            continue
        if accepted == 0:
            packet_size -= int(ceil(0.02*(dp_size-packet_size)))
        elif accepted == 1:
            increment = 1
            packet_size -= int(ceil(0.02*(dp_size-packet_size)))
        
    if time.time() - startTime > 120:
        break


print(f"Sent data equal to payload? {sent == dp}")
