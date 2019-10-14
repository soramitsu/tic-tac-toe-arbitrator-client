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


# Set up the game
@trace
def prepare_accounts():
    global iroha
    init_cmds = [
        iroha.command('CreateDomain', domain_id='games', default_role='user'),
        iroha.command('CreateAsset', asset_name='bitcoin', domain_id='games', precision=2),
        iroha.command('AddAssetQuantity', asset_id='bitcoin#games', amount='10000'),
        iroha.command('CreateAccount', account_name='match', domain_id='games', public_key=GAME_PUBLIC_KEY),
        iroha.command('CreateAccount', account_name='alice', domain_id='games', public_key=ALICE_PUBLIC_KEY),
        iroha.command('CreateAccount', account_name='bob', domain_id='games', public_key=BOB_PUBLIC_KEY),
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id='alice@games',
                      asset_id='bitcoin#games', description='init top up', amount='1000'),
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id='bob@games',
                      asset_id='bitcoin#games', description='init top up', amount='1000')
    ]
    init_tx = iroha.transaction(init_cmds)
    ic.sign_transaction(init_tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(init_tx)


# @trace
def configure_game_account():
    game_iroha = Iroha(GAME_ACCOUNT_ID)
    game_cmds = [
        game_iroha.command('AddSignatory', account_id=GAME_ACCOUNT_ID, public_key=ADMIN_PUBLIC_KEY),
        game_iroha.command('AddSignatory', account_id=GAME_ACCOUNT_ID, public_key=ALICE_PUBLIC_KEY),
        game_iroha.command('AddSignatory', account_id=GAME_ACCOUNT_ID, public_key=BOB_PUBLIC_KEY),
        game_iroha.command('GrantPermission', account_id='admin@test', permission=can_set_my_account_detail),
        game_iroha.command('GrantPermission', account_id='admin@test', permission=can_set_my_quorum),
        game_iroha.command('GrantPermission', account_id='alice@games', permission=can_set_my_account_detail),
        game_iroha.command('GrantPermission', account_id='alice@games', permission=can_transfer_my_assets),
        game_iroha.command('GrantPermission', account_id='bob@games', permission=can_set_my_account_detail),
        game_iroha.command('GrantPermission', account_id='bob@games', permission=can_transfer_my_assets)
    ]
    game_tx = game_iroha.transaction(game_cmds)
    ic.sign_transaction(game_tx, GAME_PRIVATE_KEY)
    send_transaction_and_print_status(game_tx)


# @trace
def configure_players_accounts():
    alice_iroha = Iroha('alice@games')
    alice_cmds = [
        alice_iroha.command('SetAccountDetail', account_id='alice@games', key='symbol', value='X')
    ]
    alice_tx = alice_iroha.transaction(alice_cmds)
    ic.sign_transaction(alice_tx, ALICE_PRIVATE_KEY)
    send_transaction_and_print_status(alice_tx)

    bob_iroha = Iroha('bob@games')
    bob_cmds = [
        bob_iroha.command('SetAccountDetail', account_id='bob@games', key='symbol', value='O')
    ]
    bob_tx = bob_iroha.transaction(bob_cmds)
    ic.sign_transaction(bob_tx, BOB_PRIVATE_KEY)
    send_transaction_and_print_status(bob_tx)


def init_game():
    global iroha
    cmds = [
        iroha.command('SetAccountDetail', account_id=GAME_ACCOUNT_ID, key='state', value='-,-,-,-,-,-,-,-,-')
    ]
    tx = iroha.transaction(cmds, creator_account=GAME_ACCOUNT_ID, quorum=1)
    ic.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)

    cmds = [
        iroha.command('SetAccountQuorum', account_id=GAME_ACCOUNT_ID, quorum=2)
    ]
    tx = iroha.transaction(cmds)
    ic.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


prepare_accounts()
configure_game_account()
configure_players_accounts()
init_game()
