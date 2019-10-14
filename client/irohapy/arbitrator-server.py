#!/usr/bin/env python3
#
# Copyright Soramitsu Co., Ltd. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

from time import sleep
import json
import binascii
from iroha import IrohaCrypto as ic
from iroha import Iroha, IrohaGrpc
import os
import sys

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')

IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')

net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))

# Define necessary constants we will need throughout the app

ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY', '72a9eb49c0cd469ed64f653e33ffc6dde475a6b9fd8be615086bce7c44b5a8f8')
ADMIN_PUBLIC_KEY = ic.derive_public_key(ADMIN_PRIVATE_KEY)

GAME_ACCOUNT_ID = 'match@games'

winningCombinations = [
  [0, 1, 2],
  [3, 4, 5],
  [6, 7, 8],
  [0, 3, 6],
  [1, 4, 7],
  [2, 5, 8],
  [0, 4, 7],
  [2, 4, 6]
]

iroha = Iroha(ADMIN_ACCOUNT_ID)


def trace(func):
    """
    A decorator for tracing methods' begin/end execution points
    """

    def tracer(*args, **kwargs):
        name = func.__name__
        print('\tEntering "{}"'.format(name))
        result = func(*args, **kwargs)
        print('\tLeaving "{}"'.format(name))
        return result

    return tracer


@trace
def send_transaction_and_print_status(transaction):
    global net
    hex_hash = binascii.hexlify(ic.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        print(status)


@trace
def process_pending_transactions():
    global net
    q = ic.sign_query(Iroha(GAME_ACCOUNT_ID).query('GetPendingTransactions'), ADMIN_PRIVATE_KEY)
    pending_tx = net.send_query(q)
    for tx in pending_tx.transactions_response.transactions:
        print('creator: {}'.format(tx.payload.reduced_payload.creator_account_id))
        if tx.payload.reduced_payload.creator_account_id == GAME_ACCOUNT_ID:
            # we need do this temporarily, otherwise accept will not reach MST engine
            print('tx: {}'.format(tx))
            del tx.signatures[:]
            print('tx: {}'.format(tx))
            ic.sign_transaction(tx, ADMIN_PRIVATE_KEY)
            send_transaction_and_print_status(tx)
    

@trace
def check_winner():
    """
    Get all the kv-storage entries for userone@domain
    """
    global iroha
    global net
    query = iroha.query('GetAccountDetail', account_id=GAME_ACCOUNT_ID)
    ic.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_detail_response
    print('data: {}'.format(data))
    try:
        asDict = json.loads(data.detail)
        gameState = asDict[GAME_ACCOUNT_ID]['state']
    except:
        print('State doesn''t exist in storage')
        return None

    asNumbers = []
    for x in gameState.split(','):
        if x == 'X':
            asNumbers.append(1)
        else:
            if x == 'O':
                asNumbers.append(-1)
            else:
                asNumbers.append(0)

    sums = [asNumbers[x[0]] + asNumbers[x[1]] + asNumbers[x[2]] for x in winningCombinations]
    maxCombination = max(sums)
    minCombination = min(sums)
    winner = None
    if maxCombination == 3:
        # 'X' won
        winner = 'X'
    else:
        if minCombination == -3:
            # 'O' won
            winner = 'O'
        else:
            try:
                _ = gameState.index('-')
            except ValueError:
            # no more moves possible, hence draw
                winner = 'Nobody'
    print('Account id = {}, state = {}, winner = {}'.format(GAME_ACCOUNT_ID, gameState, winner))
    return winner

# @trace
def write_winner_to_iroha(winner):
    global iroha
    cmds = [
        iroha.command('SetAccountDetail', account_id=ADMIN_ACCOUNT_ID, key='winner', value=winner)
    ]
    tx = iroha.transaction(cmds)
    ic.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

def main():
    while True:
        process_pending_transactions()
        winner = check_winner()
        if winner is not None:
            write_winner_to_iroha(winner)
            break
        sleep(5.0)


if __name__ == '__main__':
    main()
