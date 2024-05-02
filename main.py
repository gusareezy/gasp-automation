from web3 import Web3
from logger import logger

keys = open('keys', 'r').read().split('\n')

gasp_token_address = '0x1317106dd45ff0eb911e9f0af78d63fbf9076f69'
faucet_address = '0x1828eaA3cdE0B2373bc869A19cf5b4804C21752C'
eth_address = '0x1317106Dd45FF0EB911e9F0aF78D63FBF9076f69'
rolldown_address = '0x329d0c4a58b3cefdb40c5513e155228f6cc7b6c5'

chain_name = 'Holesky'
chain_url = 'https://ethereum-holesky-rpc.publicnode.com'
chain_id = '17000'
chain_symbol = 'ETH'

web3 = Web3(Web3.HTTPProvider(chain_url))
logger.info("Connected to Holesky successfully")

class Tx:
    def __init__(self, spender, recipient, value, nonce, gas_price, gas_amount, chain_id):
        self.spender = spender
        self.recipient = recipient
        self.value = value
        self.nonce = nonce
        self.gas_price = gas_price
        self.gas_amount = gas_amount
        self.chainId = chain_id
    def get_tx(self):
        return {
            'from': self.spender,
            'to': self.recipient,
            'value': self.value,
            'nonce': self.nonce,
            'gasPrice': self.gas_price,
            'gas': self.gas_amount,
            'chainId': self.chainId
        }

def send_eth(keys, counter):
    spender = web3.eth.account.from_key(keys[0])
    value = web3.to_wei('0.001', 'ether')
    nonce = web3.eth.get_transaction_count(spender.address)
    gas = web3.eth.gas_price * 2
    gas_amount = 30000

    tx_temp = Tx(spender.address, '', value, nonce, gas, gas_amount, 17000)

    for key in keys[counter:]:
        tx = tx_temp.get_tx()
        tx.update({'to': web3.eth.account.from_key(key).address})
        tx.update({'nonce': web3.eth.get_transaction_count(spender.address)})
        signed_tx = web3.eth.account.sign_transaction(tx, keys[0])
        try:
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            web3.eth.wait_for_transaction_receipt(tx_hash)
        except Exception as err:
            logger.error(err)
            logger.info("TRY AGAIN")
            send_eth(keys, counter)
        counter += 1

        logger.info(f"{spender.address} sent 0.001 ether to {tx['to']} successfully")
def faucet(faucet_addr, key):
    wallet = web3.eth.account.from_key(key)
    faucet_abi = open('faucet-abi', 'r').read()
    _faucet = web3.eth.contract(address=web3.to_checksum_address(faucet_addr), abi=faucet_abi)
    nonce = web3.eth.get_transaction_count(wallet.address)
    faucet_call = _faucet.functions.requestTokens().build_transaction({
        "from": wallet.address,
        "nonce": nonce
    })
    signed_tx = web3.eth.account.sign_transaction(faucet_call, private_key=key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as err:
        logger.error(err)
        logger.info("TRY AGAIN")
        faucet(faucet_addr, key)
    logger.info(f"{wallet.address} claimed GASP successfully")

def approve(eth_addr, rolldown_addr, key):
    wallet = web3.eth.account.from_key(key)
    token_abi = open('token-abi', 'r').read()
    token_contract = web3.eth.contract(address=eth_addr, abi=token_abi)
    nonce = web3.eth.get_transaction_count(wallet.address)
    approve_call = token_contract.functions.approve(spender=f"{web3.to_checksum_address(rolldown_addr)}", amount=web3.to_wei(10000, 'ether')).build_transaction({
        "from": wallet.address,
        "nonce": nonce
    })
    signed_tx = web3.eth.account.sign_transaction(approve_call, private_key=key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as err:
        logger.error(err)
        logger.info("TRY AGAIN")
        approve(eth_addr, rolldown_addr, key)
    logger.info(f"{wallet.address} approved for deposit")

def deposit(rolldown_addr, gasp_addr, key):
    wallet = web3.eth.account.from_key(key)
    abi = open("rolldown-abi", 'r').read()
    contract = web3.eth.contract(address=web3.to_checksum_address(rolldown_addr), abi=abi)
    amount = web3.to_wei(10000, 'ether')
    nonce = web3.eth.get_transaction_count(wallet.address)
    deposit_call = contract.functions.deposit(tokenAddress=f'{web3.to_checksum_address(gasp_addr)}', amount=amount).build_transaction({
        "from": wallet.address,
        "nonce": nonce
    })
    signed_tx = web3.eth.account.sign_transaction(deposit_call, key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
    except Exception as err:
        logger.error(err)
        logger.info("TRY AGAIN")
        deposit(rolldown_addr, gasp_addr, key)
    logger.info(f"{wallet.address} deposited to https://holesky.gasp.xyz/ successfully")

def main():
    send_eth(keys, counter=1)
    for key in keys[1:]:
        faucet(faucet_addr=faucet_address, key=key)
        approve(eth_addr=eth_address, rolldown_addr=rolldown_address, key=key)
        deposit(rolldown_addr=rolldown_address, gasp_addr=gasp_token_address, key=key)

main()