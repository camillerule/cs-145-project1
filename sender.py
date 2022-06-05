import socket

ID = "ID44919a94"
UDP_IP_ADDRESS = "10.0.1.175"
UDP_PORT_NO = 9000

Message = ID.encode()

clientSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
clientSock.sendto(Message, (UDP_IP_ADDRESS,UDP_PORT_NO))

trans_id = clientSock.recvfrom(4)
trans_id = transid.decode()
print(trans_id)