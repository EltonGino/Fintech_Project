# ml_models.py

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import statsmodels.api as sm
from sklearn.metrics import mean_squared_error, mean_absolute_error

# ARIMA Forecast
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ARIMA Forecast with Prediction Intervals
def arima_forecast(data, steps=10, alpha=0.05):
    model = ARIMA(data['close'], order=(5, 1, 0))
    model_fit = model.fit()

    # Forecast with intervals
    forecast_result = model_fit.get_forecast(steps=steps)
    forecast = forecast_result.predicted_mean
    conf_int = forecast_result.conf_int(alpha=alpha)

    forecast_dates = pd.date_range(data['timestamp'].iloc[-1], periods=steps + 1, freq='D')[1:]

    # Calculate metrics
    actuals = data['close'][-steps:] if len(data['close']) >= steps else data['close']
    mse = mean_squared_error(actuals, forecast[:len(actuals)])
    mae = mean_absolute_error(actuals, forecast[:len(actuals)])

    return pd.DataFrame({"Date": forecast_dates, "Forecast": forecast,
                         "Lower Bound": conf_int.iloc[:, 0], "Upper Bound": conf_int.iloc[:, 1]}), mse, mae


# Prophet Forecast with Prediction Intervals
def prophet_forecast(data, periods=10, interval_width=0.95):
    df = data[['timestamp', 'close']].rename(columns={'timestamp': 'ds', 'close': 'y'})
    model = Prophet(interval_width=interval_width)
    model.fit(df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    # Calculate metrics
    actuals = data['close'][-periods:] if len(data['close']) >= periods else data['close']
    forecasted_values = forecast['yhat'].tail(periods)
    mse = mean_squared_error(actuals, forecasted_values)
    mae = mean_absolute_error(actuals, forecasted_values)

    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).rename(
        columns={'ds': 'Date', 'yhat': 'Forecast', 'yhat_lower': 'Lower Bound', 'yhat_upper': 'Upper Bound'}
    ), mse, mae


# LSTM Forecast (no intervals as it is complex for this model type)
def lstm_forecast(data, steps=10):
    df = data['close'].values
    df = df.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=(0, 1))
    df_scaled = scaler.fit_transform(df)

    if len(df_scaled) < 60:
        raise ValueError("Not enough data for LSTM. Minimum 60 data points required.")

    X, y = [], []
    for i in range(60, len(df_scaled) - steps):
        X.append(df_scaled[i - 60:i, 0])
        y.append(df_scaled[i:i + steps, 0])

    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(X.shape[1], 1)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(steps))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=5, batch_size=16, verbose=0)

    last_sequence = df_scaled[-60:]
    last_sequence = np.reshape(last_sequence, (1, last_sequence.shape[0], 1))
    prediction = model.predict(last_sequence)
    prediction = scaler.inverse_transform(prediction).flatten()

    forecast_dates = pd.date_range(data['timestamp'].iloc[-1], periods=steps + 1, freq='D')[1:]
    actuals = data['close'][-steps:] if len(data['close']) >= steps else data['close']
    mse = mean_squared_error(actuals, prediction[:len(actuals)])
    mae = mean_absolute_error(actuals, prediction[:len(actuals)])

    return pd.DataFrame({"Date": forecast_dates, "Forecast": prediction}), mse, mae