from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import json
import threading
import time

def cache_stream_data_from_stream_buffer(websocket_api_manager, cache_key):
    while True:
        if websocket_api_manager.is_manager_stopping():
            exit(0)
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(0.01)
        else:
            cache.set(cache_key, oldest_stream_data_from_stream_buffer, 30)

def index(request):
    return HttpResponse("Hello, world. You're at the binance index. Try /mini_tickers")

def mini_tickers(request):
    cached_result = cache.get("mini_tickers", "has expired")

    if cached_result == "has expired":
        mini_ticker_manager = BinanceWebSocketApiManager()
        t = threading.Thread(target=cache_stream_data_from_stream_buffer, args=[mini_ticker_manager, "mini_tickers"], daemon=True)
        t.start()
        miniTicker_arr_stream_id = mini_ticker_manager.create_stream("arr", "!miniTicker")
        return HttpResponse("restarting websocket thread...")

    return JsonResponse(json.loads(cached_result), safe=False)

def orderbook(request, ticker_symbol):
    cached_result = cache.get(f"orderbook_{ticker_symbol}", "has expired")
    
    if cached_result == "has expired":
        orderbook_manager = BinanceWebSocketApiManager()
        t = threading.Thread(target=cache_stream_data_from_stream_buffer, args=[orderbook_manager, f"orderbook_{ticker_symbol}"], daemon=True)
        t.start()
        orderbook_stream_id = orderbook_manager.create_stream("depth", [ticker_symbol])
        return HttpResponse("restarting websocket thread...")

    return JsonResponse(json.loads(cached_result))



