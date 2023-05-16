from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import json
import threading
import time

def cache_stream_data_from_stream_buffer_orderbook(websocket_api_manager, cache_key):
    while True:
        if websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(0.01)
        else:
            cache.set(cache_key, oldest_stream_data_from_stream_buffer, 30)


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

def index(request):
    return HttpResponse("Hello, world. You're at the binance index. Try /mini_tickers")

def mini_tickers(request):
    def launch_ws_thread():
        mini_ticker_manager = BinanceWebSocketApiManager()
        t = threading.Thread(target=cache_stream_data_from_stream_buffer_ticker, args=[mini_ticker_manager], daemon=True)
        t.start()
        miniTicker_arr_stream_id = mini_ticker_manager.create_stream("arr", "!miniTicker")
        time.sleep(1)  # to make sure every refresh there is result
        
    test_key = cache.get("BTCUSDT", "has expired")
    if test_key == "has expired": launch_ws_thread()
    all_keys = cache.keys("*")
    filtered_minitickers_keys = [x for x in all_keys if not x.startswith("orderbook_")]
    tickers_response = []

    for k in filtered_minitickers_keys:
        cached_result = cache.get(k, "missing")
        if cached_result == "missing": continue
        tickers_response.append(cached_result)

    return JsonResponse(tickers_response, safe=False)

def orderbook(request, ticker_symbol):
    cached_result = cache.get(f"orderbook_{ticker_symbol}", "has expired")
    
    if cached_result == "has expired":
        orderbook_manager = BinanceWebSocketApiManager()
        t = threading.Thread(target=cache_stream_data_from_stream_buffer_orderbook, args=[orderbook_manager, f"orderbook_{ticker_symbol}"], daemon=True)
        t.start()
        orderbook_stream_id = orderbook_manager.create_stream("depth", [ticker_symbol])
        time.sleep(1)  # to make sure every refresh there are result
        cached_result = cache.get(f"orderbook_{ticker_symbol}")
        # return HttpResponse("restarting websocket thread...")

    return JsonResponse(json.loads(cached_result))



