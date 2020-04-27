import requests, json, time
from multiprocessing.dummy import Pool

pool = Pool(100)

transactions0 = []
transactions1 = []
transactions2 = []
transactions3 = []
transactions4 = []

nodeid = {
    'id0': 0,
    'id1': 1,
    'id2': 2,
    'id3': 3,
    'id4': 4
}

node = {
    '0': 'http://192.168.0.1:5000',
    '1': 'http://192.168.0.2:5001',
    '2': 'http://192.168.0.3:5002',
    '3': 'http://192.168.0.4:5003',
    '4': 'http://192.168.0.5:5004'
}

def trans(transactions, src_id):
    for tran in transactions:
        temp = {
            "id": nodeid[tran[0]],
	        "amount": int(tran[1])
        }
        body = json.dumps(temp)
        r = requests.post(node[src_id]+'/createtransaction', data=body)

if __name__ == '__main__':
    with open('../5nodes/transactions0.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            transactions0.append(line.split(' '))
    with open('../5nodes/transactions1.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            transactions1.append(line.split(' '))
    with open('../5nodes/transactions2.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            transactions2.append(line.split(' '))
    with open('../5nodes/transactions3.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            transactions3.append(line.split(' '))
    with open('../5nodes/transactions4.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        for line in lines:
            transactions4.append(line.split(' '))
    
    request_list = []

    r = requests.get(node['1']+'/requestregistration')
    r = requests.get(node['2']+'/requestregistration')
    r = requests.get(node['3']+'/requestregistration')
    r = requests.get(node['4']+'/requestregistration')

    r = requests.get(node['0']+'/starttimer')
    r = requests.get(node['1']+'/starttimer')
    r = requests.get(node['2']+'/starttimer')
    r = requests.get(node['3']+'/starttimer')
    r = requests.get(node['4']+'/starttimer')

    target_url = node['0']+'/begin'
    request_list.append(pool.apply_async(requests.get, [target_url]))
    target_url = node['1']+'/begin'
    request_list.append(pool.apply_async(requests.get, [target_url]))
    target_url = node['2']+'/begin'
    request_list.append(pool.apply_async(requests.get, [target_url]))
    target_url = node['3']+'/begin'
    request_list.append(pool.apply_async(requests.get, [target_url]))
    target_url = node['4']+'/begin'
    request_list.append(pool.apply_async(requests.get, [target_url]))

    time.sleep(5)
    request_list = []
    request_list.append(pool.apply_async(trans, [transactions0,'0']))
    request_list.append(pool.apply_async(trans, [transactions1,'1']))
    request_list.append(pool.apply_async(trans, [transactions2,'2']))
    request_list.append(pool.apply_async(trans, [transactions3,'3']))
    request_list.append(pool.apply_async(trans, [transactions4,'4']))
                
    for req in request_list:
        req.get()
