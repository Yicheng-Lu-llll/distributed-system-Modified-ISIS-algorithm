# -*- coding: utf-8 -*-
# Editor: Sunrise
# Date: 2022/4/14 19:08


import json
import sys
import socket
import heapq
from threading import Thread, Lock
import time
import errno

local_name = ''  # my node name
timeStamp = 0
timeStamp_lock = Lock()

num_connected_nodes = 0  # # of nodes connected to me
num_connected_nodes_lock = Lock()

node_socket_dict = {}  # form: {node1: [sockets]}
node_socket_dict_lock = Lock()

balance_dict = {}  # key: account. value: moeny
balance_dict_lock = Lock()

sleep_time = 0.05

max_send_times = 8

msgID_repo = []  # list of message ID, used for checking if the message (with same ID) is received
msgID_repo_lock = Lock()
received_repo = []  # list of (messageID, priority, sender), used for R-multicast
received_repo_lock = Lock()
msgSender_dict = {}  #
msgSender_dict_lock = Lock()


class Message:
    def __init__(self, sender='', content='', ID='', priority=''):
        self.sender = sender  # sender name, e.g. node1
        self.content = content  # message content
        self.ID = ID  # node name + timestamp
        self.priority = priority  # the priority

    def get_message_string(self):
        # convert the class to string message
        jsonDict = {}
        jsonDict['sender'] = self.sender
        jsonDict['content'] = self.content
        jsonDict['ID'] = self.ID
        jsonDict['priority'] = self.priority
        return json.dumps(jsonDict).encode('utf-8')

    def from_json(self, jsonData):
        self.sender = jsonData["sender"]
        self.content = jsonData["content"]
        self.ID = jsonData["ID"]
        self.priority = jsonData["priority"]

    def getSender(self):
        return self.sender

    def getContent(self):
        return self.content

    def getID(self):
        return self.ID

    def getPriority(self):
        p = self.priority.split('+')
        p[0], p[1] = int(p[0]), int(p[1])
        return p

    def setPriority(self, priority):
        self.priority = priority

    def setSender(self, sender):
        self.sender = sender

    def __lt__(self, item2):  # this compare fun is only for max heapq
        node1, time1 = self.getPriority()
        node2, time2 = item2.getPriority()

        if (time1 > time2) or (time1 == time2 and node1 > node2):
            return False
        if (time2 > time1) or (time1 == time2 and node2 > node1):
            return True
        else:
            print("__lt__",node1, time1)
            print("__lt__",node2, time2)
            print("compare error")
            return 0


class PriorityQueue:
    def __init__(self):
        self.q = []

    def getQueue(self):
        return self.q

    def push(self, message):
        heapq.heappush(self.q, message)

    def pop(self):
        return heapq.heappop(self.q)

    def update(self, message):
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print(message.getID(),message.getPriority(),message.getSender())
        print(self.printQ())
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        pos = -1
        for i in range(len(self.q)):
            cur_message = self.q[i]
            if message.getID() == cur_message.getID():
                pos = i
                break
        if pos == -1:
            print("should never reached")
        # print("update: ",message.getPriority(),self.q[pos].getPriority())
        if message > self.q[pos]:
            self.q[pos] = message
            heapq.heapify(self.q)
        return 

    def printQ(self):
        for i in range(len(self.q)):
            print(self.q[i].getID(),self.q[i].getPriority(),end=" , ")
        print()
        


PQ = PriorityQueue()
PQ_lock = Lock()


# set local socket in listening mode
def setSocket(IP, port):
    localSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    localSocket.bind((IP, port))
    localSocket.listen(10)
    return localSocket


# build TCP connection
def TCPConnect(filename):
    global num_connected_nodes
    global sleep_time

    nodes = decode_config(filename)
    # print("nodes info: ", nodes)
    for i in range(len(nodes)):
        curThread = Thread(target=TCPConnectSingle, args=(nodes[i][0], nodes[i][1], nodes[i][2]))
        curThread.start()
    time.sleep(sleep_time)

    # check if all nodes connected
    while True:
        if num_connected_nodes == len(nodes):
            # print(node_socket_dict)
            return True


def TCPConnectSingle(nodeName, nodeIP, nodePort):
    global num_connected_nodes
    global node_socket_dict

    # continue to connect to the node
    while True:
        curSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connected!
        if 0 == curSocket.connect_ex((nodeIP, nodePort)):
            # acquire lock to change num_connected_nodes
            num_connected_nodes_lock.acquire()
            num_connected_nodes += 1
            num_connected_nodes_lock.release()
            # acquire lock to append node_socket_dict
            node_socket_dict_lock.acquire()
            node_socket_dict[nodeName] = curSocket
            node_socket_dict_lock.release()

            # print(num_connected_nodes)
            return True
        # not connected, continue to try
        else:
            continue


