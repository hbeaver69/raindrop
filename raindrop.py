import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def make_raindrop_chart(
    ticker: str = "AAPL",
    start: str = None, 
    end: str = None,  
    interval: str = "5m",
    frequency_unit: str = "m",
    frequency_value: int = 30,
    margin: float = 0.1
):
    try:
        # Ensure start and end dates are provided
        if not start or not end:
            raise ValueError("Start and End dates must be provided.")

        # Download data from yfinance
        df = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            interval=interval,
        )

        # Check if the DataFrame is empty
        if df.empty:
            raise ValueError(f"No data returned for {ticker} between {start} and {end}. Check if the ticker is correct or if there's data available in this range.")
        
        # Reset the index to turn the Datetime index into a column
        df = df.reset_index()

        # Rename the index to 'Datetime' if necessary
        if 'Datetime' not in df.columns:
            df.rename(columns={df.columns[0]: 'Datetime'}, inplace=True)

        # Check if 'Datetime' column exists
        if 'Datetime' not in df.columns:
            raise KeyError("The 'Datetime' column is not present in the DataFrame.")

        # Convert 'Datetime' column to datetime format
        df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
        df = df.dropna(subset=['Datetime'])

        # Create 'Typical' price and calculate VWAP
        df["Typical"] = df[["Open", "High", "Low", "Close"]].sum(axis=1) / 4
        df["QTY*PX"] = df["Volume"] * df["Typical"]

        # Grouping frequency
        grouping_frequency = pd.Timedelta(frequency_value, unit=frequency_unit)
        split_frequency = pd.Timedelta(grouping_frequency.total_seconds() / 2, unit="s")

        # Group the OHLC data
        ohlc = df.groupby(pd.Grouper(key="Datetime", freq=grouping_frequency)).agg(
            Open=("Open", "first"),
            High=("High", "max"),
            Low=("Low", "min"),
            Close=("Close", "last"),
            Volume=("Volume", "sum")
        ).reset_index()

        # Check if ohlc is empty
        if ohlc.empty:
            raise ValueError(f"No data available after processing for {ticker}. Try using a different date range or frequency.")
        
        # Create split for raindrop chart
        df["Split"] = df.groupby(pd.Grouper(key="Datetime", freq=split_frequency)).ngroup()
        df["Split"] = df["Split"] % 2
        df["Datetime"] = df["Datetime"].dt.floor(grouping_frequency)
        volume_divider = df["Volume"].max() / 1000

        # Plot
        fig = make_subplots(
            rows=3,
            cols=1,
            row_heights=[0.45, 0.45, 0.1],
            shared_xaxes=True,
            vertical_spacing=0.01
        )
        showlegend = True

        for period, period_df in df.groupby("Datetime"):
            vwap_df = period_df.groupby("Split", as_index=False)[["Volume", "QTY*PX"]].sum()
            vwap_df = vwap_df.query("Volume > 0").reset_index()
            if not vwap_df.empty:
                vwap_df["VWAP"] = vwap_df["QTY*PX"] / vwap_df["Volume"]
                color = "blue"
                if len(vwap_df.index) > 1:
                    vwap_open, vwap_close = vwap_df.loc[0, "VWAP"], vwap_df.loc[1, "VWAP"]
                    if (vwap_close - vwap_open) > margin:
                        color = "green"
                    elif (vwap_open - vwap_close) > margin:
                        color = "red"
                period_df["Volume"] = period_df["Volume"].div(volume_divider).round()
                for split, split_df in period_df.groupby("Split"):
                    is_pre_split = split == 0
                    split_df = split_df.loc[split_df.index.repeat(split_df["Volume"])]
                    fig.add_trace(
                        go.Violin(
                            x=split_df["Datetime"],
                            y=split_df["Typical"],
                            side="negative" if is_pre_split else "positive",
                            name="Raindrop",
                            legendgroup="Raindrop",
                            showlegend=showlegend,
                            line=dict(color=color),
                            spanmode="hard",
                            scalegroup=str(period),
                            scalemode="count",
                            points=False,
                            hoverinfo="y",
                            hoveron="violins",
                            meanline=dict(color="white"),
                        ),
                        row=1,
                        col=1
                    )
                    showlegend = False

        fig.add_trace(
            go.Candlestick(
                x=ohlc["Datetime"],
                open=ohlc["Open"],
                high=ohlc["High"],
                low=ohlc["Low"],
                close=ohlc["Close"],
                name="OHLC",
                decreasing_line_color="red",
                increasing_line_color="green",
            ),
            row=2,
            col=1
        )

        ohlc["BarColor"] = ohlc.apply(lambda x: "green" if x["Open"] < x["Close"] else "red", axis=1)
        showlegend = True
        for color, sub_ohlc in ohlc.groupby("BarColor"):
            fig.add_trace(
                go.Bar(
                    x=sub_ohlc["Datetime"],
                    y=sub_ohlc["Volume"],
                    marker=dict(color=color),
                    legendgroup="Volume",
                    name="Volume",
                    showlegend=showlegend,
                    hovertemplate=None,
                    texttemplate="%{y:.2s}"
                ),
                row=3,
                col=1
            )
            showlegend = False

        fig.update_xaxes(
            rangeslider_visible=False,
            row=2
        )
        fig.update_xaxes(
            dtick=1000 * grouping_frequency.total_seconds(),
            showgrid=True,
            title="Datetime",
            row=3
        )
        fig.update_xaxes(
            rangebreaks=[dict(bounds=[16, 9.5], pattern="hour")],
        )
        fig.update_yaxes(title="Price", row=1)
        fig.update_yaxes(title="Price", row=2)
        fig.update_yaxes(title="Volume", row=3)
        fig.update_layout(
            title=dict(text=ticker),
            violingap=0,
            violingroupgap=0,
            template="plotly_dark",
            height=800,
            uirevision="uirevision"
        )
        
        # Return all 4 expected values
        return fig, vwap_open, vwap_close, ohlc.to_dict("records")[-1]

    except Exception as e:
        raise ValueError(f"An error occurred while generating the chart: {e}")
