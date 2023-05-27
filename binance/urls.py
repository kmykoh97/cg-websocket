from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("mini_tickers_bulk", views.mini_tickers_bulk, name="mini_tickers_bulk"),
    path("mini_ticker_single/<str:ticker_symbol>/",views.mini_ticker_single, name="mini_ticker_single"),
    path("orderbook/<str:ticker_symbol>/", views.orderbook, name="orderbook")
]
