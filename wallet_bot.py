# len(amount) in wei:
#   18 digits: less than 1 ETH (not great!)
#   19 digits: 1-9 ETH (stay within this range, ideally 5 or less ETH)
#   20 digits: 10-99 ETH (bad!)

import sys
import time
from web3 import Web3
import json

# RPC endpoint of your Ethereum node
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

class WalletBot:
    # addresses passed as {addr, key}
    def __init__(self, main_address, relief_address, eth_lower_limit, eth_upper_limit, testing=False):
        self.main_address = main_address
        self.relief_address = relief_address

        if testing == False:
            self.main_balance = str(w3.eth.get_balance(main_address["addr"]))
            self.relief_balance = str(w3.eth.get_balance(relief_address["addr"]))
        else:
            self.main_balance = '2500000000010000001' #'7172839283728172817'
            self.relief_balance = '3232323456764322234'

        self.last_main_balance = ''
        self.last_relief_balance = ''
        self.eth_upper_limit = eth_upper_limit  # around 5 ETH
        self.eth_lower_limit = eth_lower_limit  # around 2 ETH

        self.tx_defund_main = False
        self.tx_in_progress = False
        self.tx_amount = 0 # always in wei, str

    def update_balances(self):
        self.main_balance = str(w3.eth.get_balance(self.main_address["addr"]))
        self.relief_balance = str(w3.eth.get_balance(self.relief_address["addr"]))

    # amount in wei
    # addr object
    # currently failing for some reason even though Etherscan reports correct balances....
    def send_balance(self, addr_from, addr_to): 
        if self.tx_in_progress and self.tx_amount != 0:
            tx = {"from": addr_from["addr"], "to": addr_to["addr"], "value": int(self.tx_amount)}
            print("Sending " + self.tx_amount + " wei to " + addr_to["addr"])
            w3.geth.personal.send_transaction(tx, addr_from["key"])
            print("Updating balances...")
            print("-")
            self.update_balances() 
            # print("Balances updated.")
            # print("Main address: " + self.main_address["addr"])
            # print("Main address balance: \n" + self.main_balance + " wei")
            # print("Relief address: " + self.relief_address["addr"])
            # print("Relief address balance: \n" + self.relief_balance + " wei")
            self.tx_amount = 0
            self.tx_in_progress = False

    def handle_main_wallet(self):
        # balance = str(w3.eth.get_balance(w3.toChecksumAddress(address)))
        if len(self.main_balance) > 18:
            if len(self.main_balance) == 19:
                balance_float = float(self.main_balance[0] + '.' + self.main_balance[1:19])
                if balance_float > self.eth_upper_limit:
                    self.tx_in_progress = True
                    self.tx_defund_main = True
                    # d_wei = balance_float - self.eth_upper_limit
                    # d_wei = float(str(int(self.main_balance[0]) - self.eth_upper_limit) + '.' + self.main_balance[1:19])
                    d_wei = str(int(self.main_balance[0]) - self.eth_upper_limit)  + self.main_balance[1:19]
                    self.tx_amount = d_wei.strip("0")
                    # self.send_balance(self.main_address, self.relief_address, d_wei)
                    # send d_wei to relief_address
                else:
                    if balance_float <= self.eth_lower_limit:
                        if balance_float <= self.eth_lower_limit - 1:
                            self.tx_in_progress = True
                            # find eth_upper_limit - eth_lower_limit ETH
                            # 4000000000000000000 wei
                            self.tx_amount = '4000000000000000000'
                        else:
                            self.tx_in_progress = True
                            # fund eth_lower_limit + 1 ETH
                            # 3000000000000000000 wei
                            self.tx_amount = '3000000000000000000'
                    elif balance_float > self.eth_lower_limit:
                        if balance_float >= self.eth_lower_limit + 1 and balance_float < 2 * self.eth_lower_limit:
                            self.tx_in_progress = True
                            # 1000000000000000000 wei
                            self.tx_amount = '1000000000000000000'
                        elif balance_float <= self.eth_lower_limit + 1:
                            self.tx_in_progress = True
                            # 2000000000000000000 wei
                            self.tx_amount = '2000000000000000000'
            else:
                pass
                # panic! too much ETH!
        else:
            self.tx_in_progress = True
            # fund ETH IMMEDIATELY from relief_address
            # 5000000000000000000 wei
            self.tx_amount = '4000000000000000000'
        
        # pass tx handling to self.send_balance
        if self.tx_in_progress:
            if self.tx_defund_main: # defunding main wallet
                print("Defunding main wallet: " + self.tx_amount + " wei")
                # self.main_balance = str(int(self.main_balance) - int(self.tx_amount))
                self.send_balance(self.main_address, self.relief_address)
                self.tx_defund_main = False
            else:
                print("Funding main wallet: " + self.tx_amount + " wei")
                # self.main_balance = str(int(self.main_balance) + int(self.tx_amount))
                self.send_balance(self.relief_address, self.main_address)

if __name__ == "__main__":
    running = True
    testing = False
    # get limit args or read from JSON config
    eth_lower_limit = 2
    eth_upper_limit = 5

    bot = ''
    addrs = []

    # first two entries should be main wallet, all next 2 entries are relief wallets
    try:
        if sys.argv[1] == "--testing":
            addrs.append({"addr": "0xtest", "key": "test"})
            addrs.append({"addr": "0xtest", "key": "test"})
            testing = True

        else:
            with open(sys.argv[1], "r") as f:
                lines = f.readlines()

                if len(lines) <= 3:
                    print("Must provide at least two addresses for main and relief wallets. Exiting.")
                    sys.exit()

                for i in range(0, len(lines), 2):
                    addr_obj = {}
                    addr_obj["addr"] = w3.toChecksumAddress(lines[i].replace("\n", ""))
                    addr_obj["key"] = lines[i + 1].replace("\n", "")
                    addrs.append(addr_obj)

        bot = WalletBot(addrs[0], addrs[1], eth_lower_limit, eth_upper_limit, testing=testing)
        print("Wallet bot successfully started!")
        print("ETH lower limit: " + str(eth_lower_limit) + "; ETH upper limit: " + str(eth_upper_limit))

    except Exception as e:
        print("Error while opening or reading key file. Exiting.") 
        print(e)
        sys.exit()

    try:
    	while running:
            while bot.last_main_balance == bot.main_balance and bot.last_relief_balance == bot.relief_balance:
                bot.update_balances()

            bot.last_main_balance = bot.main_balance
            bot.last_relief_balance = bot.relief_balance
            # if bot.last_main_balance != bot.main_balance and bot.last_relief_balance != bot.relief_balance:
            print("Main address: " + addrs[0]["addr"])
            print("Main address balance: \n" + bot.main_balance + " wei")
            print("Relief address: " + addrs[1]["addr"])
            print("Relief address balance: \n" + bot.relief_balance + " wei")
            print("-")

            if bot.tx_in_progress == False:
                bot.handle_main_wallet()

            time.sleep(.2)

    except Exception as e:
        print("Exception encountered:")
        print(e)
