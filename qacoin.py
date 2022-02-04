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

    def get_previous_block(self): #method to get the previous block which returns the block of the previous chain in the list
        return self.chain[-1]

    def proof_of_work(self, previous_proof): #method to perform proof of work which needs to solve a formula prior to approval for creating block
        new_proof = 1 #initialize
        check_proof = False #initialize
        while check_proof is False: # while loop to keep iterating while proof is not satisfied
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest() #sha256 is method in hashlib library to perform sha256 encryption on the equation used as proof of work.encode adds a 'b' and hexdigest converts the value to hexadecimal
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
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