# read config.txt file
def decode_config(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
        numNode = int(lines[0])
        nodes = []
        for i in range(1, len(lines)):
            line = lines[i].split(' ')
            line[-1] = int(line[-1])
            nodes.append(line)
        # check error
        if numNode != len(nodes):
            raise ValueError("Config file is wrong!")

    return nodes


def get_events():
    # write code to wait until all the nodes are connected
    global local_name
    global timeStamp
    global sleep_time
    global received_repo

    while True:
        for content in sys.stdin:
            if len(content) == 0:
                continue

            # init the message struct
            content.replace('\n', '')
            timeStamp_lock.acquire()
            ID = local_name + '+' + str(timeStamp)  # form: 'node1+1'
            priority = local_name[-1] + '+' + str(timeStamp)  # form: '1+1'
            timeStamp += 1
            timeStamp_lock.release()
            msg = Message(sender=local_name, content=content, ID=ID, priority=priority)
            received_repo_lock.acquire()
            received_repo.append( (ID, tuple(msg.getPriority()), msg.getSender()) )
            received_repo_lock.release()
            # register this message to some data structure to show that I have seen this message
           
            deliver(msg)
            multicast(msg)

            time.sleep(sleep_time)



def deliver(msg):
    # if I have never seen this message, register it to some dict or map, append it to holdback queue, reorder
    # if I have seen this message, but I have not receive the feedback for this message's sending node
    #     then I am going to update the largest priority number I have ever received for this message
    #     and also update the order of the queue
    global msgID_repo
    global msgSender_dict
    global PQ
    global timeStamp
    # print(" deliver enter")
    # check if message has been received
    if msg.getID() not in msgID_repo:
        msgID_repo_lock.acquire()
        msgID_repo.append(msg.getID())
        msgID_repo_lock.release()
        # append sender
        msgSender_dict_lock.acquire()
        # PQ.printQ()
        # print("###########create msgSender_dict key: ",msg.getID(),"sender",msg.getSender(), "p:",msg.getPriority())
        msgSender_dict[msg.getID()] = [msg.getSender()]
        msgSender_dict_lock.release()
        # insert into PQ
        PQ_lock.acquire()
        PQ.push(msg)
        PQ_lock.release()

    else:
        msgSender_dict_lock.acquire()
        # PQ.printQ()
        # print("msgSender_dict: key",msg.getID(),"sender",msg.getSender(), "p:",msg.getPriority())
        if msg.getID() not in msgSender_dict:
            msgSender_dict[msg.getID()] = []
        msgSender_dict[msg.getID()].append(msg.getSender())
        msgSender_dict_lock.release()
        # update PQ if needed
        PQ_lock.acquire()
        # for item in PQ.getQueue():
        #     if item.getID() == msg.getID():
        #         PQ.update(msg)
        PQ.update(msg)
        PQ_lock.release()


def multicast(msg):
    global node_socket_dict
    global num_connected_nodes
    global sleep_time
    global local_name
    print(local_name ," start multicast :",msg.getID(),msg.getPriority(),msg.getSender())
    json_msg = msg.get_message_string()
    
    node_socket_dict_lock.acquire()
    for nodeName in node_socket_dict:
        cur_socket = node_socket_dict[nodeName]
        flag = 1
        for _ in range(max_send_times):
            if not cur_socket.send(json_msg):  # send fails
                continue
            else:
                flag = 0  # send successfully
                break
        if flag:
            # delete failed node, decrease num_connected_node
            cur_socket.close()
            del node_socket_dict[nodeName]
            num_connected_nodes_lock.acquire()
            num_connected_nodes -= 1
            num_connected_nodes_lock.release()

    node_socket_dict_lock.release()


def deliver_queue_head():
    global PQ
    global msgSender_dict
    global num_connected_nodes
    # print("deliver_queue_head enter")
    # print(PQ.getQueue()[0].getID(),PQ.getQueue()[1].getID())
    while True:
        PQ_lock.acquire()
        msgSender_dict_lock.acquire()
        num_connected_nodes_lock.acquire()

        if len(PQ.getQueue()) <= 0:
            PQ_lock.release()
            msgSender_dict_lock.release()
            num_connected_nodes_lock.release()
            break
        message = PQ.getQueue()[0]
        num_receive_node = len(set(msgSender_dict[message.getID()]))
       
        print()
        print("messageID:",message.getID(),"num_receive_node:",num_receive_node," num_connected_nodes+1: ", num_connected_nodes + 1 )
        print(msgSender_dict[message.getID()])
        print()
        
        if num_receive_node == num_connected_nodes + 1: # 1 means itself
            # print("can pop queue now !!!")
            PQ.pop()
            # print("Q:",PQ.getQueue())
            # print("before delete:",msgSender_dict[message.getID()])
            # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@msgSender_dict delete key: ",message.getID())
            del msgSender_dict[message.getID()]
            update_balances(message)
        else:
            PQ_lock.release()
            msgSender_dict_lock.release()
            num_connected_nodes_lock.release()
            break
        
        PQ_lock.release()
        msgSender_dict_lock.release()
        num_connected_nodes_lock.release()


def print_balances():
    # print("print_balances ennter")
    global balance_dict
    for account in sorted(balance_dict):
        print("BALANCES " + account + ": " + str(balance_dict[account]), end=" ")
    print()


def update_balances(queue_head_message):
    global balance_dict
    # print("update_balances")
    # resolve message
    content_list = queue_head_message.getContent().split(' ')
    command = content_list[0]

    if command == "DEPOSIT":
        account, amount = content_list[1:]
        balance_dict_lock.acquire()
        if account in balance_dict:
            balance_dict[account] += int(amount)
        else:
            balance_dict[account] = 0
        balance_dict_lock.release()
        print_balances()

    elif command == "TRANSFER":
        account, _, dest, amount = content_list[1:]
        balance_dict_lock.acquire()

        if account not in balance_dict:
            balance_dict[account] = 0
        if dest not in balance_dict:
            balance_dict[dest] = 0
        if balance_dict[account] >= int(amount):
            balance_dict[account] -= int(amount)
            balance_dict[dest] += int(amount)
            print_balances()
        else:
            print("Account:" + account + " can not transfer money to Account: " + dest + "due to lack of amount")
        balance_dict_lock.release()

    else:
        print("bad message command! should never meet")


# keep trying to accept new connect
def receive(localSocket):
    while True:
        new_socket, _ = localSocket.accept()
        Thread(target=handle_receive, args=(new_socket,)).start()
        time.sleep(sleep_time)


def handle_receive(new_socket):
    global received_repo
    global msgID_repo
    global timeStamp
    global msgSender_dict
    global local_name
    global sleep_time
    # print("handle_receive enter")
    while True:
        # receive message
        raw_data = new_socket.recv(1024).decode('utf-8')
        if len(raw_data) == 0:
            continue
        else:
            while True:
                if raw_data[-1] != '}':  # } is the last char of the message
                    raw_data += new_socket.recv(1024).decode("utf-8")
                else:
                    break
        data_list = raw_data.split("}")

        for data in data_list:
            if len(data) <= 1:
                break
            data = data + "}"
            raw_dict = json.loads(data)
            cur_message = Message()
            cur_message.from_json(raw_dict)
            print("#############ID: ",cur_message.getID(),"sender",cur_message.getSender(),"#############")
       

        for data in data_list:
            if len(data) <= 1:
                break
            data = data + "}"
            raw_dict = json.loads(data)
            cur_message = Message()
            cur_message.from_json(raw_dict)
            
            # ensure R-multicast
            received_tuple = (cur_message.getID(), tuple(cur_message.getPriority()), cur_message.getSender())
            received_repo_lock.acquire()
            # print(received_repo)
            # print(received_tuple)
            # print(received_tuple  in received_repo)
            if received_tuple in received_repo:
                # print("received_tuple",received_tuple)
                received_repo_lock.release()
                continue           
            else:
                received_repo.append(received_tuple)
                received_repo_lock.release()
                multicast(cur_message)
            

            # first seen message
            if cur_message.getID() not in msgID_repo:
                # print("first seen message")
                # update priority
                timeStamp_lock.acquire()
                priority = local_name[-1] + '+' + str(timeStamp)  # form: '1+1'
                timeStamp += 1
                timeStamp_lock.release()
                temple_msg = Message(priority=priority)
                if temple_msg > cur_message:
                    cur_message.setPriority(priority)
                    new_tuple = (cur_message.getID(), tuple(cur_message.getPriority()), cur_message.getSender())
                    received_repo_lock.acquire()
                    received_repo.append(new_tuple)
                    received_repo_lock.release()

                deliver(cur_message)
                # update sender
                cur_message.setSender(local_name)
                received_repo_lock.acquire()
                new_tuple = (cur_message.getID(), tuple(cur_message.getPriority()), cur_message.getSender())
                received_repo.append(new_tuple)
                received_repo_lock.release()

                msgSender_dict_lock.acquire()
                msgSender_dict[cur_message.getID()].append(cur_message.getSender())
                msgSender_dict_lock.release()
               
                multicast(cur_message)
                deliver_queue_head()
                time.sleep(sleep_time)
            # already seen
            else:
                # print("already seen")
                deliver(cur_message)
                deliver_queue_head()
                time.sleep(sleep_time)


def main():

    global local_name
    global sleep_time

    flag = len(sys.argv)
    if 4 != flag:
        print("Wrong input to main function!")
        return False

    # print("111")
    local_name = sys.argv[1]
    localIP = "127.0.0.1"
    localPort = int(sys.argv[2])
    filepath = sys.argv[3]

    # build TCP connection to other banks
    localSocket = setSocket(localIP, localPort)
    TCPConnect(filepath)

    # All connect
    time.sleep(sleep_time)

    Thread(target=receive, args=(localSocket,)).start()

    while True:
        get_events()


if __name__ == '__main__':
    main()
