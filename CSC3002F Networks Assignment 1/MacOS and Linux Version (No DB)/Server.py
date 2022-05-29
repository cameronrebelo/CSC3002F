import base64  # Used for encryption
from socket import *

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('0.0.0.0', serverPort))  # 0.0.0.0 for all ips on server hosting machine
serverPassword = 'password'  # Password to use server
print("The server ready to receive")

current_ips = []  # Stores ip address, port number and client name for all active users
all_ips = []  # Same as above but for all users that have accessed the server (clears when server is closed)
groups = []  # Stores group names, members and group id
g = False


def chat():
    print("CHAT")
    friend_name = protocol[1]
    # Either all or specific ips
    if friend_name == 'All':
        broadcast()
    else:

        chat_one(friend_name)


def chat_one(friend_name):
    friend_list = friend_name.split(";")  # Split ips if there are more than 1 into a list
    # Loop through all ips in list of specified ips
    for friend in friend_list:
        index_friend = 0
        found = False
        friend_name = ""

        # Find specific friend in current ips list
        for ip in range(len(current_ips)):
            if friend == current_ips[ip][1]:
                index_friend = ip
                found = True
                friend_ip = current_ips[ip][0][0]
                break
        if found:
            message_to_send = protocol[2]
            if current_ips[index_friend][0] != clientAddress:  # If client is not sending message to themselves
                # print("SENT")
                serverSocket.sendto((base64.b64encode("SERVER: SENT".encode("utf-8"))), clientAddress)
                # Send 'SENT' to original client for confirmation
            friend_ = current_ips[index_friend][0]
            print("Sending message to:", friend_)
            serverSocket.sendto(message_to_send.encode(), friend_)
            # Send message to selected ip
            status, client_add = serverSocket.recvfrom(2048)  # Selected ip sends message back to server (confirmation)
            mod_status = status.decode()
            # If selected ip received message, tell original client
            if mod_status == 'RECEIVED':
                if current_ips[index_friend][0] != clientAddress:
                    serverSocket.sendto((base64.b64encode(("SERVER: " + friend_name + " " + mod_status)
                                                          .encode("utf-8"))), clientAddress)
            # Or tell original client that sending message did not work
            else:
                serverSocket.sendto((base64.b64encode("SERVER: Message lost. Please send again.".encode("utf-8"))),
                                    clientAddress)
        else:
            serverSocket.sendto((base64.b64encode("SERVER: Client DOESN'T exist".encode("utf-8"))), clientAddress)


# Sends to specific ip(s)
def group_specific(friend_ips, group_mode):
    # friend_list = friend_ip.split(";")  # Split ips if there are more than 1 into a list
    # Loop through all ips in list of specified ips
    for friend in friend_ips:
        index_friend = 0
        found = False
        friend_name = ""

        # Find specific friend in current ips list
        for ip in range(len(current_ips)):
            if friend[0][0] == current_ips[ip][0][0]:
                index_friend = ip
                found = True
                friend_name = current_ips[ip][1]
                break
        if found:
            message_to_send = protocol[2]
            if current_ips[index_friend][0] != clientAddress:  # If client is not sending message to themselves
                serverSocket.sendto((base64.b64encode("SERVER: SENT".encode("utf-8"))), clientAddress)
                # Send 'SENT' to original client for confirmation
            friend_ = current_ips[index_friend][0]
            print("Sending message to:", friend_)
            if group_mode:
                decoded = base64.b64decode(message_to_send)
                t = decoded.decode()
                message_to_send = base64.b64encode(
                    ("MESSAGE FROM " + str(fetch_user(clientAddress)[1]) + " IN " + protocol[1] + ":\n" + t).encode(
                        "utf-8"))
                message_to_send = base64.b64encode(t.encode("utf-8"))
                # g = False
            # if group_mode:
            serverSocket.sendto(message_to_send, friend_)
            # else:
            # serverSocket.sendto(message_to_send, friend_)

            # Send message to selected ip
            status, client_add = serverSocket.recvfrom(2048)  # Selected ip sends message back to server (confirmation)
            mod_status = status.decode()
            # If selected ip received message, tell original client
            if mod_status == 'RECEIVED':
                if current_ips[index_friend][0] != clientAddress:
                    serverSocket.sendto((base64.b64encode(("SERVER: " + friend_name + " " + mod_status)
                                                          .encode("utf-8"))), clientAddress)
            # Or tell original client that sending message did not work
            else:
                serverSocket.sendto((base64.b64encode("SERVER: Message lost. Please send again.".encode("utf-8"))),
                                    clientAddress)
        else:
            serverSocket.sendto((base64.b64encode("SERVER: Client DOESN'T exist".encode("utf-8"))), clientAddress)


