import argparse
import requests
import json

ch = {'t':'t','view':'view', 'help':'help', 'balance':'balance'}


def create_transaction(sender, receiver, amount):
        dictionary = {'id' : int(receiver),'amount' : int(amount)}
        body = json.dumps(dictionary)
        res = requests.post('http://localhost:500'+str(sender)+'/createtransaction', data = body )
        print(res)
        return True
        
def view_transactions(id):
        res = requests.get('http://localhost:500'+str(id)+'/chain' )
        data = res.json()
        print(data['chain'][-1])
        return True

def balance(id):
        res = requests.get('http://localhost:500'+str(id)+'/getbalance' )
        data = res.json()
        print(data)
        return True


def console(arg):
        print("------------ CLI ---------------")
        print(arg['command'])
        if (arg['command'] == 't'):
                if (len(arg['values']) == 3):
                        sender = arg['values'][0]
                        receiver = arg['values'][1]
                        amount = arg['values'][2]
                        create_transaction(sender, receiver, amount)
                else:
                        print("I need 2 values")
        elif arg['command'] == 'view':
                if (len(arg['values']) == 0):
                        id = arg['myid'][0]
                        view_transactions(id)
                else:
                        print("Remove arguments and try again")
        elif(arg['command'] == 'balance'):
                if (len(arg['values']) == 0):
                        id = arg['myid'][0]
                        balance(id)
                else:
                        print("Remove arguments and try again")
        elif(arg['command'] == 'help'):
                if (len(arg['values']) == 0):
                        print(" command t: USAGE: t sender_id receiver_id amount\n",
                                "command view: see last transactions of the latest validated block\n",
                                "command balance: see balance of specified wallet\n",
                        "command help: explanation of commands")
                else:
                        print("Remove arguments and try again")
        return


transaction = argparse.ArgumentParser()
transaction.add_argument('--myid')
transaction.add_argument('command', choices=ch.keys())
transaction.add_argument('values', nargs='*')
args = vars(transaction.parse_args())

console(args)

print (args)
