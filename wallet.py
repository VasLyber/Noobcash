import binascii , hashlib, json , config , Crypto ,Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from time import time
from urllib.parse import urlparse
from uuid import uuid4

class Wallet:
	def __init__(self):
		self.private_key = RSA.generate(1024, Crypto.Random.new().read)
		self.public_key = self.private_key.publickey()
		self.signer = PKCS1_v1_5.new(self.private_key)

	def sign_transaction(self, message):
		h = SHA.new(str(message).encode('utf8'))
		return binascii.hexlify(self.signer.sign(h)).decode('ascii')

	def balance(self, utxolist):
		balance = 0
		for ut in utxolist:
			if ut.get_receiver() == self.address:
				balance = balance+ut.amount
		return balance

	@property
	def address(self):
		return binascii.hexlify(self.public_key.exportKey(format='DER')).decode('ascii')

def verify_signature(wallet_address, message, signature):
	pubkey = RSA.importKey(binascii.unhexlify(wallet_address))
	verifier = PKCS1_v1_5.new(pubkey)
	h = SHA.new(str(message).encode('utf8'))
	return verifier.verify(h, binascii.unhexlify(signature))
