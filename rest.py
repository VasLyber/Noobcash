from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests, json, time
import node, config

app = Flask(__name__)
CORS(app)
curr_node= None

#////////////////////////////////////////////////////////
# ONLY BOOTSRAP NODE CAN USE THIS FOR ADDING NODE TO RING
#////////////////////////////////////////////////////////
@app.route('/addnodetoring', methods=['POST'])
def add_node_to_ring():
    new_node = {}
    data = request.get_json(force=True)
    new_node['pubkey'] = data['pubkey']
    new_node['ip'] = data['ip']
    new_node['port'] = data['port']
    print(new_node)
    curr_node.register_node_to_ring(new_node)
    return jsonify(status='successful')
#////////////////////////////////////////////////////////


#////////////////////////////////////////////////////////
#        ENDPOINTS USED FOR NODE REGISTRATION  
#////////////////////////////////////////////////////////
@app.route('/requestregistration', methods=['GET'])
def request_registration():
    if curr_node.bootstrap_ip != '-1':
        temp = {
                'pubkey': curr_node.wallet.address,
                'ip': curr_node.ring[0]['ip'],
                'port': curr_node.ring[0]['port']
        }
        body = json.dumps(temp)
        # print(body)
        r = requests.post('http://'+curr_node.bootstrap_ip+':'+curr_node.bootstrap_port+'/addnodetoring', data=body)
    return jsonify(status='OK')

# AFTER REGISTRATION ALL NOES NEEDS TO KNOW GENESIS BLOCK
@app.route('/receivegenesis', methods = ['POST'])
def receive_genesis_block():
    data = request.get_json(force=True)
    curr_node.getGenesisBlock(data)
    return jsonify(status="ok")

# USED TO CONNECT ALL WALLETS WITH ALL NODES  
@app.route('/receivewallets', methods = ['POST'])
def receive_wallets():
    data = request.get_json(force=True)
    print(data)
    curr_node.ring = data
    return jsonify(status="ok")
#////////////////////////////////////////////////////////


#//////////////////////////////////////////////////////////
#   CREATING, BROADCASTING AND RECEIVING TRANSACTIONS 
#//////////////////////////////////////////////////////////
@app.route('/createtransaction', methods = ['POST'])
def create_transaction():
    data = request.get_json(force=True)
    id = data['id']
    ring = curr_node.ring
    wallet = None
    for i in ring:
    	if id == i['id']:
        	wallet = i['pubkey']
    amount = data['amount']
    new_transaction = curr_node.create_transaction(wallet, amount)
    curr_node.broadcast_transaction(new_transaction)
    return jsonify(status="ok")
    
@app.route('/receivetransaction', methods = ['POST'])
def receive_transaction():
    curr_node.transaction_counter+=1
    if curr_node.transaction_counter == 10*config.number_of_nodes:
        curr_node.stop = True
    data = request.get_json(force=True)
    # print("I ENTERED RECEIVE, HERE'S THE TRANSACTION")
    # print(data)
    curr_node.validate_transaction(data)
    return jsonify(status="ok")
#//////////////////////////////////////////////////////////


#////////////////////////////////////////////////////////
#   MINING AND RESOLVING POSSIBLE CONFLICTS     
#////////////////////////////////////////////////////////
@app.route('/begin', methods = ['GET'])
def try_mine():
    curr_node.continuous_mining()

@app.route('/chain', methods = ['GET'])
def chain_send():
    chain = curr_node.chain
    return jsonify(chain=chain)

@app.route('/chainlength', methods = ['GET'])
def chain_len():
    _len = len(curr_node.chain)
    return jsonify(length=_len)
#////////////////////////////////////////////////////////


#//////////////////////////////////////////////////////////
#       ENDPOINT FOR BLOCK RECEIVING A BLOCK
#//////////////////////////////////////////////////////////
@app.route('/receiveblock', methods = ['POST'])
def receive_block():
    data = request.get_json(force=True)
    curr_node.receive_block(data)
    return jsonify(status="ok")
#//////////////////////////////////////////////////////////


#////////////////////////////////////////////////////////
#    ENDPOINTS FOR MEASURING PROGRAM'S EFFICIENCY
#////////////////////////////////////////////////////////
@app.route('/starttimer', methods = ['GET'])
def start_timer():
    curr_node.start_time = time.time()
    return jsonify(status="ok")

@app.route('/totaltime', methods = ['GET'])
def get_timer():
    ret = curr_node.total_time
    if curr_node.block_timer_counter == 0:
        return jsonify(time_transactions=ret,avg_time_mine=0,blocks_mined=0)
    else:
        ret_block = curr_node.block_timer_sum / curr_node.block_timer_counter
        return jsonify(time_transactions=ret,avg_time_mine=ret_block,blocks_mined = curr_node.block_timer_counter)
#////////////////////////////////////////////////////////


#//////////////////////////////////////////////////////////
#   OTHER ENDPOINTS NEEDED FOR RUNNING THE APPLICATION
#//////////////////////////////////////////////////////////
@app.route('/getutxo', methods=['GET'])
def get_utxos():
    utxos = []
    for i in curr_node.UTXO:
        utxos.append(i.to_dict())
    return jsonify(utxo=utxos)

@app.route('/getwallets', methods=['GET'])
def get_wallets():
    wallets = curr_node.ring
    # body = json.dumps(wallets)
    return jsonify(wall=wallets)

@app.route('/getbalance', methods = ['GET'])
def get_balance():
    wallet = curr_node.wallet
    res = wallet.balance(curr_node.UTXO)
    return jsonify(amount=res)

@app.route('/getchain', methods=['GET'])
def get_blockchain():
    return jsonify(chain=curr_node.chain)    
#//////////////////////////////////////////////////////////


#//////////////////////////////////////////////////////////
#                      MAIN FUNCTION  
# runnign example:
# python3 rest.py -ip 127.0.0.1 -p 5000 -bip -1 -bport -1 -diff 4
#//////////////////////////////////////////////////////////
if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', default=5000, help='port to listen on')
    parser.add_argument('-diff', default=4, help='set difficulty of POW')
    parser.add_argument('-ip', help='ip to listen on')
    parser.add_argument('-bip', help='bootstrap ip, -1 if bootstrap')
    parser.add_argument('-bport', help='bootstrap port, -1 if bootstrap')
    args = parser.parse_args()
    config.difficulty = int(args.diff)
    port = args.p
    curr_node= node.Node(args.ip, args.p, args.bip, args.bport)
    app.run(host='0.0.0.0', port=port, threaded=True)
#//////////////////////////////////////////////////////////
