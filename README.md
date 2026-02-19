 Structure du Projet

```
trading_bot/
│
├── data_collection.py
├── feature_engineering.py
├── model_training.py
├── predict.py
├── backtest.py
├── risk_manager.py
├── broker_api.py
├── config.py
└── main.py
```

1. data_collection.py

```python
import requests
import pandas as pd

def get_historical_prices(symbol='XAU/USDT', interval='1h', limit=1000):
    data = []
    for _ in range(3):  # Pour récupérer plusieurs lots de données historiques
        url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
        response = requests.get(url)
        data.extend(response.json())
    
    df = pd.DataFrame(data, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms')
    df.set_index('Open Time', inplace=True)
    df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
    
    return df
```
 2. feature_engineering.py

```python
import ta  

def add_indicators(df):
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['volatility'] = df['Close'].pct_change().rolling(10).std()
    
    return df
```

 3. model_training.py

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

def prepare_data_for_model(df):
    df.dropna(inplace=True)
    X = df[['RSI', 'SMA_20', 'SMA_50', 'volatility']]
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
    df = df.iloc[:-1]  # Supprimer la dernière ligne pour éviter la cible incorrecte
    
    split = int(len(df) * 0.8)
    X_train = X[:split]
    X_test = X[split:]
    y_train = df['target'][:split]
    y_test = df['target'][split:]
    
    return X_train, X_test, y_train, y_test

def train_model(X_train, y_train):
    model = LogisticRegression()
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    print(f"Précision du modèle : {accuracy:.2f}")
```

4. predict.py

```python
import joblib

def predict(input_data):
    model = joblib.load("model.pkl")
    return model.predict(input_data)
```

5. backtest.py

```python
def backtest_strategy(df, model, initial_capital=10000):
    capital = initial_capital
    position = 0
    for index, row in df.iterrows():
        prediction = model.predict([[row['RSI'], row['SMA_20'], row['SMA_50'], row['volatility']]])[0]
        if prediction == 1 and capital > 0:  # Acheter
            position = capital / row['Close']
            capital = 0
        elif prediction == 0 and position > 0:  # Vendre
            capital = position * row['Close']
            position = 0
    return capital
```

 6. risk_manager.py

```python
class RiskManager:
    def __init__(self, risk_per_trade):
        self.risk_per_trade = risk_per_trade

    def calculate_position_size(self, account_balance, stop_loss_distance):
        risk_amount = account_balance * self.risk_per_trade
        position_size = risk_amount / stop_loss_distance
        return position_size
```

7. broker_api.py

```python
import requests

class BrokerAPI:
    def __init__(self, api_key):
        self.api_key = api_key

    def place_order(self, symbol, quantity, order_type='MARKET'):
        # Intégration de l'API du broker pour passer un ordre
        pass  # Ajouter la logique d'envoi d'ordres ici
```

 8. config.py

```python
SYMBOL = "BTCUSDT"
RISK_PER_TRADE = 0.02
INITIAL_CAPITAL = 10000
```

9. main.py

```python
from data_collection import get_historical_prices
from feature_engineering import add_indicators
from model_training import prepare_data_for_model, train_model, evaluate_model
from backtest import backtest_strategy
import joblib

def main():
    df = get_historical_prices()
    df = add_indicators(df)
    
    X_train, X_test, y_train, y_test = prepare_data_for_model(df)
    
    model = train_model(X_train, y_train)
    evaluate_model(model, X_test, y_test)
    
    joblib.dump(model, "model.pkl")  # Sauvegarde du modèle

    # Backtest
    final_capital = backtest_strategy(df, model)
    print(f"Capital final après backtest : {final_capital:.2f}")

if __name__ == "__main__":
    main()
```
