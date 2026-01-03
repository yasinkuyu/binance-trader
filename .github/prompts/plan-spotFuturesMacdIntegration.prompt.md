# Plan: Ampliar funcionalidades Spot-Futures con integración MACD

## Objetivo
Extender el trading bot para soportar tanto operaciones spot como futures, integrando MACD en las señales activas de estrategia y completando la documentación de APIs necesarias. El sistema actual está bien fundamentado: todos los items del roadmap (MACD, Stop-Loss, modos profit/range) ya están implementados, pero MACD no se usa en decisiones de compra/venta activas, y falta soporte para futures.

## Estado Actual (Roadmap)

| Item | Status | Ubicación | Notas |
|------|--------|-----------|-------|
| **MACD Indicator** | ✅ IMPLEMENTADO | Indicators.py | Cálculo completo con línea de señal e histograma |
| **Stop-Loss** | ✅ IMPLEMENTADO | Trading.py & BollingerStrategy.py | Ambas versiones: % y basado en ATR |
| **Modo Profit** | ✅ FUNCIONAL | Trading.py | Compra a precio calculado, venta a % objetivo |
| **Modo Range** | ✅ FUNCIONAL | Trading.py | Compra/venta a precios exactos en rango especificado |

### Brecha Actual
- ✅ Spot trading completamente funcional
- ✅ 9 indicadores técnicos implementados
- ❌ MACD no integrado en señales activas de estrategia
- ❌ Futures trading sin implementar
- ❌ Soporte para leverage/margen ausente

## Plan de Implementación (6 Pasos)

### Paso 1: VERIFICAR FUNCIONAMIENTO E INTEGRIDAD DEL MACD ANTES DE INCLUIR EN BollingerStrategy
**Archivo**: `app/BollingerStrategy.py`  
**Objetivo**: Agregar MACD (histogram + cruce de líneas) como confirmación en lógica de señales BUY/SELL junto con Bollinger Bands y RSI.

**Estado**: ✅ **COMPLETADO** (3 de enero 2026)

**Cambios realizados**:
1. **Mejora de `Indicators.macd()`**
   - Cálculo histórico de valores MACD (no solo aproximación)
   - Signal line es EMA(9) real del historial MACD
   - Histogram calcula diferencia precisa MACD-Signal

2. **Nuevo método: `Indicators.macd_signal_cross()`**
   - Detecta bullish_cross: MACD cruzó arriba signal line
   - Detecta bearish_cross: MACD cruzó abajo signal line
   - Detecta momentum persistente (bullish/bearish_momentum)
   - Devuelve 'none' si no hay señal clara

3. **Integración en `BollingerStrategy`**
   - Calcula MACD línea, signal, e histogram en cada análisis
   - Detecta cruces MACD y momentum
   - Nueva lógica BUY: +25 confianza con bullish_cross, +15 con bullish_momentum
   - Nueva lógica SELL: +25 confianza con bearish_cross, +15 con bearish_momentum
   - Divergencias detectadas: -10 confianza si MACD diverge de señal principal

4. **Parámetros configurables**
   - `macd_fast`: 12 (EMA rápida)
   - `macd_slow`: 26 (EMA lenta)
   - `macd_signal`: 9 (Período signal line)
   - `use_macd`: True/False (habilitar/deshabilitar)

**Testing completado**:
- ✅ MACD Calculation: Valores correctos (MACD: 2.38, Signal: 1.90, Histogram: 0.47)
- ✅ Signal Cross Detection: Detecta bullish y bearish momentum
- ✅ Strategy Integration: BUY/SELL signals generadas con MACD confirmation
- ✅ Backwards Compatibility: Funciona sin MACD si use_macd=False

**Archivos creados**:
- `test_macd_integration.py`: Suite de tests exhaustiva (400+ líneas)
- `test_macd_live.sh`: Script para testing en vivo con Binance
- `MACD_INTEGRATION_STEP1.md`: Documentación completa del paso

**Impacto esperado**:
- Win rate: +15% mejora vs solo Bollinger
- Operaciones: -20% (más selectivas)
- Calidad de señales: Confirmación multi-indicador

---

### Paso 2: Extender BinanceAPI, uno para SPOT otro para Futures con métodos Futures
**Archivo**: `app/BinanceAPI.py`  
**Objetivo**: Agregar endpoints futures usando base URL alternativa `https://fapi.binance.com/fapi/v1`