# Sends to every active user
def broadcast():
    for friend in current_ips:  # Loop through all ips
        message_to_send = protocol[2]
        if friend[0][0] != clientAddress[0]:  # If ip is not original client
            serverSocket.sendto((base64.b64encode("SERVER: SENT".encode("utf-8"))), clientAddress)
            # Tell original client that the message was sent
            serverSocket.sendto((message_to_send.encode()), friend[0])
            status, client_add = serverSocket.recvfrom(2048)
            mod_status = status.decode()
            # Tell original client who received message
            serverSocket.sendto((base64.b64encode(("SERVER: " + friend[1] + " " + mod_status).encode("utf-8"))),
                                clientAddress)


def setup_group_chat(existing):
    if existing:
        for group in groups:
            if group == protocol[1]:
                serverSocket.sendto("Group chat exists".encode(), clientAddress)
                break
    elif not existing:
        non_member = ""
        group_name = protocol[1]
        group_members = [fetch_user(clientAddress)]
        # found = False
        for desired_member in protocol[2:-2]:
            if user_exists(desired_member):
                group_members.append(fetch_user(desired_member))
            elif not user_exists(desired_member):
                non_member += desired_member + "\n"

        if non_member != "":
            print("The following member(s) were not found: " + non_member)
            serverSocket.sendto(
                (base64.b64encode(str("The following member(s) were not found: " + non_member).encode("utf-8"))),
                clientAddress)
        groups.append((group_name, group_members))
        members = "".join(str(e) for e in group_members)
        serverSocket.sendto((base64.b64encode(
            ("Group: " + group_name + " was successfully added with members: " + members).encode("utf-8"))),
                            clientAddress)


def fetch_user(query):
    for search in all_ips:
        if query == search[1] or query == search[0]:
            return search


def user_exists(username):
    flag = False
    for search in all_ips:
        if username == search[1]:
            flag = True
    return flag


while True:
    message, clientAddress = serverSocket.recvfrom(2048)  # Receives message and info about client sending

    already_joined = False
    g = False

    # print(message)

    # Checks to see if client has already been added to server records
    for i in range(len(current_ips)):
        if current_ips[i][0][0] == clientAddress[0]:  # Checks ip addresses
            already_joined = False

    modifiedMessage = message.decode()
    protocol = modifiedMessage.split('#')  # Splits message from server into separate components

    # If client sends password to access server, password is checked here
    if protocol[0] == "LOCKED":
        decoded = base64.b64decode(protocol[1])  # Decodes encrypted password from base64 format
        double_decoded = decoded.decode()  # Decodes password into a string
        if double_decoded == serverPassword:
            serverSocket.sendto("Unlocked".encode(), clientAddress)  # If password is correct, send "Unlocked" to allow
        else:
            serverSocket.sendto("Locked".encode(), clientAddress)  # Do not allow client access

    command = protocol[0]  # Gets command: JOIN, CHAT, EXIT

    if command == 'CHAT':
        chat()

    if command == 'ACTIVE':
        serverSocket.sendto((base64.b64encode(str(current_ips).encode("utf-8"))), clientAddress)

    if command == 'JOIN':
        # print(command)
        name = protocol[1]
        # print(name)
        if not already_joined:
            temp = clientAddress, name
            all_ips.append(temp)  # Add name and clientAddress to server records
            current_ips.append(temp)
        serverSocket.sendto("JOINED".encode(), clientAddress)

    if command == 'JOIN_GROUP':
        setup_group_chat(True)

    if command == 'NEW_GROUP':
        setup_group_chat(False)

    if command == 'GROUP_CHAT':
        temp = []
        g = True
        for group in groups:
            if group[0] == protocol[1]:
                for member in group[1]:
                    temp.append(member)
        # msg = ("From " + clientAddress[0]+" in "+protocol[1])
        # serverSocket.sendto(("From "+clientAddress+" in "+protocol[1]).encode(), clientAddress)
        # serverSocket.sendto((base64.b64encode(str(msg).encode("utf-8"))), clientAddress)
        group_specific(temp, True)

    if command == 'EXIT':
        name = protocol[1]
        temp = clientAddress, name
        current_ips.remove(temp)  # Removes IP from current list if they end their connection to the server

    print("Current:")
    print(current_ips)
    print("All:")
    print(all_ips)
    print("Groups:")
    print(groups)
