# -*- coding: UTF-8 -*-
# Advanced Technical Indicators for Binance Trader
# Implements Bollinger Bands, RSI, Volume Analysis, and more

import math
from typing import List, Tuple, Dict


class Indicators:
    """
    Technical Analysis Indicators for Cryptocurrency Trading
    """

    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[float, float, float]:
        """
        Calculate Bollinger Bands

        Args:
            prices: List of closing prices (most recent last)
            period: Moving average period (default: 20)
            std_dev: Standard deviation multiplier (default: 2.0)

        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        if len(prices) < period:
            return None, None, None

        # Calculate Simple Moving Average (SMA)
        sma = sum(prices[-period:]) / period

        # Calculate Standard Deviation
        variance = sum([(price - sma) ** 2 for price in prices[-period:]]) / period
        std = math.sqrt(variance)

        # Calculate bands
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return upper_band, sma, lower_band

    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index (RSI)

        Args:
            prices: List of closing prices (most recent last)
            period: RSI period (default: 14)

        Returns:
            RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral value if not enough data

        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas[-period:]]
        losses = [-delta if delta < 0 else 0 for delta in deltas[-period:]]

        # Calculate average gain and loss
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def ema(prices: List[float], period: int) -> float:
        """
        Calculate Exponential Moving Average (EMA)

        Args:
            prices: List of closing prices (most recent last)
            period: EMA period

        Returns:
            EMA value
        """
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA

        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    @staticmethod
    def volume_analysis(volumes: List[float], period: int = 20) -> Dict[str, float]:
        """
        Analyze volume patterns

        Args:
            volumes: List of volume data (most recent last)
            period: Analysis period

        Returns:
            Dictionary with volume metrics
        """
        if len(volumes) < period:
            return {
                'avg_volume': sum(volumes) / len(volumes) if volumes else 0,
                'current_volume': volumes[-1] if volumes else 0,
                'volume_ratio': 1.0
            }

        avg_volume = sum(volumes[-period:]) / period
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

        return {
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'volume_ratio': volume_ratio,
            'is_high_volume': volume_ratio > 1.5,
            'is_low_volume': volume_ratio < 0.5
        }

    @staticmethod
    def atr(high: List[float], low: List[float], close: List[float], period: int = 14) -> float:
        """
        Calculate Average True Range (ATR) for volatility measurement

        Args:
            high: List of high prices
            low: List of low prices
            close: List of closing prices
            period: ATR period (default: 14)

        Returns:
            ATR value
        """
        if len(high) < period + 1:
            return 0.0

        true_ranges = []
        for i in range(1, len(high)):
            tr = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
            true_ranges.append(tr)

        atr = sum(true_ranges[-period:]) / period
        return atr

    @staticmethod
    def bb_width(upper: float, lower: float, middle: float) -> float:
        """
        Calculate Bollinger Band Width (volatility indicator)

        Args:
            upper: Upper Bollinger Band
            lower: Lower Bollinger Band
            middle: Middle Bollinger Band (SMA)

        Returns:
            BB Width as percentage
        """
        if middle == 0:
            return 0.0
        return ((upper - lower) / middle) * 100

    @staticmethod
    def bb_percent(price: float, upper: float, lower: float) -> float:
        """
        Calculate %B - where price is within the Bollinger Bands

        Args:
            price: Current price
            upper: Upper Bollinger Band
            lower: Lower Bollinger Band

        Returns:
            %B value (0-1, can exceed these bounds)
        """
        if upper == lower:
            return 0.5
        return (price - lower) / (upper - lower)

    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        MACD measures momentum and trend-following characteristics by:
        - MACD Line: Fast EMA (12) - Slow EMA (26)
        - Signal Line: 9-period EMA of MACD Line
        - Histogram: MACD Line - Signal Line (visual difference)

        Trading Signals:
        - Bullish: MACD crosses above signal line (positive histogram)
        - Bearish: MACD crosses below signal line (negative histogram)

        Args:
            prices: List of closing prices (most recent last)
            fast: Fast EMA period (default: 12)
            slow: Slow EMA period (default: 26)
            signal: Signal line EMA period (default: 9)

        Returns:
            Tuple of (MACD_line, Signal_line, Histogram)
            Values near 0 = neutral, Positive = bullish, Negative = bearish
        """
        if len(prices) < slow:
            return 0.0, 0.0, 0.0

        # Calculate EMAs
        ema_fast = Indicators.ema(prices, fast)
        ema_slow = Indicators.ema(prices, slow)

        # MACD Line = Fast EMA - Slow EMA
        macd_line = ema_fast - ema_slow

        # Signal Line = 9-period EMA of MACD values (simplified with last N values)
        # For proper calculation, we need historical MACD values
        # Using simplified approach: approximate signal line
        if len(prices) >= slow + signal:
            # Calculate MACD values for last signal+slow periods
            macd_values = []
            for i in range(slow, len(prices)):
                fast_ema = Indicators.ema(prices[:i+1], fast)
                slow_ema = Indicators.ema(prices[:i+1], slow)
                macd_values.append(fast_ema - slow_ema)

            # Signal line is EMA of MACD values
            if len(macd_values) >= signal:
                signal_line = Indicators.ema(macd_values[-signal:], signal)
            else:
                signal_line = sum(macd_values) / len(macd_values) if macd_values else 0.0
        else:
            signal_line = macd_line * 0.8  # Fallback approximation

        # Histogram = MACD - Signal
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def macd_signal_cross(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
        """
        Detect MACD signal line crossovers

        Returns:
            'bullish_cross': MACD line crossed above signal line (buy signal)
            'bearish_cross': MACD line crossed below signal line (sell signal)
            'bullish_momentum': MACD > signal (positive momentum)
            'bearish_momentum': MACD < signal (negative momentum)
            'none': No clear signal
        """
        if len(prices) < slow + 2:
            return 'none'

        # Current values
        macd_curr, signal_curr, hist_curr = Indicators.macd(prices[-slow:] if len(prices) >= slow else prices, fast, slow, signal)

        # Previous values
        if len(prices) >= slow + 1:
            macd_prev, signal_prev, hist_prev = Indicators.macd(prices[-(slow+1):-1] if len(prices) > slow else prices, fast, slow, signal)
        else:
            return 'none'

        # Detect crossovers
        if macd_prev <= signal_prev and macd_curr > signal_curr:
            return 'bullish_cross'
        elif macd_prev >= signal_prev and macd_curr < signal_curr:
            return 'bearish_cross'
        elif macd_curr > signal_curr:
            return 'bullish_momentum'
        elif macd_curr < signal_curr:
            return 'bearish_momentum'

        return 'none'

    @staticmethod
    def support_resistance(prices: List[float], window: int = 20) -> Tuple[float, float]:
        """
        Identify support and resistance levels

        Args:
            prices: List of prices
            window: Lookback window

        Returns:
            Tuple of (support, resistance)
        """
        if len(prices) < window:
            window = len(prices)

        recent_prices = prices[-window:]
        support = min(recent_prices)
        resistance = max(recent_prices)

        return support, resistance
