"""
ML-based trading strategy stub.
Provides mock machine learning predictions for FX trading.
"""

import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from models import TradeSignal, SignalType, MLPrediction, FXRate
from utils import calculate_all_indicators, PriceData

logger = logging.getLogger(__name__)

@dataclass
class MLModelConfig:
    """Configuration for ML models."""
    model_type: str = "lstm"  # lstm, gru, transformer, random_forest
    lookback_window: int = 60
    prediction_horizon: int = 1
    retrain_interval_hours: int = 24
    confidence_threshold: float = 0.7
    feature_columns: List[str] = None
    
    def __post_init__(self):
        if self.feature_columns is None:
            self.feature_columns = [
                'close', 'sma_fast', 'sma_slow', 'rsi', 'macd_line', 
                'bb_upper', 'bb_lower', 'atr', 'volume'
            ]

class MockMLModel:
    """Mock ML model for demonstration purposes."""
    
    def __init__(self, model_type: str = "lstm"):
        self.model_type = model_type
        self.is_trained = False
        self.last_training = None
        self.model_accuracy = random.uniform(0.55, 0.75)  # Mock accuracy
        self.feature_importance = self._generate_feature_importance()
        
        # Simulate model parameters
        self.weights = np.random.randn(20) * 0.1
        self.bias = random.uniform(-0.1, 0.1)
    
    def _generate_feature_importance(self) -> Dict[str, float]:
        """Generate mock feature importance scores."""
        features = ['price_change', 'sma_cross', 'rsi', 'macd', 'bb_position', 
                   'volume', 'volatility', 'momentum', 'trend', 'support_resistance']
        
        importance = {}
        remaining = 1.0
        
        for i, feature in enumerate(features):
            if i == len(features) - 1:
                importance[feature] = remaining
            else:
                value = random.uniform(0, remaining / (len(features) - i))
                importance[feature] = value
                remaining -= value
        
        return importance
    
    def predict(self, features: np.ndarray) -> Tuple[float, float]:
        """
        Make a prediction based on features.
        
        Args:
            features: Feature array
            
        Returns:
            Tuple of (prediction, confidence)
        """
        if not self.is_trained:
            self._mock_training()
        
        # Mock prediction logic
        prediction_raw = np.dot(features[:len(self.weights)], self.weights) + self.bias
        prediction = np.tanh(prediction_raw)  # Normalize to -1, 1
        
        # Add some noise and market regime simulation
        market_noise = random.gauss(0, 0.1)
        prediction += market_noise
        
        # Calculate confidence based on magnitude
        confidence = min(abs(prediction) + 0.3, 0.95)
        
        # Simulate model uncertainty
        confidence *= self.model_accuracy
        
        return prediction, confidence
    
    def _mock_training(self):
        """Simulate model training process."""
        logger.info(f"Training {self.model_type} model...")
        self.is_trained = True
        self.last_training = datetime.utcnow()
        
        # Simulate training metrics
        self.training_metrics = {
            'loss': random.uniform(0.2, 0.5),
            'accuracy': self.model_accuracy,
            'precision': random.uniform(0.5, 0.8),
            'recall': random.uniform(0.5, 0.8),
            'f1_score': random.uniform(0.5, 0.75)
        }
    
    def should_retrain(self, retrain_interval_hours: int = 24) -> bool:
        """Check if model should be retrained."""
        if not self.last_training:
            return True
        
        time_since_training = datetime.utcnow() - self.last_training
        return time_since_training.total_seconds() > retrain_interval_hours * 3600
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metrics."""
        return {
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'last_training': self.last_training.isoformat() if self.last_training else None,
            'accuracy': self.model_accuracy,
            'feature_importance': self.feature_importance,
            'training_metrics': getattr(self, 'training_metrics', {})
        }

class MLStrategy:
    """ML-powered trading strategy."""
    
    def __init__(self, config: Optional[MLModelConfig] = None):
        self.config = config or MLModelConfig()
        self.models: Dict[str, MockMLModel] = {}
        self.prediction_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration_minutes = 5  # Cache predictions for 5 minutes
        
        # Strategy parameters
        self.min_confidence = 0.6
        self.position_sizing_factor = 0.5
        
        # Performance tracking
        self.predictions_made = 0
        self.correct_predictions = 0
        self.prediction_history = []
    
    def _get_or_create_model(self, pair: str) -> MockMLModel:
        """Get or create ML model for currency pair."""
        if pair not in self.models:
            self.models[pair] = MockMLModel(self.config.model_type)
            logger.info(f"Created new {self.config.model_type} model for {pair}")
        
        return self.models[pair]
    
    async def get_signals(self, pair: str, historical_data: Optional[List[PriceData]] = None) -> List[TradeSignal]:
        """
        Generate ML-based trading signals.
        
        Args:
            pair: Currency pair
            historical_data: Historical price data
            
        Returns:
            List of trading signals
        """
        # Check cache first
        cache_key = f"{pair}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"
        if cache_key in self.prediction_cache:
            cached_prediction = self.prediction_cache[cache_key]
            cache_time = cached_prediction['timestamp']
            if (datetime.utcnow() - cache_time).seconds < self.cache_duration_minutes * 60:
                return self._create_signal_from_prediction(pair, cached_prediction)
        
        try:
            # Generate prediction
            prediction = await self._generate_prediction(pair, historical_data)
            
            # Cache prediction
            self.prediction_cache[cache_key] = {
                'prediction': prediction,
                'timestamp': datetime.utcnow()
            }
            
            # Clean old cache entries
            self._clean_cache()
            
            # Convert to trading signals
            return self._create_signal_from_prediction(pair, {'prediction': prediction})
            
        except Exception as e:
            logger.error(f"Error generating ML signals for {pair}: {e}")
            return []
    
    async def _generate_prediction(self, pair: str, historical_data: Optional[List[PriceData]]) -> MLPrediction:
        """Generate ML prediction for currency pair."""
        model = self._get_or_create_model(pair)
        
        # Retrain if needed
        if model.should_retrain(self.config.retrain_interval_hours):
            await self._retrain_model(pair, model, historical_data)
        
        # Generate features
        features = await self._generate_features(pair, historical_data)
        
        # Make prediction
        prediction_value, confidence = model.predict(features)
        
        # Convert to signal type
        if prediction_value > 0.1:
            signal = SignalType.BUY
        elif prediction_value < -0.1:
            signal = SignalType.SELL
        else:
            signal = SignalType.HOLD
        
        # Create ML prediction object
        prediction = MLPrediction(
            pair=pair,
            prediction=signal,
            probability=abs(prediction_value),
            confidence=confidence,
            features=self._get_feature_dict(features),
            model_version=f"{model.model_type}_v1.0"
        )
        
        # Track prediction
        self.predictions_made += 1
        self.prediction_history.append({
            'timestamp': datetime.utcnow(),
            'pair': pair,
            'prediction': signal.value,
            'confidence': confidence,
            'actual_outcome': None  # Will be updated later
        })
        
        # Keep only recent predictions
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-500:]
        
        return prediction
    
    def _get_feature_dict(self, features: np.ndarray) -> Dict[str, float]:
        """Convert feature array to dictionary with named features."""
        feature_names = [
            'price_momentum', 'sma_ratio', 'rsi_normalized', 'macd_signal',
            'bb_position', 'volatility', 'volume_ratio', 'trend_strength'
        ]
        
        feature_dict = {}
        for i, name in enumerate(feature_names):
            if i < len(features):
                feature_dict[name] = float(features[i])
        
        return feature_dict
    
    async def _generate_features(self, pair: str, historical_data: Optional[List[PriceData]]) -> np.ndarray:
        """Generate feature vector for ML model."""
        if not historical_data or len(historical_data) < 50:
            # Generate mock features
            return self._generate_mock_features()
        
        # Calculate technical indicators
        indicators = calculate_all_indicators(historical_data)
        
        # Extract features from indicators
        features = []
        
        try:
            # Price momentum
            closes = [p.close for p in historical_data]
            price_momentum = (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 else 0
            features.append(price_momentum)
            
            # SMA ratio
            sma_fast = indicators.get('sma_fast', [])
            sma_slow = indicators.get('sma_slow', [])
            if sma_fast and sma_slow and not (np.isnan(sma_fast[-1]) or np.isnan(sma_slow[-1])):
                sma_ratio = (sma_fast[-1] - sma_slow[-1]) / sma_slow[-1]
            else:
                sma_ratio = 0
            features.append(sma_ratio)
            
            # RSI normalized
            rsi = indicators.get('rsi', [])
            if rsi and not np.isnan(rsi[-1]):
                rsi_normalized = (rsi[-1] - 50) / 50  # Normalize to -1, 1
            else:
                rsi_normalized = 0
            features.append(rsi_normalized)
            
            # MACD signal
            macd_line = indicators.get('macd_line', [])
            macd_signal = indicators.get('macd_signal', [])
            if macd_line and macd_signal and not (np.isnan(macd_line[-1]) or np.isnan(macd_signal[-1])):
                macd_diff = macd_line[-1] - macd_signal[-1]
            else:
                macd_diff = 0
            features.append(macd_diff)
            
            # Bollinger Bands position
            bb_upper = indicators.get('bb_upper', [])
            bb_lower = indicators.get('bb_lower', [])
            if bb_upper and bb_lower and not (np.isnan(bb_upper[-1]) or np.isnan(bb_lower[-1])):
                bb_range = bb_upper[-1] - bb_lower[-1]
                bb_position = (closes[-1] - bb_lower[-1]) / bb_range if bb_range > 0 else 0.5
            else:
                bb_position = 0.5
            features.append(bb_position)
            
            # Volatility (ATR normalized)
            atr = indicators.get('atr', [])
            if atr and not np.isnan(atr[-1]):
                volatility = atr[-1] / closes[-1] if closes[-1] > 0 else 0
            else:
                volatility = 0.01
            features.append(volatility)
            
            # Volume ratio (if available)
            volumes = [p.volume for p in historical_data if p.volume > 0]
            if len(volumes) >= 20:
                avg_volume = sum(volumes[-20:]) / 20
                volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
            else:
                volume_ratio = 1
            features.append(volume_ratio)
            
            # Trend strength
            if len(closes) >= 20:
                trend_strength = (closes[-1] - closes[-20]) / closes[-20]
            else:
                trend_strength = 0
            features.append(trend_strength)
            
        except Exception as e:
            logger.warning(f"Error calculating features for {pair}: {e}")
            return self._generate_mock_features()
        
        # Pad or trim to fixed length
        while len(features) < 20:
            features.append(0.0)
        
        return np.array(features[:20])
    
    def _generate_mock_features(self) -> np.ndarray:
        """Generate mock features when real data is not available."""
        # Generate realistic-looking random features
        features = []
        
        # Price momentum
        features.append(random.gauss(0, 0.02))
        
        # SMA ratio
        features.append(random.gauss(0, 0.01))
        
        # RSI normalized
        features.append(random.uniform(-0.4, 0.4))
        
        # MACD signal
        features.append(random.gauss(0, 0.001))
        
        # BB position
        features.append(random.uniform(0.1, 0.9))
        
        # Volatility
        features.append(random.uniform(0.005, 0.03))
        
        # Volume ratio
        features.append(random.uniform(0.5, 2.0))
        
        # Trend strength
        features.append(random.gauss(0, 0.05))
        
        # Additional features
        for _ in range(12):
            features.append(random.gauss(0, 0.1))
        
        return np.array(features)
    
    def _create_signal_from_prediction(self, pair: str, prediction_data: Dict[str, Any]) -> List[TradeSignal]:
        """Convert ML prediction to trading signal."""
        prediction = prediction_data['prediction']
        
        if (prediction.prediction == SignalType.HOLD or 
            prediction.confidence < self.min_confidence):
            return []
        
        # Calculate signal strength based on confidence and probability
        signal_strength = min(prediction.confidence * prediction.probability, 1.0)
        
        # Create trading signal
        signal = TradeSignal(
            pair=pair,
            signal=prediction.prediction,
            strength=signal_strength,
            price=0.0,  # Will be filled by calling code
            timestamp=datetime.utcnow(),
            strategy="ml",
            confidence=prediction.confidence,
            indicators=[]  # ML doesn't use traditional indicators
        )
        
        return [signal]
    
    async def _retrain_model(self, pair: str, model: MockMLModel, 
                           historical_data: Optional[List[PriceData]]):
        """Retrain ML model with new data."""
        logger.info(f"Retraining ML model for {pair}")
        
        # Mock retraining process
        await asyncio.sleep(0.1)  # Simulate training time
        
        # Update model accuracy based on recent performance
        recent_accuracy = self._calculate_recent_accuracy(pair)
        if recent_accuracy is not None:
            # Blend recent accuracy with model accuracy
            model.model_accuracy = 0.7 * model.model_accuracy + 0.3 * recent_accuracy
        
        model._mock_training()
        logger.info(f"Model retrained for {pair}. New accuracy: {model.model_accuracy:.3f}")
    
    def _calculate_recent_accuracy(self, pair: str) -> Optional[float]:
        """Calculate recent prediction accuracy for a pair."""
        recent_predictions = [
            p for p in self.prediction_history 
            if p['pair'] == pair and p['actual_outcome'] is not None
        ]
        
        if len(recent_predictions) < 5:
            return None
        
        correct = sum(1 for p in recent_predictions[-20:] 
                     if p['prediction'] == p['actual_outcome'])
        return correct / min(len(recent_predictions), 20)
    
    def _clean_cache(self):
        """Clean old cache entries."""
        current_time = datetime.utcnow()
        keys_to_remove = []
        
        for key, data in self.prediction_cache.items():
            if (current_time - data['timestamp']).seconds > self.cache_duration_minutes * 60 * 2:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.prediction_cache[key]
    
    def update_prediction_outcome(self, pair: str, timestamp: datetime, 
                                actual_signal: SignalType):
        """Update prediction history with actual outcomes for model improvement."""
        for prediction in self.prediction_history:
            if (prediction['pair'] == pair and 
                abs((prediction['timestamp'] - timestamp).seconds) < 3600):  # Within 1 hour
                prediction['actual_outcome'] = actual_signal.value
                break
    
    def get_model_performance(self, pair: Optional[str] = None) -> Dict[str, Any]:
        """Get ML model performance metrics."""
        if pair:
            model = self.models.get(pair)
            if not model:
                return {}
            
            model_info = model.get_model_info()
            recent_accuracy = self._calculate_recent_accuracy(pair)
            
            return {
                'pair': pair,
                'model_info': model_info,
                'recent_accuracy': recent_accuracy,
                'predictions_made': sum(1 for p in self.prediction_history if p['pair'] == pair)
            }
        else:
            # Overall performance
            total_predictions = len(self.prediction_history)
            predictions_with_outcomes = [
                p for p in self.prediction_history 
                if p['actual_outcome'] is not None
            ]
            
            accuracy = 0.0
            if predictions_with_outcomes:
                correct = sum(1 for p in predictions_with_outcomes 
                            if p['prediction'] == p['actual_outcome'])
                accuracy = correct / len(predictions_with_outcomes)
            
            return {
                'total_predictions': total_predictions,
                'predictions_with_outcomes': len(predictions_with_outcomes),
                'overall_accuracy': accuracy,
                'active_models': len(self.models),
                'model_types': {pair: model.model_type for pair, model in self.models.items()}
            }

# Import asyncio for async operations
import asyncio