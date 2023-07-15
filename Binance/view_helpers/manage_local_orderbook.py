"""
Manages a local order book and prints out its best prices.
Based on https://binance-docs.github.io/apidocs/spot/en/#diff-depth-stream

Instructions:
    1. Have binance-connector installed
    2. Define symbol in this file and adjust other fields if needed
    3. python manage_local_order_book.py

"""

from binance.spot import Spot as Client
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from binance.lib.utils import config_logging
import binance
import os
import logging
import json
import asyncio


config_logging(logging, logging.INFO)

symbol = 'BTCUSDT'  # Example: BNBUSDT
base_url = 'https://data-api.binance.vision'
stream_url = 'wss://data-stream.binance.vision'

client = Client(base_url=base_url)
ws_client = SpotWebsocketClient(stream_url=stream_url)

order_book = {
    "lastUpdateId": 0,
    "bids": [],
    "asks": []
}


def get_snapshot():
    """
    Retrieve order book
    """
    try:
        return client.depth(symbol, limit=1)
    except binance.error.ClientError:
        return {"exception": "rate-limited"}


def manage_order_book(side, update):
    """
    Updates local order book's bid or ask lists based on the received update ([price, quantity])
    """

    price, quantity = update

    # price exists: remove or update local order
    for i in range(0, len(order_book[side])):
        if price == order_book[side][i][0]:
            # quantity is 0: remove
            if float(quantity) == 0:
                order_book[side].pop(i)
                return
            else:
                # quantity is not 0: update the order with new quantity
                order_book[side][i] = update
                return

    # price not found: add new order
    if float(quantity) != 0:
        order_book[side].append(update)
        if side == 'asks':
            # asks prices in ascendant order
            order_book[side] = sorted(order_book[side])
        else:
            # bids prices in descendant order
            order_book[side] = sorted(order_book[side], reverse=True)

        # maintain side depth <= 1000
        if len(order_book[side]) > 1000:
            order_book[side].pop(len(order_book[side]) - 1)


def process_updates(message):
    """
    Updates bid and ask orders in the local order book.
    """

    for update in message['b']:
        manage_order_book('bids', update)
    for update in message['a']:
        manage_order_book('asks', update)
    # logging.info("Condition 'U' <= last_update_id + 1 <= 'u' matched! Process diff update")


def message_handler(message):
    """
    Syncs local order book with depthUpdate message's u (Final update ID in event) and U (First update ID in event).
    If synced, then the message will be processed.
    """

    global order_book

    if "depthUpdate" in json.dumps(message):

        last_update_id = order_book['lastUpdateId']


        if message['u'] <= last_update_id:
            return  # Not an update, wait for next message
        # U <= lastUpdateId+1 AND u >= lastUpdateId+1.
        if message['U'] <= last_update_id + 1 <= message['u']:
            order_book['lastUpdateId'] = message['u']

            process_updates(message)
        else:
            logging.info('Out of sync, re-syncing...')
            order_book = get_snapshot()
            # print(order_book['lastUpdateId'])
            print(order_book)


async def listen_ws():
    """
    Listens to the ws to get the updates messages.
    """

    ws_client.start()
    ws_client.diff_book_depth(
        symbol=symbol.lower(),
        id=1,
        speed=1000,
        callback=message_handler,
    )


async def get_best_price():
    """
    Gets best available prices (for bid and ask) every second
    """

    while True:
        if order_book.get('lastUpdateId') > 0:
            print(
                f'Best prices -> bid:{order_book["bids"][0][0]} , ask:{order_book["asks"][0][0]}')
            print(order_book["bids"])
            print(order_book["asks"])
        await asyncio.sleep(10)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(listen_ws(), get_best_price()))
    loop.close()


main()
