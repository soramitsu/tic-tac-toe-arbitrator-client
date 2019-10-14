#!/usr/bin/env python3
#
# Copyright Soramitsu Co., Ltd. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

import os
import binascii
from iroha import Iroha, IrohaCrypto, IrohaGrpc
from iroha.primitive_pb2 import can_set_my_account_detail, can_transfer_my_assets
import sys

if sys.version_info[0] < 3:
    raise Exception('Python 3 or a more recent version is required.')


IROHA_HOST_ADDR = os.getenv('IROHA_HOST_ADDR', '127.0.0.1')
IROHA_PORT = os.getenv('IROHA_PORT', '50051')

ADMIN_ACCOUNT_ID = os.getenv('ADMIN_ACCOUNT_ID', 'admin@test')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY', '72a9eb49c0cd469ed64f653e33ffc6dde475a6b9fd8be615086bce7c44b5a8f8')
ADMIN_PUBLIC_KEY = '4a60a53785ab3aeed09fc57c9360c37597ded473efda0826bace79aa08522e48'

USER_ACCOUNT_ID = 'user@test'
USER_PRIVATE_KEY = 'f4b9fd3aa77d3979e13ba80e638de5e771e298c97150efa9a3c81d4beac6cd54'
USER_PUBLIC_KEY = 'e3ca75053bedbdc4fbaf6c52294b72de3973ab83eab0646f4d6c73f191c3835b'

EXPLORER_DOMAIN_ID = 'explorer'
EXPLORER_ACCOUNT_ID = 'admin'
EXPLORER_PUBLIC_KEY = '2c72cee27724a6fc8df70b950885233935413f91df57a92ef185941c82f1bf11'


iroha = Iroha(ADMIN_ACCOUNT_ID)
# iroha = Iroha(USER_ACCOUNT_ID)
net = IrohaGrpc('{}:{}'.format(IROHA_HOST_ADDR, IROHA_PORT))

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
    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    for status in net.tx_status_stream(transaction):
        print(status)


@trace
def create_domain(domainID, defaultRole='user'):
    """
    Creates domain @domainID
    """
    commands = [
        iroha.command('CreateDomain', domain_id=domainID, default_role=defaultRole),
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def create_asset(domainID, asset):
    """
    Creates asset @asset#domain with precision 2
    """
    tx = iroha.transaction([
        iroha.command('CreateAsset', asset_name=asset, domain_id=domainID, precision=2)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def create_domain_and_asset(domainID, asset):
    """
    Creates domain @domainID and asset $asset#domain
    """
    commands = [
        iroha.command('CreateDomain', domain_id=domainID, default_role='user'),
        iroha.command('CreateAsset', asset_name=asset, domain_id=domainID, precision=2)
    ]
    tx = IrohaCrypto.sign_transaction(
        iroha.transaction(commands), ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def add_coin_to_admin(asset_id, amount):
    """
    Add @amount units of 'asset_id' to 'admin@test'
    """
    tx = iroha.transaction([
        iroha.command('AddAssetQuantity', asset_id=asset_id, amount=amount)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def create_account(acc_name, domain_id, public_key):
    """
    Create account
    """
    tx = iroha.transaction([
        iroha.command('CreateAccount', account_name=acc_name, domain_id=domain_id,
                      public_key=public_key)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def transfer_asset(dest_id, asset_id, amount):
    """
    Transfer '${amount}' of '${asset_id}' from 'admin@test' to '${dest_id}'
    """
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=dest_id,
                      asset_id=asset_id, description='Transfer from admin', amount=amount)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def transfer_other_asset(source_id, dest_id, asset_id, amount):
    """
    Transfer '${amount}' of '${asset_id}' from '${source_id}' to '${dest_id}'. Requires 'root' permission
    """
    tx = iroha.transaction([
        iroha.command('TransferAsset', src_account_id=source_id, dest_account_id=dest_id,
                      asset_id=asset_id, description='Transfer other asset', amount=amount)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def grant_transfer_assets_permission(grantor, grantee, private_key):
    """
    Make '${grantee}' able to transfer '${grantor}' assets
    """
    tx = iroha.transaction([
        iroha.command('GrantPermission', account_id=grantee, permission=can_transfer_my_assets)
    ], creator_account=grantor)
    IrohaCrypto.sign_transaction(tx, private_key)
    send_transaction_and_print_status(tx)


@trace
def set_account_detail(account_id, key, value):
    """
    Add or change entry with key @key to have value @value in @account_id's key-value storage
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail', account_id=account_id, key=key, value=value)
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def set_age_to_user(account_id):
    """
    Set age to @account_is by admin@test
    """
    tx = iroha.transaction([
        iroha.command('SetAccountDetail', account_id=account_id, key='age', value='18')
    ])
    IrohaCrypto.sign_transaction(tx, ADMIN_PRIVATE_KEY)
    send_transaction_and_print_status(tx)


@trace
def get_coin_info(asset_id):
    """
    Get asset info for $asset_id
    :return:
    """
    query = iroha.query('GetAssetInfo', asset_id=asset_id)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.asset_response.asset
    print('Asset id = {}, precision = {}'.format(data.asset_id, data.precision))


@trace
def get_account_assets(account_id):
    """
    List all the assets of $account_id
    """
    query = iroha.query('GetAccountAssets', account_id=account_id)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    for asset in data:
        print('Asset id = {}, balance = {}'.format(asset.asset_id, asset.balance))


@trace
def get_account_details(account_id):
    """
    Get all the kv-storage entries for userone@domain
    """
    query = iroha.query('GetAccountDetail', account_id=account_id)
    IrohaCrypto.sign_query(query, ADMIN_PRIVATE_KEY)

    response = net.send_query(query)
    data = response.account_detail_response
    print('Account id = {}, details = {}'.format(account_id, data.detail))



# Commands examples
create_domain('ecb')
create_asset('ecb', 'eur')
create_domain_and_asset('cbr', 'rub')

get_coin_info('eur#ecb')
get_coin_info('rub#cbr')
get_coin_info('usd#test')

add_coin_to_admin('usd#test', '10000')
add_coin_to_admin('eur#ecb', '20000')
add_coin_to_admin('rub#cbr', '58236.12')

create_account('user', 'test', USER_PUBLIC_KEY)
set_age_to_user('user@test')
set_account_detail('admin@test', 'name', 'Admin')

transfer_asset('user@test', 'eur#ecb', '580.39')
transfer_asset('user@test', 'rub#cbr', '2020.83')


print('admin@test assets:')
get_account_assets("admin@test")
print('user@test assets:')
get_account_assets("user@test")


grant_transfer_assets_permission('user@test', 'admin@test', USER_PRIVATE_KEY)
transfer_other_asset('user@test', 'admin@test', 'eur#ecb', '14.20')

print('admin@test assets:')
get_account_assets("admin@test")
print('user@test assets:')
get_account_assets("user@test")

create_domain(EXPLORER_DOMAIN_ID, 'admin')
create_account(EXPLORER_ACCOUNT_ID, EXPLORER_DOMAIN_ID, EXPLORER_PUBLIC_KEY)

print('done')
