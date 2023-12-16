from collections import OrderedDict
import hashlib, json, datetime

#//////////////////////////////////////////////////////
# 			FIRST BLOCK OF BLOCKCHAIN
# ALMOST  THE SAME AS CLASS BLOCK BUT LESS FUNCTIONS 
#//////////////////////////////////////////////////////
class GenesisBlock:
	def __init__(self, genesis_tr):
		self.prevHash = 0
		self.timestamp = datetime.datetime.now()
		self.listOfTransactions = genesis_tr
		self.blocknumber = 0
		self.nonce = "0"

	def to_dict(self, include_nonce = True):
		if include_nonce == False:
			temp= OrderedDict({
				'transactions': self.listOfTransactions,
				'previousHash': self.prevHash,
				'number': self.blocknumber,
				'timestamp': str(self.timestamp)
			})
		else:
			temp= OrderedDict({
				'transactions': self.listOfTransactions,
				'previousHash': self.prevHash,
				'number': self.blocknumber,
				'timestamp': str(self.timestamp),
				'nonce': self.nonce
			})
		return temp
#//////////////////////////////////////////////////////


#//////////////////////////////////////////////////////
#		BLOCKS USED TO CREATE BLOCKCHAIN
#//////////////////////////////////////////////////////
class Block:
	def __init__(self, previousHash, listoftransactions, last_block):
		self.prevHash = previousHash
		self.timestamp = datetime.datetime.now()
		self.listOfTransactions = listoftransactions
		self.blocknumber = last_block+1
		self.nonce = None

	def to_dict(self, include_nonce = True):
		if include_nonce == False:
			temp= OrderedDict({
				'transactions': self.listOfTransactions,
				'previousHash': self.prevHash,
				'number': self.blocknumber,
				'timestamp': str(self.timestamp)
			})
		else:
			temp= OrderedDict({
				'transactions': self.listOfTransactions,
				'previousHash': self.prevHash,
				'number': self.blocknumber,
				'timestamp': str(self.timestamp),
				'nonce': self.nonce
			})
		return temp

	# setters and getters
	def add_hash(self, h):
		self.currenthash = h

	def add_nonce(self, n):
		self.nonce = n
	
	def getHash(self):
		return self.currenthash

	def getblocknum(self):
		return self.blocknumber

#//////////////////////////////////////////////////////


	

