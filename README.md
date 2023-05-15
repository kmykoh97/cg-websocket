This readme is incomplete...

To start, run `docker-compose up`

You can read most of the logics in binance/views.py

This project is using https://github.com/LUCIT-Systems-and-Development/unicorn-binance-websocket-api as it's websocket manager

api:
- http://ip:8000/binance/mini_tickers
- http://ip:8000/binance/orderbook/#{symbol} eg http://ip:8000/binance/orderbook/btcusdt

 