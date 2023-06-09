from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import json
import threading
import time

def cache_stream_data_from_stream_buffer_ticker(websocket_api_manager):
    while True:
        if websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(0.01)
        else:
            json_array = json.loads(oldest_stream_data_from_stream_buffer)
            for item in json_array:
                cache.set(item['s'], item, 30)

def cache_stream_data_from_stream_buffer_orderbook(websocket_api_manager, cache_key):
    while True:
        if websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(0.01)
        else:
            cache.set(cache_key, oldest_stream_data_from_stream_buffer, 30)

def launch_ws_thread_for_ticker():
    mini_ticker_manager = BinanceWebSocketApiManager()
    t = threading.Thread(target=cache_stream_data_from_stream_buffer_ticker, args=[mini_ticker_manager], daemon=True)
    t.start()
    miniTicker_arr_stream_id = mini_ticker_manager.create_stream("arr", "!miniTicker")
    time.sleep(1)  # to make sure every refresh there is result


def launch_ws_thread_for_orderbook(ticker_symbol):
    orderbook_manager = BinanceWebSocketApiManager()
    t = threading.Thread(target=cache_stream_data_from_stream_buffer_orderbook, args=[orderbook_manager, f"orderbook_{ticker_symbol}"], daemon=True)
    t.start()
    orderbook_stream_id = orderbook_manager.create_stream("depth20", [ticker_symbol])
    time.sleep(1)  # to make sure every refresh there are result

def index(request):
    return HttpResponse("Hello world. You're at the binance index. Try /mini_tickers_bulk OR /mini_ticker_single/BTCUSDT OR /orderbook/BTCUSDT")

def mini_tickers_bulk(request):
    test_key = cache.get("BTCUSDT", "has expired")
    if test_key == "has expired": launch_ws_thread_for_ticker()
    all_keys = cache.keys("*")
    filtered_minitickers_keys = [x for x in all_keys if not x.startswith("orderbook_")]
    tickers_response = []

    for k in filtered_minitickers_keys:
        cached_result = cache.get(k, "missing")
        if cached_result == "missing": continue
        tickers_response.append(cached_result)

    return JsonResponse(tickers_response, safe=False)

def mini_ticker_single(request, ticker_symbol):
    cached_result = cache.get(ticker_symbol, "has expired")

    if cached_result == "has expired":
        launch_ws_thread_for_ticker()
        cached_result = cache.get(ticker_symbol)
    
    return JsonResponse(cached_result, safe=False)

def orderbook(request, ticker_symbol):
    cached_result = cache.get(f"orderbook_{ticker_symbol}", "has expired")
    
    if cached_result == "has expired":
        launch_ws_thread_for_orderbook(ticker_symbol)
        cached_result = cache.get(f"orderbook_{ticker_symbol}")
        # return HttpResponse("restarting websocket thread...")

    return JsonResponse(json.loads(cached_result))



