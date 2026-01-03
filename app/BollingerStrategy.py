# -*- coding: UTF-8 -*-
# Advanced Bollinger Bands Trading Strategy
# Combines BB with RSI, Volume Analysis, and Risk Management

import logging
from typing import Dict, List, Tuple, Optional
from Indicators import Indicators


class BollingerStrategy:
    """
    Advanced Bollinger Bands Trading Strategy with MACD Confirmation

    Strategy Rules:
    - BUY: Price touches lower band + RSI < 30 + High volume + MACD bullish cross/momentum
    - SELL: Price touches upper band + RSI > 70 + MACD bearish cross/momentum
    - Alternative: Reach middle band (take profit)
    - Uses dynamic stop-loss based on ATR
    
    MACD Integration:
    - Bullish signals confirmed when MACD shows bullish momentum
    - Bearish signals confirmed when MACD shows bearish momentum
    - Increases confidence score when MACD crosses signal line
    """

    def __init__(self, config: Dict = None):
        """
        Initialize Bollinger Bands Strategy with MACD

        Args:
            config: Strategy configuration parameters
        """
        self.config = config or {}

        # Bollinger Bands parameters
        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std_dev = self.config.get('bb_std_dev', 2.0)

        # RSI parameters
        self.rsi_period = self.config.get('rsi_period', 14)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)

        # Volume parameters
        self.volume_period = self.config.get('volume_period', 20)
        self.volume_threshold = self.config.get('volume_threshold', 1.2)

        # Risk management
        self.stop_loss_atr_multiplier = self.config.get('stop_loss_atr', 2.0)
        self.take_profit_target = self.config.get('take_profit', 'middle')  # 'middle', 'upper', or percentage

        # Additional filters
        self.min_bb_width = self.config.get('min_bb_width', 1.0)  # Minimum volatility
        self.max_bb_width = self.config.get('max_bb_width', 10.0)  # Maximum volatility

        # MACD parameters
        self.macd_fast = self.config.get('macd_fast', 12)
        self.macd_slow = self.config.get('macd_slow', 26)
        self.macd_signal = self.config.get('macd_signal', 9)
        self.use_macd = self.config.get('use_macd', True)  # Enable/disable MACD confirmation

        self.logger = logging.getLogger('BollingerStrategy')

    def analyze(self, klines: List[List], current_price: float, current_volume: float = 0) -> Dict:
        """
        Analyze market conditions using Bollinger Bands + RSI + Volume + MACD strategy

        Args:
            klines: List of kline data [timestamp, open, high, low, close, volume, ...]
            current_price: Current market price
            current_volume: Current trading volume

        Returns:
            Dictionary containing analysis results and trading signals
        """
        if not klines or len(klines) < self.bb_period:
            return {
                'signal': 'WAIT',
                'confidence': 0.0,
                'reason': 'Insufficient data for analysis'
            }

        # Extract price and volume data
        closes = [float(k[4]) for k in klines]  # Close prices
        highs = [float(k[2]) for k in klines]   # High prices
        lows = [float(k[3]) for k in klines]    # Low prices
        volumes = [float(k[5]) for k in klines] # Volumes

        # Calculate indicators
        upper_band, middle_band, lower_band = Indicators.bollinger_bands(
            closes, self.bb_period, self.bb_std_dev
        )

        if upper_band is None:
            return {
                'signal': 'WAIT',
                'confidence': 0.0,
                'reason': 'Unable to calculate Bollinger Bands'
            }

        rsi = Indicators.rsi(closes, self.rsi_period)
        bb_width = Indicators.bb_width(upper_band, lower_band, middle_band)
        bb_percent = Indicators.bb_percent(current_price, upper_band, lower_band)
        volume_data = Indicators.volume_analysis(volumes, self.volume_period)
        atr = Indicators.atr(highs, lows, closes, 14)
        
        # Calculate MACD indicators
        macd_line, signal_line, histogram = Indicators.macd(closes, self.macd_fast, self.macd_slow, self.macd_signal)
        macd_signal_cross = Indicators.macd_signal_cross(closes, self.macd_fast, self.macd_slow, self.macd_signal) if self.use_macd else 'none'

        # Build analysis result
        analysis = {
            'price': current_price,
            'indicators': {
                'bb_upper': upper_band,
                'bb_middle': middle_band,
                'bb_lower': lower_band,
                'bb_width': bb_width,
                'bb_percent': bb_percent,
                'rsi': rsi,
                'volume_ratio': volume_data['volume_ratio'],
                'atr': atr,
                'macd_line': macd_line,
                'macd_signal': signal_line,
                'macd_histogram': histogram,
                'macd_signal_cross': macd_signal_cross
            },
            'signal': 'WAIT',
            'confidence': 0.0,
            'reason': '',
            'entry_price': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0
        }

        # Check volatility conditions
        if bb_width < self.min_bb_width:
            analysis['reason'] = f'Low volatility (BB Width: {bb_width:.2f}%)'
            return analysis

        if bb_width > self.max_bb_width:
            analysis['reason'] = f'Excessive volatility (BB Width: {bb_width:.2f}%)'
            return analysis

        # Determine trading signal
        signal_result = self._generate_signal(
            current_price, upper_band, middle_band, lower_band,
            rsi, volume_data, bb_percent, atr, macd_line, signal_line, histogram, macd_signal_cross
        )

        analysis.update(signal_result)
        return analysis

    def _generate_signal(
        self,
        price: float,
        upper: float,
        middle: float,
        lower: float,
        rsi: float,
        volume_data: Dict,
        bb_percent: float,
        atr: float,
        macd_line: float,
        macd_signal: float,
        macd_histogram: float,
        macd_signal_cross: str
    ) -> Dict:
        """
        Generate trading signal based on strategy rules + MACD confirmation

        MACD Integration:
        - BUY: Confirmation when MACD shows bullish_cross or bullish_momentum
        - SELL: Confirmation when MACD shows bearish_cross or bearish_momentum
        - Bollinger: Primary signal from price position and bands
        - RSI: Secondary confirmation for momentum
        - Volume: Tertiary confirmation for strength

        Returns:
            Dictionary with signal, confidence, and trade parameters
        """
        confidence = 0.0
        reasons = []

        # === BUY SIGNAL CONDITIONS ===
        if price <= lower * 1.005:  # Price at or below lower band (0.5% tolerance)
            confidence += 30
            reasons.append('Price at lower BB')

            # RSI confirmation
            if rsi < self.rsi_oversold:
                confidence += 25
                reasons.append(f'RSI oversold ({rsi:.1f})')
            elif rsi < 40:
                confidence += 15
                reasons.append(f'RSI favorable ({rsi:.1f})')

            # Volume confirmation
            if volume_data['volume_ratio'] > self.volume_threshold:
                confidence += 20
                reasons.append(f'High volume ({volume_data["volume_ratio"]:.2f}x)')
            elif volume_data['volume_ratio'] > 1.0:
                confidence += 10
                reasons.append(f'Above avg volume ({volume_data["volume_ratio"]:.2f}x)')

            # BB position
            if bb_percent < 0.1:
                confidence += 15
                reasons.append('Price well below lower band')

            # MACD confirmation - bullish momentum or cross
            if self.use_macd:
                if macd_signal_cross == 'bullish_cross':
                    confidence += 25
                    reasons.append('MACD bullish cross ↑')
                elif macd_signal_cross == 'bullish_momentum':
                    confidence += 15
                    reasons.append('MACD bullish momentum')
                elif macd_histogram < 0:
                    confidence -= 10  # Bearish divergence
                    reasons.append('MACD bearish (divergence warning)')

            if confidence >= 50:
                # Calculate trade parameters
                stop_loss = price - (atr * self.stop_loss_atr_multiplier)

                if self.take_profit_target == 'middle':
                    take_profit = middle
                elif self.take_profit_target == 'upper':
                    take_profit = upper
                else:
                    take_profit = price * (1 + self.take_profit_target / 100)

                return {
                    'signal': 'BUY',
                    'confidence': min(confidence, 100),
                    'reason': ' | '.join(reasons),
                    'entry_price': price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'risk_reward': (take_profit - price) / (price - stop_loss) if price > stop_loss else 0
                }

        # === SELL SIGNAL CONDITIONS ===
        elif price >= upper * 0.995:  # Price at or above upper band (0.5% tolerance)
            confidence += 30
            reasons.append('Price at upper BB')

            # RSI confirmation
            if rsi > self.rsi_overbought:
                confidence += 25
                reasons.append(f'RSI overbought ({rsi:.1f})')
            elif rsi > 60:
                confidence += 15
                reasons.append(f'RSI favorable ({rsi:.1f})')

            # Volume confirmation
            if volume_data['volume_ratio'] > self.volume_threshold:
                confidence += 20
                reasons.append(f'High volume ({volume_data["volume_ratio"]:.2f}x)')

            # BB position
            if bb_percent > 0.9:
                confidence += 15
                reasons.append('Price well above upper band')

            # MACD confirmation - bearish momentum or cross
            if self.use_macd:
                if macd_signal_cross == 'bearish_cross':
                    confidence += 25
                    reasons.append('MACD bearish cross ↓')
                elif macd_signal_cross == 'bearish_momentum':
                    confidence += 15
                    reasons.append('MACD bearish momentum')
                elif macd_histogram > 0:
                    confidence -= 10  # Bullish divergence
                    reasons.append('MACD bullish (divergence warning)')

            if confidence >= 50:
                return {
                    'signal': 'SELL',
                    'confidence': min(confidence, 100),
                    'reason': ' | '.join(reasons),
                    'entry_price': 0.0,
                    'stop_loss': 0.0,
                    'take_profit': 0.0
                }

        # === TAKE PROFIT at MIDDLE BAND (if holding) ===
        if middle * 0.99 <= price <= middle * 1.01:
            return {
                'signal': 'TAKE_PROFIT',
                'confidence': 70,
                'reason': 'Price reached middle band (take profit target)',
                'entry_price': 0.0,
                'stop_loss': 0.0,
                'take_profit': middle
            }

        # No clear signal
        return {
            'signal': 'WAIT',
            'confidence': confidence,
            'reason': 'No clear signal | ' + ' | '.join(reasons) if reasons else 'Waiting for setup',
            'entry_price': 0.0,
            'stop_loss': 0.0,
            'take_profit': 0.0
        }

    def should_buy(self, analysis: Dict) -> bool:
        """
        Determine if should execute buy order

        Args:
            analysis: Analysis result from analyze()

        Returns:
            True if should buy
        """
        return analysis['signal'] == 'BUY' and analysis['confidence'] >= 50

    def should_sell(self, analysis: Dict, position_price: float = 0) -> bool:
        """
        Determine if should execute sell order

        Args:
            analysis: Analysis result from analyze()
            position_price: Price at which position was entered (for profit calculation)

        Returns:
            True if should sell
        """
        if analysis['signal'] in ['SELL', 'TAKE_PROFIT']:
            return analysis['confidence'] >= 50

        # Check stop loss
        if position_price > 0 and analysis['stop_loss'] > 0:
            if analysis['price'] <= analysis['stop_loss']:
                return True

        return False

    def calculate_position_size(
        self,
        balance: float,
        price: float,
        risk_percentage: float = 2.0,
        stop_loss: float = 0
    ) -> float:
        """
        Calculate position size based on risk management

        Args:
            balance: Available balance
            price: Entry price
            risk_percentage: Percentage of balance to risk (default: 2%)
            stop_loss: Stop loss price

        Returns:
            Position size (quantity to buy)
        """
        if stop_loss == 0 or price <= stop_loss:
            # Default position size (no stop loss provided)
            return (balance * (risk_percentage / 100)) / price

        # Risk-based position sizing
        risk_amount = balance * (risk_percentage / 100)
        price_risk = price - stop_loss
        position_size = risk_amount / price_risk

        # Don't use more than available balance
        max_quantity = balance / price
        return min(position_size, max_quantity)