**Métodos a agregar**:
- `get_futures_account()` - Información de cuenta futures
- `get_futures_balance()` - Saldos futures por activo
- `get_position_risk(symbol)` - Información de posición abierta
- `buy_futures_limit(symbol, quantity, price)` - Orden limit compra
- `sell_futures_limit(symbol, quantity, price)` - Orden limit venta
- `change_leverage(symbol, leverage)` - Cambiar leverage (1-125x)
- `change_margin_type(symbol, margin_type)` - isolated/cross
- `get_open_positions()` - Listar posiciones abiertas

**Consideraciones**:
- Reutilizar código de autenticación existente
- Usar mismos headers y firma que endpoints spot
- Agregar validación de parámetros (leverage 1-125)

---

### Paso 3: Crear FuturesAPI.py - Capa de abstracción
**Archivo**: `app/FuturesAPI.py` (nuevo)  
**Objetivo**: Envoltura de alto nivel para lógica futures, separando concerns

**Componentes**:
```python
class FuturesAPI:
    def __init__(self, binance_api):
        self.api = binance_api
    
    def set_leverage(symbol, leverage): # 1-125
    def set_margin_type(symbol, margin_type): # isolated/cross
    def calculate_liquidation_price(position_size, entry_price, leverage, margin_type)
    def calculate_position_size(account_balance, risk_percent, entry_price, stop_loss_price, leverage)
    def get_funding_rate(symbol)
    def validate_position_safety(symbol, position_size, leverage)
```

**Validaciones internas**:
- Verificar saldo disponible antes de leverage
- Calcular precio de liquidación
- Alertar si riesgo > umbral

---

### Paso 4: Extender config.py y argumentos CLI
**Archivos**: `app/config.py` y `trader.py`  
**Objetivo**: Agregar parámetros de configuración para futures

**Parámetros nuevos**:
```
--trading_type       [spot|futures] default: spot
--leverage           1-125, default: 1
--margin_type        [isolated|cross], default: isolated
--max_liquidation_risk  % de saldo a riesgo, default: 5
--funding_rate_alert    % diferencial, default: 0.01
```

**Validaciones**:
- Si trading_type=spot, ignorar leverage/margin_type
- Si trading_type=futures, requerir leverage > 1 explícito
- Validar compatibility con modo de trading (range mode no aplica a futures)

---

### Paso 5: Crear FuturesTradingBot.py
**Archivo**: `app/FuturesTradingBot.py` (nuevo)  
**Objetivo**: Adaptación de BollingerTradingBot para futures con validaciones específicas

**Diferencias vs Spot**:
- Llamar `FuturesAPI.set_leverage()` en setup
- Antes de compra: verificar `calculate_liquidation_price()` < stop_loss_price
- Rastrear `get_funding_rate()` cada 8h (pago estándar)
- Agregar lógica de cierre forzado si precio se acerca a liquidación
- Logging detallado de cambios de leverage/margen

**Estructura**:
```python
class FuturesTradingBot(BollingerTradingBot):
    def __init__(self, option):
        super().__init__(option)
        self.futures_api = FuturesAPI(self.client)
        self.setup_futures_mode()
    
    def setup_futures_mode(self):
        # Configurar leverage y margen
    
    def validate_liquidation_risk(self):
        # Antes de cada trade
    
    def check_funding_rates(self):
        # Cada ciclo
```

---

### Paso 6: Crear trader_futures.py
**Archivo**: `trader_futures.py` (nuevo)  
**Objetivo**: Entry point específico para operaciones futures, espejo de trader.py

**Estructura**:
- Copiar argumentos de `trader.py`
- Agregar args futures: `--leverage`, `--margin_type`, `--max_liquidation_risk`
- Reemplazar `Trading` con `FuturesTradingBot`
- Advertencias/confirmaciones para leverage alto (>5x)

---

## Secuencia Recomendada de Implementación

### **Fase 1: MACD (✅ COMPLETADO - 3 de enero 2026)**
✅ Paso 1: Integrar MACD en BollingerStrategy
   - Mejorada función macd() con cálculo histórico
   - Nuevo método macd_signal_cross() para detección de cruces
   - Integración en BollingerStrategy.analyze()
   - Nueva lógica de señales con confirmación MACD
   - Suite de tests completa: 4 tests, todos pasando
   - Documentación técnica y ejemplos incluidos

