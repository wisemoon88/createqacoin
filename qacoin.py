# Module 2 - Create a Cryptocurrency

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.18.4: pip install requests==2.18.4

# Importing the libraries
import datetime #used for timestamping the block
import hashlib #this is used in the sha256 encryption
import json #used to create and utilize json files
from flask import Flask, jsonify, request #flask is a web app, jsonify is to jsonify something? requests is to use requests library
import requests
from uuid import uuid4 #this creates a address for the node port
from urllib.parse import urlparse #this parses the full address to only get the node without the http

# Part 1 - Building a Blockchain

class Blockchain: # this is creating the blockchain class.  a class can be used as soon as it is defined.

    def __init__(self): #__init__ is defined so that the instance automatically has the attributes of the class when an instance is created
        self.chain = [] # creating a list of the chain.  mined blocks will be stored in this list
        self.transactions = [] # creating a list of transactions which will be stored before mined into the blockchain
        self.create_block(proof = 1, previous_hash = '0') # when a Blockchain class is created, it will create a block by default.  this will be the genesis block with arbitrary proof of 1 and previous hash 0
        self.nodes = set() # creating a node variable which is an empty set which will be used to store the addresses of the nodes in the network
    
    def create_block(self, proof, previous_hash): # this creates a create block method which requires argument of proof and previous hash 
        block = {'index': len(self.chain) + 1, #block variable is a dictionary with various keys and values.  len(self.chain) gives length of the current chain which provides value for index
                 'timestamp': str(datetime.datetime.now()), #datetime library has now method which gives timestamp for the actual time when block was mined
                 'proof': proof, #coming from argument value
                 'previous_hash': previous_hash, # coming from argument value
                 'transactions': self.transactions} #transaction key will take in the current list in the self.transaction attribute
        self.transactions = [] #once block is mined, all transactions are stored in the block hence all current transactions in list will need to be emptied
        self.chain.append(block) # block variable created will be appended to the chain list.
        return block

    def get_previous_block(self): #method to get the previous block which returns the block of the last block in the list of the chain
        return self.chain[-1]

    def proof_of_work(self, previous_proof): #method to perform proof of work which needs to solve a formula prior to approval for creating block
        new_proof = 1 #initialize
        check_proof = False #initialize
        while check_proof is False: # while loop to keep iterating while proof is not satisfied
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest() #sha256 is method in hashlib library to perform sha256 encryption on the equation used as proof of work.encode adds a 'b' and hexdigest converts the value to hexadecimal
            if hash_operation[:4] == '0000': # check variable if generated hexadecimal has 4 leading zeros.  if true exit while loop if not add 1 to new proof and keep iterating
                check_proof = True
            else:
                new_proof += 1
        return new_proof # returns new proof as proof of work
    
    def hash(self, block): #hash method which returns the sha256 hash of the argument block
        encoded_block = json.dumps(block, sort_keys = True).encode() #json.dumps converts a python dictionary to a json string
        return hashlib.sha256(encoded_block).hexdigest() #returns the sha256 hash of the argument block
    
    def is_chain_valid(self, chain): #method to check if the chain is valid
        previous_block = chain[0] #initializing from 1st genesis block
        block_index = 1 #initiallizing
        while block_index < len(chain): #keep iterating while current index is still smaller than length of chain
            block = chain[block_index] #getting the current block
            if block['previous_hash'] != self.hash(previous_block): # comparing previous hash of current block and hash of previous block.  if not the same return false
                return False 
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000': # checking if hash operation has a valid proof of work.  done by comparing previous proof and current proof in operation equation
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount): #method to add transaction into list prior to adding into block.  takes in sender, receiver and amount argument
        self.transactions.append({'sender': sender, #append the arguments into the transaction list as a dictionary with 3 keys and values coming from argument
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block() #getting previous block
        return previous_block['index'] + 1 # returning a value of the next block index to be mined
    
    def add_node(self, address): #method to add nodes into the network
        parsed_url = urlparse(address) #parses the address into different sections
        self.nodes.add(parsed_url.netloc) #netloc gets only the address without the http
    
    def replace_chain(self): # replaces chain from the network if it is not the shortest
        network = self.nodes #current network of nodes which is a set
        longest_chain = None #initializing
        max_length = len(self.chain) # checking the length of the current chain in the current blockcain
        for node in network: #looping the nodes in the network and checking length of chain in each
            response = requests.get(f'http://{node}/get_chain') # getting the address of the node and requesting check.  need to understand hand in hand together with get chain method in part 2
            if response.status_code == 200:
                length = response.json()['length'] # taking the length json value from the json file
                chain = response.json()['chain'] #taking the chain json value from the json file
                if length > max_length and self.is_chain_valid(chain): # check if length of current chain is larger than current max length in node.  and if chain is valid.  if so update max length with current length and longest chain with current chain
                    max_length = length #check if length of current chain is larger than current max length in node.  and if chain is valid.  if so update max length with current length and longest chain with current chain
                    longest_chain = chain #check if length of current chain is larger than current max length in node.  and if chain is valid.  if so update max length with current length and longest chain with current chain
        if longest_chain: # if longest chain has been update ie True, will need to update the chain in the current node with the longest chain
            self.chain = longest_chain
            return True #return true as end of method if chain has been updated
        return False

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__) # defining an app with the flask class

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '') #defining an node address using the uuid4

# Creating a Blockchain
blockchain = Blockchain() # defining a blockchain with the blockchain class

# Mining a new block
@app.route('/mine_block', methods = ['GET']) #decorator used to define a mine block function with a get methods
def mine_block(): #defining a mine block function which can be requested from postman
    previous_block = blockchain.get_previous_block() # getting previous block
    previous_proof = previous_block['proof'] # getting previous blocks proof
    proof = blockchain.proof_of_work(previous_proof) # getting proof of work for the block to be created
    previous_hash = blockchain.hash(previous_block) # hashing the previous block to be used as argument for the create block method
    blockchain.add_transaction(sender = node_address, receiver = 'Hadelin', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Hadcoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5000)
