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
import os
import logging
import json
import asyncio



def get_snapshot(symbol):
    """
    Retrieve order book
    """
    
    base_url = 'https://data-api.binance.vision'
    client = Client(base_url=base_url)
    return client.depth(symbol, limit=5000)


def manage_order_book(side, update, order_book):
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

        # maintain side depth <= 5000
        if len(order_book[side]) > 5000:
            order_book[side].pop(len(order_book[side]) - 1)

def message_handler_v2(message, order_book_old, symbol):
    """
    Syncs local order book with depthUpdate message's u (Final update ID in event) and U (First update ID in event).
    If synced, then the message will be processed.
    """

    order_book = order_book_old

    if "depthUpdate" in json.dumps(message):
        last_update_id = order_book['lastUpdateId']
        message = message["data"]
        
        if message['u'] <= last_update_id:
            return  # Not an update, wait for next message
        if message['U'] <= last_update_id + 1 <= message['u']:
            order_book['lastUpdateId'] = message['u']
            for update in message['b']:
                manage_order_book('bids', update, order_book)
            for update in message['a']:
                manage_order_book('asks', update, order_book)
        else:
            logging.info('Out of sync, re-syncing...')
            order_book = get_snapshot(symbol)
        
        return order_book


def ManageLocalOrderBookV2(ticker_symbol, message, order_book):
    temp = message_handler_v2(message, order_book, ticker_symbol)
    return temp
