"""
Parameter-Adaptive Reliable UDP-based
Protocol

RULE, Camille P. 
201909414
CS 145 Project 1
"""

"""
import socket module to send message over network
import sys module to get parameters from command line
import hashlibe for computing for checksum
import time module to track timeouts 
import math ceil function for payload division
"""
import socket
import sys
import hashlib
import time
from math import ceil

"""
Given function to compute for hecksum in lab specifications
"""
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

#Set server IP addr and port to a tuple
UDP_IP_PORT = (UDP_IP_ADDRESS, UDP_PORT_NO)

#Create socket for receiving packets from server 
clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSock.bind(('', 6745)) #bind at port 6745 (designated port for student)
clientSock.settimeout(15) #set timeout to default 15 seconds

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
LEVEL 2 AND 3 IMPLEMENTATION
"""
#Open payload file and parse contents
f = open(fn,"rb")
dp = f.read()
dp = dp.decode()

"""
Set appropriate flags
Z variable is the Z flag which denotes last packet in transmission, initially 0
seq variable keeps track of the sequence number of packet, initially 0
charsent denotes how many characters of the payload has been sent thus far, initially 0
"""
Z = seq = charsent = 0
dp_size = len(dp) #get length of payload for reference

"""
`accepted` flag if server accepts transmission of a packet, initially 0
(server has not accepted any packet yet)

`increment` flag to check if client can continue incrementing payload size being sent, initially 0
`maxed` flag to check if no more incrementation can be done - payload size has been exceeded, initially 0

empty string `sent` to keep track of all sent data from payload
(will be useful to check if correct packets are sent)
"""
accepted = 0
increment = 0
maxed = 0
sent = ''

"""
set a fraction of payload size as best guess packet size
value was taken by trial and error, started from taking 1/2 of payload size -> 1/4 -> 1/8 -> 1/32
"""
packet_size = int(ceil(0.03125 * dp_size)) 

print(f"Length: {dp_size}")

#start timer for timeout (to check if packets were not ACKed)
startTime = time.time()
#start sending
while charsent < dp_size:
    #last packet rules
    #if packetsize and current size of data sent exceeds remaining payload size
    if (charsent + packet_size >= dp_size):
        #to get remaining data left, subtract payload size from sent characters so far 
        rem = dp_size - charsent
        #if 0 is the answer, then there are no more data left to send
        if rem == 0:
            #Tell server this is the last packet, set Z to 1
            Z = 1
            
            """
            Create payload using specifications:
            ID = 44919a94 (given as project credential)
            SN = sequence number padded with zeroes using .zfill
            TXN = transaction id taken from server 
            PAYLOAD = take data from payload starting from the last sent character
            to the length of the data packet size
            """
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:dp_size]}")
        
        #remaining data may not be equal to 0 but is still less than packet size
        elif rem > 0 and rem < packet_size:
            #this is still the last packet to be sent, set Z to 1
            Z = 1
            #take payload to be from the last character sent up to the remaining data 
            payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+rem]}")
    #if packet isn't last, packet is for transmission
    #take payload to be from last character sent up to the size of packet
    else:
        payload = (f"{intent}SN{str(seq).zfill(7)}TXN{trans_id}LAST{Z}{dp[charsent:charsent+packet_size]}")
    
    #print payload for checking/debugging
    #print("Current payload", payload)

    #use provided checksum function to generate checksum (client side)
    checksum = compute_checksum(payload)
    
    #send payload to client
    clientSock.sendto(payload.encode(), UDP_IP_PORT)
    print("Packet sending...")

    """
    for the implementation of sending packets, we use a try-except block to try getting 
    ACK packets from the server EXCEPT if the packet we sent was not ACKED which will lead to the 
    time out of socket
    """
    try: 
        #try getting ACK response from server
        response, addr = clientSock.recvfrom(1024) 
        #if response was received, server was able to receive packet, set `accepted` flag to 1
        accepted = 1
        #increment `sent` variable to hold current sent data (for checking)
        sent += dp[charsent:charsent+packet_size]

        print("ACK received...")

        #decode response from server to get checksum; checksum at index 23 onwards of ACK packet
        #according to project specs
        rescheck = response.decode()
        rescheck = rescheck[23:]

        #if checksums are not equal, break transmission 
        if rescheck != checksum:
            print(f"Server checksum{rescheck}")
            print(f"Client checksum{checksum}")
            print("Checksum error")
            break 

        #increment the last sent character to be packet size 
        charsent += packet_size 
        #increment sequence number of packet by 1
        seq += 1

        #increment flag used to check if payload can still be increased
        #if this flag is 0, incrementation can still be done
        if increment == 0:
            """
            increment packet size by subracting current packet size from total 
            data packet size

            get only 2 percent of size to add 
            this value was gotten from trial and error. implementation first tested by
            getting 50% -> 25% -> 10% -> 5% -> 2%
            """
            packet_size += int(ceil(0.02*(dp_size-packet_size)))
        
        #accepted flags and increments flags will be set to 1 if packet was:
        # 1) accepted by server
        # 2) but can no longer be incrremented
        #this means that payload size has been maxed out and we set `maxed` flag to 1
        if accepted == 1 and increment == 1:
            maxed = 1

        print(f"Current packet size {packet_size}, remaining {dp_size-charsent}")
        """
        if timeout is reached, packet has not been ACKed by server. we have the following scenarios:
            1) Initial packet size not accepted by server
            2) Previous transmissions accepted but this one failed because we incremented too high
            3) We just need to resend packet
        """
    except socket.timeout:
        print("Server NACKed")
        print(f"Packet not accepted because of payload size: {packet_size}")

        if maxed == 1:
            continue
        
        #if accepted flag has not been set to 1, inital packet sent was not accepted, adjust payload size
        #values same as used during incrementation
        if accepted == 0:
            packet_size -= int(ceil(0.02*(dp_size-packet_size)))
        
        #if accepted flag has been set to 1, transmission has already been accepted by server
        #but socket has timed out either because of:
        #1) payload size
        #2) being in the queue
        #in this case, we want to decrease payload size still and send again 
        elif accepted == 1:
            #set increment flag to 1 to signify that we can't increment payload size anymore
            increment = 1
            packet_size -= int(ceil(0.02*(dp_size-packet_size)))
            
    #checker if 120 second time allotment has passes
    if time.time() - startTime > 120:
        break

print("Packet transmission finished.")
print(f"Sent data equal to payload? {sent == dp}")
