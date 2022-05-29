import base64  # Used for encryption
import binascii
import os
from socket import *
import threading
import time
import hashlib

serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

locked = True  # Is true until client enters correct server password
serverName = input("Input server IP to connect to the server: ")


def get_ip():
    hostname = gethostname()
    ip_add = gethostbyname(hostname)
    return ip_add


# Gaining access to server
while locked:
    serverPassword = input("Enter the server password")
    serverPassword = serverPassword.encode("utf-8")  # Using base64 for encryption
    encoded = base64.b64encode(serverPassword)  # Encodes inputted password
    lockStatus = "LOCKED#".encode()  # State is LOCKED
    sendMess = lockStatus + encoded  # Header consists of Command ("LOCKED") and body consists of the message (password)
    clientSocket.sendto(sendMess, (serverName, serverPort))  # Sends header and body to server
    status, clientA = clientSocket.recvfrom(2048)  # Receives message from server to determine password correctness
    if status.decode() == 'Unlocked':  # If server sends "Unlocked", client breaks out loop and continues
        locked = False
    else:
        print("Wrong password")  # Else client must reenter password
client_ip = get_ip()
clientName = input("Input your name: ")
clientSocket.sendto(("JOIN#" + clientName).encode(),
                    (serverName, serverPort))  # Client added to list of users on server
msg, client_address = clientSocket.recvfrom(2048)  # Expects "JOINED" (confirmation of joining)
clientSocket.sendto(("CHECKINDB#" + clientName).encode(), (serverName, serverPort))
msg, client_address = clientSocket.recvfrom(2048)
msg = msg.decode()
if msg == 'NEWUSERPASSWORD' or msg == 'NEWUSER':
    password = input('Please choose a password: ')
    clientSocket.sendto(('NEWUSERPASSWORD#'+clientName + '#' + password).encode(), (serverName, serverPort))
elif msg == 'OLDUSER':
    password_guess = input('Please enter your password: ')
    clientSocket.sendto(('CHECKPASSWORD#' + password_guess).encode(), (serverName, serverPort))
    msg, client_address = clientSocket.recvfrom(2048)
    msg = msg.decode()
    print(msg)
    while msg != 'LOGGEDIN':
        password_guess = input('Please enter your password: ')
        clientSocket.sendto(('CHECKPASSWORD#' + password_guess).encode(), (serverName, serverPort))
        msg, client_address = clientSocket.recvfrom(2048)
        msg = msg.decode()
    
# Thread to always receive messages
def receiver():
    while True:
        message, client_add = clientSocket.recvfrom(2048)
        try:
            decoded = base64.b64decode(message)
            message = decoded.decode()
        except binascii.Error:  # Only occurs when server sends RECEIVED
            pass
        message_parts = message.split("`")
        message = message_parts[0]
        if len(message_parts) == 2:
            message_hash = (hashlib.md5(message.encode())).hexdigest()
            if message_hash == message_parts[1]:
                if message != 'LEAVE':
                    print(message)
                # Condition so that server does not wait for incorrect client to send confirmation message "RECEIVED"
                if message != "SENT":
                    clientSocket.sendto("RECEIVED".encode(), (serverName, serverPort))
            else:
                print("Message was corrupted")
        else:
            if message != 'LEAVE':
                print(message)
            # Condition so that server does not wait for incorrect client to send confirmation message "RECEIVED"
            if message != "SENT":
                clientSocket.sendto("RECEIVED".encode(), (serverName, serverPort))

# Thread to always send messages
def sender():
    while True:
        time.sleep(0.5)  # Sleeps so that client can receive messages before immediately being prompted to send message
        print("To chat with one other user, enter CHAT \nTo chat with a group, enter GROUP")
        print("To broadcast a message, enter BROADCAST \nTo see a list of users online, enter ACTIVE")
        command_input = input('To exit the server and end your client, enter EXIT: ')

        # Add command to see all active users
        # CHAT to send messages to one person
        # Protocol format: Header = Command (CHAT) and IP; Body = Message
        if command_input == 'CHAT':
            friend_ip = input("Enter the username of the person you would like to chat with: ")
            protocol = ("CHAT#" + friend_ip + "#").encode()
            do_communication(command_input, protocol)


        # GROUP to create or join an existing group
        # Protocol format: Header = Command (JOIN_GROUP) ; Body = group name

        elif command_input == 'GROUP':
            command = input("Join an existing group(E) or make a new group(N): ")
            if command == "E":
                group_name = input("Enter the name of your group to join: ")
                protocol = ("JOIN_GROUP#" + group_name).encode()
                clientSocket.sendto(protocol, (serverName, serverPort))
                print("You are now in: " + group_name + "\n\ntype LEAVE to exit")
                protocol = ("GROUP_CHAT#" + group_name + "#").encode()
                do_communication(command_input, protocol)

            else:
                group_name = input("Enter the name of your new group: ")
                group_members = []
                print("Enter the names of the people you want in your group: ")
                print("Type DONE when you are finished")
                member = ""
                while member != "DONE":
                    member = input("")
                    if member=="":
                        print("No input, try again")
                        continue
                    group_members.append(member)

                member_output = ""
                for member in group_members:
                    member_output += member + "#"

                protocol = ("NEW_GROUP#" + group_name + "#" + member_output).encode()
                clientSocket.sendto(protocol, (serverName, serverPort))
                time.sleep(5)
                print("You are now in: " + group_name + "\n\ntype LEAVE to exit")
                command_input = ""
                protocol = ("GROUP_CHAT#" + group_name + "#").encode()
                do_communication(command_input, protocol)

        # BROADCAST to send messages to everyone online
        # Protocol format: Header = Command (CHAT) and ALL (send to all IPs); Body = Message
        elif command_input == 'BROADCAST':
            protocol = "CHAT#All#".encode()
            do_communication(command_input, protocol)
        elif command_input == 'ACTIVE':
            clientSocket.sendto(command_input.encode(), (serverName, serverPort))
        elif command_input == 'EXIT':
            clientSocket.sendto((command_input + "#" + clientName).encode(), (serverName, serverPort))
            os._exit(0)
        else:
            # Displays if input is not a valid format/command
            print("Wrong input format")

def do_communication(command_input, protocol):
    while command_input != "LEAVE":
        command_input = input("")
        if command_input != "LEAVE":
            encrypted_message = clientName + ": " + command_input
            encrypt_hash = hashlib.md5(encrypted_message.encode()).hexdigest()
            encoded_encrypt = base64.b64encode((encrypted_message + "`" + encrypt_hash).encode("utf-8"))
            clientSocket.sendto((protocol + encoded_encrypt),
                                (serverName, serverPort))

thread1 = threading.Thread(target=receiver)
thread2 = threading.Thread(target=sender)

thread2.start()
thread1.start()