**Archivos creados/modificados:**
- ✅ app/Indicators.py (mejorada)
- ✅ app/BollingerStrategy.py (integrada)
- ✅ test_macd_integration.py (nuevo)
- ✅ test_macd_live.sh (nuevo)
- ✅ MACD_INTEGRATION_STEP1.md (nuevo)
- ✅ STEP1_COMPLETE.md (nuevo)

**Validación completada:**
- ✅ MACD Calculation: Precisión verificada
- ✅ Signal Cross Detection: Cruces identificados correctamente
- ✅ Strategy Integration: Señales generadas con MACD confirmation
- ✅ Backwards Compatibility: Funciona sin MACD si use_macd=False

**Beneficio**: Mejora +15% en win rate esperada, señales más confiables

---

### **Fase 2: Fundamentos Futures (Próximo - 1-2 semanas)**
2. Paso 2: Extender BinanceAPI con métodos futures
3. Paso 3: Crear FuturesAPI (abstracción)
4. Paso 4: Agregar parámetros config
5. Testing unitario de cálculos (liquidación, posiciones)

### **Fase 3: Bot Futures (1-2 semanas)**
6. Paso 5: Implementar FuturesTradingBot
7. Paso 6: Crear trader_futures.py
8. Testing completo en testnet (si aplica)
9. QA con montos mínimos en demo

---

## Consideraciones Técnicas

### MACD Integration
- **Parámetros actuales**: 12, 26, 9 (estándar)
- **Histograma**: Detectar cruces (de negativo a positivo = BUY)
- **Fortaleza**: Combina momentum + trend-following
- **Debilidad**: Lag en mercados rápidos (requiere RSI para confirmación)

### Futures vs Spot
| Aspecto | Spot | Futures |
|--------|------|---------|
| Leverage | 1x | 1-125x |
| Margen | N/A | Isolated/Cross |
| Liquidación | No aplica | Automática si saldo < margen |
| Comisión | Maker: 0.1% | Maker: 0.02% |
| Funding | No | Cada 8h (pagos) |
| Shorting | No | Sí (con leverage) |

### API Base URLs
- Spot: `https://api.binance.com/api/v3/`
- Futures: `https://fapi.binance.com/fapi/v1/`

### Documentación Binance Requerida
- ✅ Spot: Documentación presente en proyecto
- ❌ Futures: Agregar referencias a `fapi/v1` endpoints
  - `/account` (futures)
  - `/openOrders` (futures)
  - `/positionRisk`
  - `/leverage` (cambio)
  - `/marginType` (cambio)

---

## Testing Strategy

### Test Mode (Sin capital)
```bash
# Spot con MACD
python trader.py --symbol ETHBTC --test_mode True

# Futures demo
python trader_futures.py --symbol ETHUSDT --test_mode True --leverage 3
```

### Backtest
- Usar datos históricos de BinanceAPI
- Simular avec MACD + Bollinger
- Comparar vs solo Bollinger
- Verificar drawdown máximo

### Validación Futures
- Testnet Binance (si disponible)
- Órdenes mínimas en live
- Monitoreo 24/7 de liquidación (automatizado)

---

## Métricas de Éxito

- [ ] MACD integrado: +15% win rate vs solo Bollinger
- [ ] Futures setup: 0 liquidaciones involuntarias
- [ ] Performance: <500ms latencia por ciclo
- [ ] Confiabilidad: 99.5% uptime en test 1 semana
- [ ] Documentación: Actualizada + ejemplos de uso

---

## Notas de Refinamiento

**A Validar**:
1. ¿Usar WebSocket para actualizaciones en tiempo real o polling cada N segundos?
2. ¿Aplicar MACD solamente o crear estrategia multi-timeframe?
3. ¿Margen cross recomendado o isolated para mayor seguridad?
4. ¿Almacenar datos de funding rate en DB para análisis?
5. ¿Agregar alertas Telegram/Discord en eventos críticos (liquidación cercana)?

**Extensiones Futuras**:
- Multi-pair portfolio (diversificación)
- Machine learning para optimización de parámetros
- Backtesting framework completo
- Dashboard web con métricas en tiempo real
