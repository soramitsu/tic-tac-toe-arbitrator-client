#!/usr/bin/env python3
#
# Copyright Soramitsu Co., Ltd. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

import binascii
from iroha import IrohaCrypto as ic
from iroha import Iroha, IrohaGrpc
from iroha.primitive_pb2 import can_set_my_account_detail, can_transfer_my_assets, can_set_my_quorum
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
GAME_PRIVATE_KEY = '9b965ebbd194dc538735310740e6667cb8222811c5e4e8e917a6fbe77deeb6dc'
GAME_PUBLIC_KEY = ic.derive_public_key(GAME_PRIVATE_KEY)

ALICE_ACCOUNT_ID = 'alice@games'
ALICE_PRIVATE_KEY = '7384819f00d820e291f0dc9f1fce827d9f94ad508bf5252fb310916465b94f17'
ALICE_PUBLIC_KEY = ic.derive_public_key(ALICE_PRIVATE_KEY)

BOB_ACCOUNT_ID = 'bob@games'
BOB_PRIVATE_KEY = '4125f29b841b6bab5ab9bc830e19629e86a51fcb77c9554fdf3d8af41780573b'
BOB_PUBLIC_KEY = ic.derive_public_key(BOB_PRIVATE_KEY)


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
def send_batch_and_print_status(transactions):
    global net
    net.send_txs(transactions)
    for tx in transactions:
        hex_hash = binascii.hexlify(ic.hash(tx))
        print('\t' + '-' * 20)
        print('Transaction hash = {}, creator = {}'.format(
            hex_hash, tx.payload.reduced_payload.creator_account_id))
        for status in net.tx_status_stream(tx):
            print(status)


# @trace
def make_move(account_id, privateKey, new_state):
    iroha = Iroha(account_id)
    cmds = [
        iroha.command('SetAccountDetail', account_id=GAME_ACCOUNT_ID, key='state', value=new_state)
    ]
    tx = iroha.transaction(cmds, creator_account=GAME_ACCOUNT_ID, quorum=2)
    ic.sign_transaction(tx, privateKey)
    send_transaction_and_print_status(tx)

# state is [-,-,-,-,-,-,-,-,-]
make_move('alice@games', ALICE_PRIVATE_KEY, '[X,-,-,-,-,-,-,-,-]')
make_move('bob@games', BOB_PRIVATE_KEY, '[X,-,-,-,O,-,-,-,-]')
make_move('alice@games', ALICE_PRIVATE_KEY, '[X,-,X,-,O,-,-,-,-]')
make_move('bob@games', BOB_PRIVATE_KEY, '[X,O,X,-,O,-,-,-,-]')
make_move('alice@games', ALICE_PRIVATE_KEY, 'X,O,X,-,O,-,X,-,-')
make_move('bob@games', BOB_PRIVATE_KEY, 'X,O,X,-,O,-,X,O,-')
