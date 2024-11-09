import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import yfinance as yf
from datetime import datetime, timedelta
from ml_models import arima_forecast, prophet_forecast, lstm_forecast  # Importa funções de ML/DL

# Inicializa banco de dados
def init_database():
    conn = sqlite3.connect('stock_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            timestamp TEXT,
            ticker TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (timestamp, ticker)
        )
    ''')
    conn.commit()
    conn.close()

# Carregar dados do banco de dados SQLite ou buscar, se não disponível
def load_data(ticker, start_date, end_date):
    conn = sqlite3.connect('stock_data.db')
    query = '''
        SELECT * FROM stock_data
        WHERE ticker = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp
    '''
    data = pd.read_sql_query(query, conn, params=(ticker, start_date, end_date))
    conn.close()
    if data.empty:
        data = fetch_data_from_yfinance(ticker, start_date, end_date)
        if not data.empty:
            conn = sqlite3.connect('stock_data.db')
            data.to_sql('stock_data', conn, if_exists='append', index=False)
            conn.close()
    return data

# Buscar dados do yfinance
def fetch_data_from_yfinance(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data['ticker'] = ticker
    data = data.rename(columns={"Date": "timestamp", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    return data[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']]

# Obter os dados mais recentes para um ticker específico
def get_most_recent_data(ticker):
    conn = sqlite3.connect('stock_data.db')
    query = '''
        SELECT * FROM stock_data
        WHERE ticker = ?
        ORDER BY timestamp DESC
        LIMIT 1
    '''
    most_recent_data = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return most_recent_data.iloc[0] if not most_recent_data.empty else None

# Mapear nomes de empresas populares para tickers
company_ticker_map = {
    "Apple": "AAPL",
    "Nvidia": "NVDA",
    "Tesla": "TSLA",
    "Amazon": "AMZN",
    "AMD": "AMD",
    "Petrobras": "PETR4.SA",
    "Vale": "VALE3.SA",
    "Itaú Unibanco": "ITUB4.SA",
    "Bradesco": "BBDC4.SA",
    "Ambev": "ABEV3.SA"
}

# Recuperar ticker a partir do nome da empresa
def get_ticker_from_name(company_name):
    return company_ticker_map.get(company_name.title())

# Configuração da interface Streamlit
st.set_page_config(page_title="Painel de Dados de Ações em Tempo Real", layout="wide")
st.title("📈 Painel de Dados de Ações em Tempo Real")
st.sidebar.header("Opções de Filtro")

# Selecione rapidamente um ticker
st.sidebar.subheader("Seleção Rápida de Ticker")
quick_ticker = st.sidebar.selectbox("Escolha uma ação popular", list(company_ticker_map.values()))

# Opções de Filtro Personalizado
st.sidebar.subheader("Opções de Filtro Personalizado")
company_name = st.sidebar.text_input("Nome da Empresa (opcional)", key="company_name")
ticker_input = st.sidebar.text_input("Símbolo do Ticker (ex: AAPL)", key="ticker").upper()
ticker = get_ticker_from_name(company_name) or ticker_input or quick_ticker

# Datas de início e fim
start_date = st.sidebar.date_input("Data de Início", datetime.now() - timedelta(days=30), min_value=datetime(2019, 1, 1))
end_date = st.sidebar.date_input("Data de Fim", datetime.now())

# Comparação entre múltiplas ações
st.sidebar.subheader("Comparação de Múltiplas Ações")
selected_tickers = st.sidebar.multiselect("Selecione ações para comparar", list(company_ticker_map.values()), default=[ticker])

# Função para limpar campos de busca
def clear_search():
    st.session_state["company_name"] = ""
    st.session_state["ticker"] = ""

# Botão de limpar
if st.sidebar.button("Limpar Busca", on_click=clear_search):
    st.sidebar.write("Entradas limpas! Por favor, insira um novo ticker ou nome de empresa.")

# Carregar dados para o ticker principal e tickers selecionados
data = load_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
combined_data = pd.DataFrame()
for selected_ticker in selected_tickers:
    stock_data = load_data(selected_ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    if not stock_data.empty:
        combined_data = pd.concat([combined_data, stock_data], axis=0)

# Exibir dados e gráficos
if not data.empty:
    st.write(f"### Dados para {ticker} de {start_date} a {end_date}")
    col1, col2, col3, col4 = st.columns(4)
    avg_close = data['close'].mean()
    price_change = data['close'].iloc[-1] - data['close'].iloc[0] if len(data) > 1 else 0
    volume_avg = data['volume'].mean()
    most_recent_data = get_most_recent_data(ticker)
    most_recent_price = most_recent_data['close'] if most_recent_data is not None else "N/A"
    most_recent_date = most_recent_data['timestamp'] if most_recent_data is not None else "N/A"

    col1.metric(label="Preço Médio de Fechamento", value=f"R${avg_close:.2f}")
    col2.metric(label="Variação de Preço", value=f"R${price_change:.2f}")
    col3.metric(label="Volume Médio", value=f"{volume_avg:.0f}")
    col4.metric(label="Preço Mais Recente", value=f"R${most_recent_price:.2f}", delta=f"Data: {most_recent_date}")

    # Exibir dados brutos em seção expansível
    with st.expander("Ver Dados Brutos"):
        st.dataframe(data)

    # Gráfico interativo de movimentos de preço
    st.subheader("Movimentos de Preço")
    fig = px.line(data, x="timestamp", y=["open", "high", "low", "close"],
                  title="Preços de Ações ao Longo do Tempo", labels={"timestamp": "Data"})
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig, use_container_width=True)

    # Gráfico de volume
    st.subheader("Volume de Negociação")
    fig_vol = px.bar(data, x="timestamp", y="volume", title="Volume de Negociação ao Longo do Tempo",
                     labels={"timestamp": "Data", "volume": "Volume"})
    fig_vol.update_layout(bargap=0.1)
    st.plotly_chart(fig_vol, use_container_width=True)

    # Filtro avançado
    st.subheader("Filtragem e Ordenação Avançada")
    sort_by = st.selectbox("Ordenar Dados Por:", options=["timestamp", "open", "close", "high", "low", "volume"])
    ascending = st.checkbox("Ordenar em Ordem Crescente", value=True)
    sorted_data = data.sort_values(by=sort_by, ascending=ascending)
    st.write(f"Dados ordenados por {sort_by} ({'Crescente' if ascending else 'Decrescente'}):")
    st.dataframe(sorted_data)

# Comparação entre ações
if not combined_data.empty:
    st.write("### Comparação de Ações Selecionadas")
    fig_compare = px.line(combined_data, x="timestamp", y="close", color="ticker", title="Comparação de Preços das Ações")
    st.plotly_chart(fig_compare, use_container_width=True)

    fig_vol_compare = px.bar(combined_data, x="timestamp", y="volume", color="ticker", title="Comparação de Volume")
    fig_vol_compare.update_layout(bargap=0.1)
    st.plotly_chart(fig_vol_compare, use_container_width=True)

# Seção de Previsão de Machine Learning e Deep Learning
st.subheader("Previsão com Machine Learning e Deep Learning")
st.write("Nesta seção, fornecemos previsões usando três modelos: ARIMA, Prophet e LSTM. "
         "Cada modelo utiliza dados históricos para prever preços futuros, com técnicas e pontos fortes distintos.")

forecast_period = st.slider("Período de Previsão (dias)", 1, 30, 7)

# Inicializar métricas do modelo
model_metrics = []

if st.button("Executar Previsão"):
    # Previsão ARIMA
    st.write("#### Previsão ARIMA")
    arima_forecast_df, arima_mse, arima_mae = arima_forecast(data, forecast_period)
    st.line_chart(arima_forecast_df.set_index("Date"), use_container_width=True)
    st.write(f"**Erro Quadrático Médio (MSE):** {arima_mse:.4f}")
    st.write(f"**Erro Médio Absoluto (MAE):** {arima_mae:.4f}")
    st.dataframe(arima_forecast_df)
    model_metrics.append({"Modelo": "ARIMA", "MSE": arima_mse, "MAE": arima_mae})

    # Previsão Prophet
    st.write("#### Previsão Prophet")
    prophet_forecast_df, prophet_mse, prophet_mae = prophet_forecast(data, forecast_period)
    st.line_chart(prophet_forecast_df.set_index("Date"), use_container_width=True)
    st.write(f"**Erro Quadrático Médio (MSE):** {prophet_mse:.4f}")
    st.write(f"**Erro Médio Absoluto (MAE):** {prophet_mae:.4f}")
    st.dataframe(prophet_forecast_df)
    model_metrics.append({"Modelo": "Prophet", "MSE": prophet_mse, "MAE": prophet_mae})

    # Previsão LSTM
    st.write("#### Previsão LSTM")
    try:
        lstm_forecast_df, lstm_mse, lstm_mae = lstm_forecast(data, forecast_period)
        st.line_chart(lstm_forecast_df.set_index("Date"), use_container_width=True)
        st.write(f"**Erro Quadrático Médio (MSE):** {lstm_mse:.4f}")
        st.write(f"**Erro Médio Absoluto (MAE):** {lstm_mae:.4f}")
        st.dataframe(lstm_forecast_df)
        model_metrics.append({"Modelo": "LSTM", "MSE": lstm_mse, "MAE": lstm_mae})
    except ValueError as e:
        st.error(f"Erro na Previsão LSTM: {e}")

# Exibir comparação de métricas
if model_metrics:
    comparison_df = pd.DataFrame(model_metrics)
    st.write("### Comparação de Modelos")
    st.dataframe(comparison_df)
    st.bar_chart(comparison_df.set_index("Modelo"))

# Download dos dados filtrados
st.sidebar.subheader("Baixar Dados")
csv = data.to_csv(index=False)
st.sidebar.download_button(label="Baixar CSV", data=csv, file_name=f"{ticker}_dados.csv", mime="text/csv")

# Inicializar o banco de dados
init_database()