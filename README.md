# Brief agenda for the "Getting started with Iroha" talk at Hyperledger bootcamp in Moscow


### Introduction
What is Iroha, why it is there, how does it stand out of the crowd and why do we care at all


### Main architectural aspects
Things we usually mention when speaking about Iroha:
- transaction pipeline
- consensus
- cryptographic libs
- commands and queries
- multisig accounts and transactioins

and other things we will be mentioning real soon like
- smart-contracts,
- python based TUI,
- BFT consensus property etc.


### Step-by-step walkthrough bringing up the network

#### Prerequisites
Have docker and docker-compose installed

1. Get Iroha docker image
```bash
docker pull hyperledger/iroha:1.1.0
```
2. Create local workfolders for block stores
3. Inspect ```docker-compose.yml``` and peers' config file
4. (optional) Export postgres ports 
```
ports:
  - 5432:5432
```
5. Walking through the ```genesis.block```: understanding domains, roles, accounts, assets etc.
6. Where should I get the keypairs?
	- either use a ready-made ones or 
	- generate a keypair with iroha-cli:
```
$ docker run -t -v $(pwd):/opt/iroha_data --entrypoint /bin/bash hyperledger/iroha:1.1.0 -c "iroha-cli -account_name $USER -new_account"
```
  or, if the network is already running, in a bit simpler form
```
$ docker exec -t $IROHA_CONTAINER_NAME iroha-cli -account_name user -new_account
```
7. Finally, run the network


### How do I interact with Iroha?
There are many client libraries available. Some are up to date, others may not be.
#### Python client 
##### Prerequsite: have python3 installed
1. Install python client:
```
$ pip3 install iroha
```
2. To get the feel of it clone the official repository
```
git clone https://github.com/hyperledger/iroha-python
```
  and play with eamples; 
  However, for our demo we will use modified scripts from the ```./client/irohapy``` folder of this repo. More on this further down.


### Monitoring Iroha bu means of the Hyperledger Explorer
#### Prerequisites: Node.js, npm/yarn
[not today, folks]
Anyway, the code is available at
```
$ git clone https://github.com/turuslan/iroha-explorer-backend.git
```
Instructions on how to build are in README. However, there are a few things to note.


### Back to the point
1. The idea behind the demo: why at all we need an "arbitrator" to play tic-tac-toe? (Answer: we want to see Iroha in action, demonstrate multisig concept)
2. Making necessary preparations on the ledger side:
- create domain for the game, and accounts for players and the game (a word about keypairs again - have a bunch upfront) 
- manipulate permissions and add signatorees to enable multisig, deposit some assets to the game account (optional)
To do all the above we could either:
- use client API (python)
- inserte commands directly in genesis.block
N.B.: in the latter case make sure the docker volumes with the old block stores are removed, otherwise genesis block will be ignored.
- run the "arbitrator" server to listen and process multisig transactions.

#### But how can we actually play the game?
- Initial idea: download beautiful UI specially tailored from Iroha JS wallet for the purpose of the tic-tac-toe game
```
git clone https://github.com/soramitsu/tic-tac-toe-player-client.git
```
The latter, in turn, makes use of the ```Iroha-helpers``` JS library which does all communictaion with Iroha:
```
https://github.com/soramitsu/iroha-helpers
```
The description in the repo gives the idea of how commands and queries can be executed.

! Compare with python client. Which one is more user-friendly?

- build the Vue.js application
#### Prerequisites: Node.js and yarn installed
- in the UI code, note where and how transactions are created and sent, and how the status stream is handled
- configure the grpc web proxy (recalling the Iroha ```docker-compose.yml``` file)
- run the dev server
```
$ yarn serve
```
- make the first move...

(unfortunately, the GUI is not yet fully functional due to a small bug)

Not a big deal - nothing can stop us from playing. We continue with python client.

#### Things to note
- Current implementation of the multisig logig is overly simple: all the transactions get approved
- The implementation assumes players are being honest and not trying to cheat by submitting invalid game state updates or making a move more than one time in a raw: to tolerate malicious players behaviour we need to implement extra logic for the arbitrator:
  - state update validation
  - sorting pending MST by timestamp and processing the oldest first.
 
But this is already beyond the scope of this introductory talk.
