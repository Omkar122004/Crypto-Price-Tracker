import streamlit as st
import requests
import datetime
import matplotlib.pyplot as plt

# ---------------- BINANCE API ---------------- #

def get_crypto_pairs():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    data = requests.get(url).json()

    pairs = {}
    for item in data["symbols"]:
        if item["status"] == "TRADING":
            base = item["baseAsset"]
            quote = item["quoteAsset"]
            symbol = item["symbol"]
            pairs[f"{base}/{quote} ({symbol})"] = symbol
    return pairs


def get_price(symbol):
    url = "https://api.binance.com/api/v3/ticker/price"
    data = requests.get(url, params={"symbol": symbol}).json()
    return float(data["price"])


def get_historical_data(symbol, days):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1d", "limit": days}
    data = requests.get(url, params=params).json()

    history = []
    for item in data:
        dt = datetime.datetime.fromtimestamp(item[0] / 1000)
        close_price = float(item[4])
        history.append((dt, close_price))
    return history


# ---------------- FOREX API FIX ---------------- #

def get_forex_rate(currency):
    """
    Fetch USD → target currency conversion.
    Uses ExchangeRate-API (free, no API key required).
    """
    url = "https://open.er-api.com/v6/latest/USD"

    try:
        data = requests.get(url).json()
        return data["rates"].get(currency, None)
    except:
        return None


# ---------------- STREAMLIT UI ---------------- #

st.set_page_config(page_title="Crypto Price Tracker", layout="wide")
st.title("💹 Crypto Price Tracker (Multi-Currency)")

st.sidebar.header("Options")

# Load crypto list
pairs = get_crypto_pairs()
pair_names = list(pairs.keys())

default_index = next((i for i, p in enumerate(pair_names) if "BTC/USDT" in p), 0)

crypto_name = st.sidebar.selectbox("Choose Crypto Pair:", pair_names, index=default_index)
symbol = pairs[crypto_name]

# Supported currencies
currencies = ["USD", "INR", "EUR", "GBP", "JPY", "AED", "AUD", "CAD", "CNY", "SGD"]
currency = st.sidebar.selectbox("Select Currency:", currencies)

# Days for chart
days = st.sidebar.selectbox("Historical Range:", [7, 30, 90, 180, 365], index=1)

# ---------------- MAIN ACTION ---------------- #

if st.sidebar.button("Show Price"):
    usdt_price = get_price(symbol)

    forex_rate = get_forex_rate(currency)

    if forex_rate is None:
        st.error(f"❌ Could not get forex rate for {currency}")
        st.stop()

    final_price = usdt_price * forex_rate

    st.metric(label=f"{crypto_name} Price ({currency})",
              value=f"{currency} {final_price:,.4f}")

    # Chart
    history = get_historical_data(symbol, days)

    if len(history) > 0:
        dates = [d[0] for d in history]
        prices = [p[1] * forex_rate for p in history]

        plt.figure(figsize=(10, 4))
        plt.plot(dates, prices)
        plt.title(f"{crypto_name} Price History ({currency})")
        plt.xlabel("Date")
        plt.ylabel(f"Price ({currency})")
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
    else:
        st.error("❌ Could not load historical chart data.")
