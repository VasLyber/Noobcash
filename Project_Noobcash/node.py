from multiprocessing.dummy import Pool
from collections import OrderedDict
import hashlib , requests, json
import block , wallet, config , transaction, time
pool = Pool(100)


#/////////////////////////////////////////////////////////
#	CLASS REPRESENTING EVERY NODE CONNECTED TO THE RING
#/////////////////////////////////////////////////////////
class Node:
	def __init__(self, ip, port, bootstrap_ip, bootstrap_port):
		# variables used for communication
		self.ip = ip
		self.port = port
		self.bootstrap_ip = bootstrap_ip
		self.bootstrap_port = bootstrap_port
		self.wallet = self.create_wallet()
		self.ring = [{
			'pubkey' : self.wallet.address,
			'ip'   : ip,
			'port' : port,
			'id'   : int(port) % 10 #works for up to 10 nodesS
		}]
		#blockchain
		self.chain = []
		self.verified_transactions = []
		self.UTXO = []
		# like a transaction pool, but transactions<=maximum
		self.current_block  = []

		#variables used for mining
		self.isMining = False
		self.lock_for_resolving_conflicts = False
		self.mining_needs_to_stop = False
		self.usingChain = False
		self.bcounter = 0
		self.blockWhileMining = []

		# variables  for measuring block time
		self.block_timer_start = None
		self.block_timer_end = None
		self.block_timer_sum = 0
		self.block_timer_counter = 0

		# variables for measuring time of total transactions
		self.start_time = None
		self.end_time = None
		self.transaction_counter = 0
		self.total_time = None

		#variable for terminating loop of continuous mining
		self.stop = False

	# ////////////////////////////////////////////////////////////
	#	 			 INITIALIZATION FUNCTIONS
	# ////////////////////////////////////////////////////////////
	# 		ONLY BOOTSTRAP RUNS THIS FUNCTION
	def register_node_to_ring(self, new_node): #only bootstrap can do that
		# print("Entered reg_ring")
		temp = {
				'pubkey' : new_node['pubkey'],
				'ip'		: new_node['ip'],
				'port'   : new_node['port'],
				'id'   : int(new_node['port']) % 10 #this is used for 10 nodes
			}
		self.ring.append(temp)
		# print(self.ring)
		if len(self.ring) == config.number_of_nodes:
			body = json.dumps(self.ring)
			for i in self.ring:
				res = requests.post('http://'+i['ip']+':'+i['port']+'/receivewallets', data = body )
			self.create_genesis_transactions()

	def create_wallet(self):
		##create a wallet for this node, with a public key and a private key
		return wallet.Wallet()
	# ////////////////////////////////////////////////////////////



	# ////////////////////////////////////////////////////////////
	#		 FIRST BLOCK IN BLOCKCHAIN FUNCTIONS
	# ////////////////////////////////////////////////////////////
	def create_genesis_block(self, genesis_transactions):
		genesis_block = block.GenesisBlock(genesis_transactions)
		transaction_dict = []
		for i in genesis_block.listOfTransactions:
			transaction_dict.append(i.to_dict())
		genesis_block.listOfTransactions = transaction_dict
		genblock_final = genesis_block.to_dict()
		body = json.dumps(genblock_final)
		for i in self.ring:
			res = requests.post('http://'+i['ip']+':'+i['port']+'/receivegenesis', data = body )

	def getGenesisBlock(self,genblock):
		#put genesis block in chain
		self.chain.append(genblock)
		#crete utxos and append them to the list
		for i in genblock['transactions']:
			output = transaction.TransactionOutput(i['receiver_address'] , i['amount'])
			self.UTXO.append(output)

	def create_genesis_transactions(self):
		genesis_transactions = []
		for i in self.ring:
			new_transaction = transaction.GenesisTransaction(i['pubkey'], 100)
			genesis_transactions.append(new_transaction)
		self.create_genesis_block(genesis_transactions)
	# ////////////////////////////////////////////////////////////


	#///////////////////////////////////////////////////////
	#		FUNCTIONS IMPLEMENTING TRANSATIONS
	#///////////////////////////////////////////////////////
	def create_transaction(self, receiver, amount):
		transaction_input = []
		#inputs ola ta outputs pou exoun os receiver ton torino sender
		bal = 0
		for i in self.UTXO:
			if i.recipient == self.wallet.address:
				transaction_input.append(i)
				bal = bal + i.amount
		new_transaction = transaction.Transaction(self.wallet, receiver, amount, transaction_input)
		new_transaction.add_id_to_output()
		new = new_transaction.transaction_to_dict(include_hash=True)
		return new

	def broadcast_transaction(self, dict):
		body = json.dumps(dict)
		request_list = []
		for i in self.ring:
			target_url = 'http://'+i['ip']+':'+i['port']+'/receivetransaction'
			request_list.append(pool.apply_async(requests.post, [target_url,body]))
		for req in request_list:
			print(req.get())

	def validate_transaction(self, _transaction, resolve_confl = False):
		tran = {"sender": _transaction['sender'],
			 "receiver": _transaction['receiver'],
             "amount": _transaction['amount'],
             "inputs": _transaction['inputs'],
             "outputs": _transaction['outputs']
		}
		if (wallet.verify_signature(tran["sender"] , tran , _transaction['signature'])):
			print("I just verified one transaction")
			transaction_input=[]
			total_sum=0
			for i in self.UTXO:
				i_to_dict = i.to_dict()
				if (i_to_dict['recipient'] == _transaction['sender']):
					transaction_input.append(i)
					total_sum = total_sum+i.amount
			if (total_sum>=_transaction['amount']):
			#eparki xrimata gia tin metafora
				for tran in transaction_input:
					self.UTXO.remove(tran)
				#now create transaction outputs and add them at the utxo list
				output1=transaction.TransactionOutput(_transaction['receiver'] , _transaction['amount'])
				output2=transaction.TransactionOutput(_transaction['sender'] ,total_sum-_transaction['amount'])
				self.UTXO.append(output1)
				self.UTXO.append(output2)
				if not resolve_confl:
					self.verified_transactions.append(_transaction)
			return True
		else:
			return False
	#///////////////////////////////////////////////////////


	#///////////////////////////////////////////////////////
	# 		FUNCTIONS IMPLEMENTING ALL MINING JOBS
	#///////////////////////////////////////////////////////
	def mine_job(self):
		for i in range(config.max_transactions):
			self.current_block.append(self.verified_transactions[i])

		previousblock = self.chain[-1]
		previousmessage = OrderedDict(
				{'transactions': previousblock['transactions'],
					'previousHash':  previousblock['previousHash'],
					'number': previousblock['number'],
					'timestamp': previousblock['timestamp']
				})
		previoushash = hashlib.sha256((str(previousmessage)+previousblock['nonce']).encode()).hexdigest()
		new_block = block.Block(previoushash, self.current_block, previousblock['number'])
		self.mine_block(new_block)
		return

	def mine_block( self, _block):
		print("I am mining")
		self.isMining = True
		# save previoushash for block being mined in order to check it after finish mining
		last_block = self.chain[-1]
		previousmessage = OrderedDict(
						{'transactions': last_block['transactions'],
						 'previousHash': last_block['previousHash'],
						 'timestamp': last_block['timestamp'],
						 'number': last_block['number']
						})
		my_previous_hash = hashlib.sha256((str(previousmessage)+last_block['nonce']).encode()).hexdigest()
		message = _block.to_dict(include_nonce=False)
		nonce = self.search_proof(message)
		_block.add_nonce(nonce)
		if nonce == "nope":
			self.isMining = False
			return

		while self.usingChain:
			pass
		self.usingChain = True
		last_block = self.chain[-1]
		self.usingChain = False
		previousmessage = OrderedDict(
						{'transactions': last_block['transactions'],
						 'previousHash': last_block['previousHash'],
						 'timestamp': last_block['timestamp'],
						 'number': last_block['number']
						})
		new_previous_hash = hashlib.sha256((str(previousmessage)+last_block['nonce']).encode()).hexdigest()
		if new_previous_hash == my_previous_hash:
			self.broadcast_block(_block.to_dict())
			self.current_block = []
		self.isMining = False
		return

	def search_proof(self, message):
		self.block_timer_start = time.time()
		i = 0
		prefix = '0' * config.difficulty
		self.mining_needs_to_stop = False
		while not self.mining_needs_to_stop:
			nonce = str(i)
			digest = hashlib.sha256((str(message) + nonce).encode()).hexdigest()
			if digest.startswith(prefix):
				print(digest)
				self.block_timer_end = time.time()
				self.block_timer_sum += self.block_timer_end - self.block_timer_start
				self.block_timer_counter += 1
				return nonce
			i += 1
		if self.mining_needs_to_stop == True:
			print("Mining process interrupted, block was mined somewhere else :(\n")
			return "nope"
	#///////////////////////////////////////////////////////



	#///////////////////////////////////////////////////////
	#			FUNCTIONS FOR BLOCKCHAIN
	#///////////////////////////////////////////////////////
	def receive_block(self, block):
		while self.usingChain:
			pass
		self.usingChain = True
		self.validate_block(block)
		self.usingChain = False
		return

	def broadcast_block(self, dict):
		print('broadcasting block!')
		body = json.dumps(dict)
		request_list = []
		for i in self.ring:
			target_url = 'http://'+i['ip']+':'+i['port']+'/receiveblock'
			request_list.append(pool.apply_async(requests.post, [target_url,body]))
		for req in request_list:
			print(req.get())
		return
	#///////////////////////////////////////////////////////


	#///////////////////////////////////////////////////////
	#					CONCENCUS FNCTIONS
	#///////////////////////////////////////////////////////
	def validate_block(self,block):
		#check proof of work
		proofofwork = self.valid_proof(block)
		if (proofofwork):
			#check previous hash
			previousblock=self.chain[-1]
			previousmessage = OrderedDict(
						{'transactions': previousblock['transactions'],
						 'previousHash':  previousblock['previousHash'],
						 'number': previousblock['number'],
						 'timestamp': previousblock['timestamp']
						})
			previoushash = hashlib.sha256((str(previousmessage)+previousblock['nonce']).encode()).hexdigest()
			if len(self.chain) >= 2:# diklida asfaleias gia 2 receive
				previousblock=self.chain[-2]
				previousmessage = OrderedDict(
							{'transactions': previousblock['transactions'],
							'previousHash':  previousblock['previousHash'],
							#'nonce': self.nonce ,
							'number': previousblock['number'],
							'timestamp': previousblock['timestamp']
							})
				previoushash_2 = hashlib.sha256((str(previousmessage)+previousblock['nonce']).encode()).hexdigest()
				if block['previousHash'] == previoushash_2:
					return False

			if (block['previousHash'] != previoushash):
				print("wrong prev hash")
				flag = self.resolve_conflicts()
				if (flag==False):
					return False
				return True
			else:
				self.mining_needs_to_stop = True
				transactions=block['transactions']
				#check  all that transactions in received block are verified
				for tran in transactions:
					flag=0
					for vt in self.verified_transactions:
						if tran['id']==vt['id'] :
							flag=1
					if flag==0:
						return False
					flag=0
				#if all transactions in block are verified remove them from verified_trans
				for tran in transactions:
					for vt in self.verified_transactions:
						if tran['id']==vt['id'] :
							self.verified_transactions.remove(vt)
				self.chain.append(block)
				self.current_block = []
				return True
		return False

	def valid_proof(self , block):
		temp= OrderedDict({'transactions': block['transactions'],
						 'previousHash':  block['previousHash'],
						 'number': block['number'],
						 'timestamp': block['timestamp']
						})
		print("I received block, time to check proof of work")
		nonce = block['nonce']
		digest = hashlib.sha256((str(temp) + nonce).encode()).hexdigest()
		if ( digest.startswith('0' * config.difficulty)):
			return True
		else:
			return False

	def valid_chain(self, blockchain):
		# check for the longer chain accroose all nodes
		last_block = blockchain[0]
		current_index = 1
		while current_index < len(blockchain):
			block = blockchain[current_index]
			if block['previous_hash'] != hashlib.sha256(last_block.to_dict(include_nonce= False)+last_block['nonce']).hexdigest():
				return False
			# I need to do 3 thing:
			# Check that the Proof of Work is correct
			# Need to make sure that the dictionary is ordered. Otherwise we'll get a different hash
			# Delete the reward transaction
			if not self.valid_proof(block):
				return False

			last_block = block
			current_index += 1

		return True

	def resolve_conflicts(self):
		print("Found some conflicts. Time to resolve them")
		max_chain = -1
		node_max_chain = None
		for i in self.ring:
			req = requests.get('http://'+i['ip']+':'+i['port']+'/chainlength')
			res = req.json()
			if res['length'] > max_chain:
				node_max_chain = res['length']
				node_max_chain = i
		req = requests.get('http://'+node_max_chain['ip']+':'+node_max_chain['port']+'/chain')
		res = req.json()
		chain = res['chain']
		# "lock" using condition variable #
		self.lock_for_resolving_conflicts = True
		self.UTXO = [] # new utxo list
		for bl in chain:
			trans = bl['transactions']
			for tran in trans:
				if bl['number'] == 0:
					output = transaction.TransactionOutput(tran['receiver_address'] , tran['amount'])
					self.UTXO.append(output)
				else:
					self.validate_transaction(tran, True)
					try:
						self.verified_transactions.remove(tran)
					except ValueError:
						pass
		for vt in self.verified_transactions:
			self.validate_transaction(vt, True)
		self.lock_for_resolving_conflicts = False
		return True
	#/////////////////////////////////////////////////////////


	#/////////////////////////////////////////////////////////
	#	 ALL NODES RUN AN INFINITE LOOP OF MINING
	#/////////////////////////////////////////////////////////
	def continuous_mining(self):
		print("node just started")
		while True:
			if len(self.verified_transactions) >= config.max_transactions and not self.current_block:#gemizei otan ksekinaie h
				self.mine_job()
			#time to stop
			if len(self.verified_transactions) < config.max_transactions and self.stop:
				self.end_time = time.time()
				self.total_time = self.end_time - self.start_time
				self.stop = False
	#/////////////////////////////////////////////////////////
