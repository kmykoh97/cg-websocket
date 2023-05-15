from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("mini_tickers", views.mini_tickers, name="mini_tickers"),
    path("orderbook/<str:ticker_symbol>/", views.orderbook, name="orderbook")
]
