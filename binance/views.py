from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from unicorn_binance_websocket_api.manager import BinanceWebSocketApiManager
import json
import threading
import time
from datetime import datetime

def cache_stream_data_from_stream_buffer_ticker():
    websocket_api_manager = BinanceWebSocketApiManager(stream_buffer_maxlen=60)
    miniTicker_arr_stream_id = websocket_api_manager.create_stream("arr", "!miniTicker")

    while True:
        if websocket_api_manager.is_manager_stopping():
            websocket_api_manager.stop_manager_with_all_streams()
            break
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(5)
            oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
            if oldest_stream_data_from_stream_buffer is False:
                websocket_api_manager.stop_manager_with_all_streams()
                break
            else:
                json_array = json.loads(oldest_stream_data_from_stream_buffer)
                cache.set("checkpoint_ticker", datetime.now(), 100)
                cache.set("tickers_all", oldest_stream_data_from_stream_buffer)
                for item in json_array:
                    cache.set(f"ticker_{item['s']}", item, 180)
        else:
            json_array = json.loads(oldest_stream_data_from_stream_buffer)
            cache.set("checkpoint_ticker", datetime.now(), 100)
            cache.set("tickers_all", oldest_stream_data_from_stream_buffer)
            for item in json_array:
                cache.set(f"ticker_{item['s']}", item, 180)

def cache_stream_data_from_stream_buffer_orderbook(ticker_symbol, cache_key):
    websocket_api_manager = BinanceWebSocketApiManager(stream_buffer_maxlen=10)
    orderbook_stream_id = websocket_api_manager.create_stream("depth20", [ticker_symbol])

    while True:
        if websocket_api_manager.is_manager_stopping():
            websocket_api_manager.stop_manager_with_all_streams()
            break
        oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
        cache.set(f"checkpoint_{cache_key}", datetime.now(), 300)
        if oldest_stream_data_from_stream_buffer is False:
            time.sleep(5)
            oldest_stream_data_from_stream_buffer = websocket_api_manager.pop_stream_data_from_stream_buffer()
            if oldest_stream_data_from_stream_buffer is False:
                websocket_api_manager.stop_manager_with_all_streams()
                break
        else:
            cache.set(cache_key, oldest_stream_data_from_stream_buffer, 180)
        time.sleep(3)

def launch_ws_thread_for_ticker():
    t = threading.Thread(target=cache_stream_data_from_stream_buffer_ticker, daemon=True)
    t.start()
    time.sleep(1)  # to make sure every refresh there is result
    
def launch_ws_thread_for_orderbook(ticker_symbol):
    t = threading.Thread(target=cache_stream_data_from_stream_buffer_orderbook, args=[ticker_symbol, f"orderbook_{ticker_symbol}"], daemon=True)
    t.start()
    time.sleep(1)  # to make sure every refresh there is result

def index(request):
    test_key = cache.get("BTCUSDT", "404")

    if test_key == "404":
        return HttpResponseNotFound()
        
    return HttpResponse("Hello world. You're at the binance index. Try /mini_tickers_bulk OR /mini_ticker_single/BTCUSDT OR /orderbook/BTCUSDT")

def checkpoint_ticker_is_new(symbol):
    determinant = cache.get(f"checkpoint_{symbol}", "404")

    if determinant == "404":
        cache.set(f"checkpoint_{symbol}", datetime.now(), 360)
        return True

    return False

def mini_tickers_bulk(request):
    ticker_is_new = checkpoint_ticker_is_new("ticker")
    if ticker_is_new: launch_ws_thread_for_ticker()
    all_keys = cache.keys("*")
    filtered_minitickers_keys = [x for x in all_keys if x.startswith("ticker_")]
    tickers_response = []

    for k in filtered_minitickers_keys:
        cached_result = cache.get(k, "404")
        if cached_result == "404": continue
        tickers_response.append(cached_result)

    return JsonResponse(tickers_response, safe=False)

def mini_ticker_single(request, ticker_symbol):
    ticker_is_new = checkpoint_ticker_is_new("ticker")
    if ticker_is_new: launch_ws_thread_for_ticker()
    cached_result = cache.get(f"ticker_{ticker_symbol}")

    return JsonResponse(cached_result, safe=False)

def orderbook(request, ticker_symbol):
    ticker_is_new = checkpoint_ticker_is_new(f"orderbook_{ticker_symbol}")
    if ticker_is_new: launch_ws_thread_for_orderbook(ticker_symbol)
    cached_result = cache.get(f"orderbook_{ticker_symbol}")

    return JsonResponse(json.loads(cached_result), safe=False)
