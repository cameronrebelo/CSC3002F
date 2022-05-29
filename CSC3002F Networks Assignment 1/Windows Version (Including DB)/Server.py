import base64  # Used for encryption
from socket import *
import pyodbc, os

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('0.0.0.0', serverPort))  # 0.0.0.0 for all ips on server hosting machine
serverPassword = 'password'  # Password to use server
print("The server ready to receive")

current_ips = []  # Stores ip address, port number and client name for all active users
all_ips = []  # Same as above but for all users that have accessed the server (clears when server is closed)
groups = []  # Stores members group id, group names
g = False

#establishes connection to the msaccess database, 'ChatDatabase.accdb'
try:
    path = str(os.path.dirname(__file__))
    path += '\db.accdb'
    #uses a relative path to connect to the database
    con_string = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + path +';\''
    
    conn = pyodbc.connect(con_string)
    cursor = conn.cursor()
except pyodbc.Error as e:
    print('error in db connection')

def check_user_name_in_db(username):
    cursor.execute('SELECT userName from userInfo')
    existing_users = [item[0] for item in cursor.fetchall()]
    print(existing_users + 'HERE')
    found = False
    for u in existing_users:
        if u == username:
            found = True 
    return found

def check_ip_in_db (ip):
    cursor.execute('SELECT [IPAddress] from userInfo')
    existing_ips = [item[0] for item in cursor.fetchall()]
    found = False
    for i in existing_ips:
        if i == ip:
            found = True 
    return found

def chat():
    print("CHAT")
    friend_ip = protocol[1]
    # Either all or specific ips
    if friend_ip == 'All':
        broadcast()
    else:

        chat_one(friend_ip)

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
                friend_name = current_ips[ip][1]
                friend_ip = current_ips[ip][0][0]
                break
        if found:
            message_to_send = protocol[2]
            if current_ips[index_friend][0] != clientAddress:  # If client is not sending message to themselves
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
            # if group_mode:
            serverSocket.sendto(message_to_send, friend_)
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
            # print("SENT")
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
        for desired_member in protocol[2:-2]:
            if user_exists(desired_member):
                group_members.append(fetch_user(desired_member))
            elif not user_exists(desired_member):
                non_member += desired_member + "\n"

        if non_member != "":
            print("The following member(s) were not found: " + non_member)
            serverSocket.sendto(
                (base64.b64encode(str("The following member(s) were not found: \m" + non_member).encode("utf-8"))),
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

    command = protocol[0]  # Gets command: JOIN, CHAT, EXIT (maybe add DISPLAY)

    if command == 'CHAT':
        chat()

    if command == 'ACTIVE':
        serverSocket.sendto((base64.b64encode(str(current_ips).encode("utf-8"))), clientAddress)

    if command == 'JOIN':
        name = protocol[1]
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
       
        group_specific(temp, True)

    if command == 'EXIT':
        name = protocol[1]
        temp = clientAddress, name
        current_ips.remove(temp)  # Removes IP from current list if they end their connection to the server

    if command == 'CHECKINDB':
            cursor.execute('select userName from userInfo')
            list_users = [item[0] for item in cursor.fetchall()]
            print(list_users)
            if temp[1] not in list_users:
                serverSocket.sendto(('NEWUSER').encode(), clientAddress)
            else:
                serverSocket.sendto(('OLDUSER').encode(), clientAddress)
    
    if command == 'NEWUSERPASSWORD':
        name = protocol[1]
        password = protocol[2]
        cursor.execute('insert into userInfo (userName, ipAddress) values (\'' + name + '\', \'' + clientAddress[0] +'\')') 
        conn.commit()
        cursor.execute('select userID from userInfo where userName = \'' + name +'\'')
       
        clientID = cursor.fetchone()[0]
        cursor.execute('insert into userPassword (userID, userPassword) VALUES (\''  + str(clientID) + '\', ' + '\'' + password + '\')')
        conn.commit()

    if command == 'CHECKPASSWORD':
        cursor.execute('select userID from userInfo where userName = \'' + name +'\'')
       
        clientID = cursor.fetchone()[0]
        logged_in = False
        right_password = cursor.execute("SELECT userPassword FROM UserPassword where userID = " + str(clientID)).fetchall()
        print(right_password[0][0])
        print( protocol[1])
        check_pass =protocol[1]
        if check_pass == right_password[0][0]:
            print('here')
            logged_in = True 
            print(logged_in)
        while logged_in != True:            
            serverSocket.sendto('WRONG'.encode(), clientAddress)
            if right_password == check_pass:
                logged_in = True
                break
        serverSocket.sendto("LOGGEDIN".encode(), clientAddress)

    if command == 'CHECK_FOR_GROUP':
        print("HERE")
        g_name = protocol[1]
        print('\n' + g_name)
        in_db = False
        cursor.execute('SELECT GroupName from GroupInfo')
        group_list = [group for group in cursor.fetchall()]
        for i in range(len(group_list)):
            if group_list[i][0] == g_name:
                in_db = True 
        if in_db:
            serverSocket.sendto(base64.b64encode(('OLD_GROUP#' + g_name).encode('utf8')), clientAddress)
        else:     
            serverSocket.sendto(base64.b64encode(('NEW_GROUP#'  + g_name).encode('utf8')), clientAddress)
    

