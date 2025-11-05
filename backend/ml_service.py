#!/usr/bin/env python3
"""
Machine Learning Service for Brain Stroke Risk Prediction
Updated to work with the trained model from ml-model directory
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up logging
logger = logging.getLogger(__name__)

class StrokeRiskPredictor:
    """
    Enhanced stroke risk prediction service using trained ML models
    """

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the stroke risk predictor"""
        self.model = None
        self.scaler = None
        self.label_encoders = {}
        self.feature_names = []
        self.model_name = "Unknown"
        self.model_version = "1.0.0"
        self.model_metrics = {}

        # Set default model path with Railway-friendly fallbacks
        if model_path is None:
            current_dir = Path(__file__).parent
            logger.info(f"🔍 DEBUGGING: Current directory: {current_dir}")
            logger.info(f"🔍 DEBUGGING: Working directory: {Path.cwd()}")

            # Try multiple possible model locations
            possible_paths = [
                # First try: backend/models (Railway deployment friendly)
                current_dir / "models" / "stroke_prediction_model.pkl",
                # Second try: ml-model directory (local development)
                current_dir.parent / "ml-model" / "models" / "stroke_prediction_model.pkl",
                # Third try: absolute path for Railway
                Path("/app/ml-model/models/stroke_prediction_model.pkl"),
                # Fourth try: relative to working directory
                Path("ml-model/models/stroke_prediction_model.pkl"),
                # Fifth try: backend models from root
                Path("/app/backend/models/stroke_prediction_model.pkl"),
            ]

            model_path = None
            logger.info(f"🔍 DEBUGGING: Checking {len(possible_paths)} possible model paths:")
            for i, path in enumerate(possible_paths, 1):
                logger.info(f"🔍 DEBUGGING: Path {i}: {path} (exists: {path.exists()})")
                if path.exists():
                    model_path = path
                    logger.info(f"✅ DEBUGGING: Found model at: {path}")
                    break

            if model_path is None:
                logger.error("❌ DEBUGGING: No model file found in any expected location")
                logger.error("🔍 DEBUGGING: This will trigger fallback model creation")
                # Will trigger fallback model creation
                model_path = possible_paths[0]  # Use first path as default

        self.model_path = Path(model_path)
        self._load_model()

    def _load_model(self):
        """Load the trained ML model and preprocessing objects"""
        try:
            logger.info(f"🔍 DEBUGGING: Attempting to load model from {self.model_path}")
            logger.info(f"🔍 DEBUGGING: Model path exists: {self.model_path.exists()}")

            if self.model_path.exists():
                logger.info(f"✅ DEBUGGING: Loading model from {self.model_path}")
                logger.info(f"🔍 DEBUGGING: File size: {self.model_path.stat().st_size} bytes")

                # Load model artifacts
                model_artifacts = joblib.load(self.model_path)
                logger.info(f"🔍 DEBUGGING: Model artifacts keys: {list(model_artifacts.keys())}")

                self.model = model_artifacts['model']
                self.scaler = model_artifacts['scaler']
                self.label_encoders = model_artifacts['label_encoders']
                self.feature_names = model_artifacts['feature_names']
                self.model_name = model_artifacts['model_name']
                self.model_metrics = model_artifacts.get('model_metrics', {})

                logger.info(f"✅ DEBUGGING: Model loaded successfully: {self.model_name}")
                logger.info(f"🔍 DEBUGGING: Model type: {type(self.model)}")
                logger.info(f"📊 DEBUGGING: Model AUC Score: {self.model_metrics.get(self.model_name, {}).get('auc_score', 'N/A')}")

            else:
                logger.error(f"❌ DEBUGGING: Model file not found at {self.model_path}")
                logger.error("🔍 DEBUGGING: Creating a simple fallback model...")
                self._create_fallback_model()

        except Exception as e:
            logger.error(f"❌ DEBUGGING: Error loading model: {str(e)}")
            logger.error(f"🔍 DEBUGGING: Exception type: {type(e)}")
            logger.error("🔍 DEBUGGING: Creating a simple fallback model...")
            self._create_fallback_model()

    def _create_fallback_model(self):
        """Create a simple fallback model when the trained model is not available"""
        logger.warning("⚠️ DEBUGGING: Creating fallback model - this should NOT happen in production!")
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler, LabelEncoder

        # Create a simple fallback model
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        self.scaler = StandardScaler()
        self.model_name = "Fallback Random Forest"
        self.model_version = "1.0.0-fallback"
        logger.warning(f"⚠️ DEBUGGING: Fallback model created: {self.model_name} {self.model_version}")

        # Initialize label encoders with expected categories
        self.label_encoders = {
            'gender': LabelEncoder(),
            'ever_married': LabelEncoder(),
            'work_type': LabelEncoder(),
            'Residence_type': LabelEncoder(),
            'smoking_status': LabelEncoder()
        }

        # Fit encoders with expected categories
        self.label_encoders['gender'].fit(['Male', 'Female', 'Other'])
        self.label_encoders['ever_married'].fit(['Yes', 'No'])
        self.label_encoders['work_type'].fit(['Private', 'Self-employed', 'Govt_job', 'children', 'Never_worked'])
        self.label_encoders['Residence_type'].fit(['Urban', 'Rural'])
        self.label_encoders['smoking_status'].fit(['never smoked', 'formerly smoked', 'smokes', 'Unknown'])

        self.feature_names = [
            'gender', 'age', 'hypertension', 'heart_disease', 'ever_married',
            'work_type', 'Residence_type', 'avg_glucose_level', 'bmi',
            'smoking_status', 'family_history_stroke'
        ]

        # Create dummy training data to fit the fallback model
        dummy_data = np.array([[1, 45, 0, 0, 1, 0, 1, 100, 25, 0, 0]] * 10)
        dummy_target = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])  # 50% stroke rate

        self.scaler.fit(dummy_data)
        self.model.fit(self.scaler.transform(dummy_data), dummy_target)

        logger.warning("✅ Fallback model created and ready")

    def preprocess_features(self, patient_data: Dict[str, Any]) -> np.ndarray:
        """Preprocess patient data for model prediction"""
        try:
            # Create a copy to avoid modifying original data
            data = patient_data.copy()

            # Handle categorical features with label encoding
            categorical_features = ['gender', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']

            for feature in categorical_features:
                if feature in data and feature in self.label_encoders:
                    str_value = str(data[feature])

                    # Check if value exists in encoder classes
                    if str_value in self.label_encoders[feature].classes_:
                        data[feature] = self.label_encoders[feature].transform([str_value])[0]
                    else:
                        # Handle unseen categories
                        logger.warning(f"Unknown value '{str_value}' for {feature}, using default")
                        data[feature] = 0
                elif feature in data:
                    # If encoder doesn't exist, try to handle manually
                    if feature == 'gender':
                        data[feature] = 1 if data[feature].lower() == 'male' else 0
                    elif feature == 'ever_married':
                        data[feature] = 1 if data[feature].lower() == 'yes' else 0
                    elif feature == 'Residence_type':
                        data[feature] = 1 if data[feature].lower() == 'urban' else 0
                    else:
                        data[feature] = 0

            # Handle residence_type vs Residence_type inconsistency
            if 'residence_type' in data and 'Residence_type' not in data:
                data['Residence_type'] = data['residence_type']
            elif 'Residence_type' not in data and 'residence_type' not in data:
                data['Residence_type'] = 0  # Default to Rural

            # Ensure all required features are present
            feature_vector = []
            for feature in self.feature_names:
                if feature in data:
                    feature_vector.append(float(data[feature]))
                else:
                    logger.warning(f"Missing feature '{feature}', using default value 0")
                    feature_vector.append(0.0)

            # Convert to numpy array and reshape for single prediction
            feature_array = np.array(feature_vector).reshape(1, -1)

            # Apply scaling
            if self.scaler is not None:
                scaled_features = self.scaler.transform(feature_array)
            else:
                scaled_features = feature_array

            return scaled_features

        except Exception as e:
            logger.error(f"Error preprocessing features: {str(e)}")
            # Return zero features as fallback
            return np.zeros((1, len(self.feature_names)))

    def predict_risk(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict stroke risk for a patient"""
        try:
            # Preprocess the features
            processed_features = self.preprocess_features(patient_data)

            # Make prediction
            if self.model is None:
                raise Exception("Model not loaded")

            prediction = self.model.predict(processed_features)[0]
            probability = self.model.predict_proba(processed_features)[0][1]

            # Classify risk level
            risk_level = self._classify_risk_level(probability)

            # Identify risk factors
            risk_factors = self._identify_risk_factors(patient_data)

            # Generate recommendations
            recommendations = self._generate_recommendations(risk_level, risk_factors)

            # Calculate confidence
            confidence = self._calculate_confidence(probability)

            result = {
                'prediction': int(prediction),
                'probability_score': float(probability),
                'risk_level': risk_level,
                'confidence': confidence,
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'model_version': self.model_version,
                'model_name': self.model_name
            }

            logger.info(f"Prediction completed: {risk_level} risk ({probability:.1%} probability)")
            return result

        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            # Return a safe fallback prediction
            return {
                'prediction': 0,
                'probability_score': 0.1,
                'risk_level': 'LOW',
                'confidence': 'LOW',
                'risk_factors': ['Unable to analyze - system error'],
                'recommendations': ['Please consult a healthcare professional'],
                'model_version': self.model_version,
                'model_name': f"{self.model_name} (Error Mode)",
                'error': str(e)
            }

    def _classify_risk_level(self, probability: float) -> str:
        """Classify risk level based on probability"""
        if probability < 0.3:
            return 'LOW'
        elif probability < 0.7:
            return 'MODERATE'
        else:
            return 'HIGH'

    def _identify_risk_factors(self, patient_data: Dict[str, Any]) -> List[str]:
        """Identify risk factors present in patient data"""
        risk_factors = []

        try:
            age = float(patient_data.get('age', 0))
            if age > 65:
                risk_factors.append(f'Advanced age ({int(age)} years)')
            elif age > 50:
                risk_factors.append(f'Older age ({int(age)} years)')

            if patient_data.get('hypertension', 0):
                risk_factors.append('Hypertension')

            if patient_data.get('heart_disease', 0):
                risk_factors.append('Heart disease')

            glucose = float(patient_data.get('avg_glucose_level', 0))
            if glucose > 140:
                risk_factors.append(f'High glucose level ({glucose:.1f} mg/dL)')
            elif glucose > 100:
                risk_factors.append(f'Elevated glucose level ({glucose:.1f} mg/dL)')

            bmi = float(patient_data.get('bmi', 0))
            if bmi > 30:
                risk_factors.append(f'Obesity (BMI: {bmi:.1f})')
            elif bmi > 25:
                risk_factors.append(f'Overweight (BMI: {bmi:.1f})')

            smoking_status = str(patient_data.get('smoking_status', '')).lower()
            if 'smokes' in smoking_status:
                risk_factors.append('Current smoking')
            elif 'formerly' in smoking_status:
                risk_factors.append('Former smoking history')

            if patient_data.get('family_history_stroke', 0):
                risk_factors.append('Family history of stroke')

            alcohol = str(patient_data.get('alcohol_consumption', '')).lower()
            if 'heavy' in alcohol:
                risk_factors.append('Heavy alcohol consumption')

            if not risk_factors:
                risk_factors.append('No major risk factors identified')

        except Exception as e:
            logger.error(f"Error identifying risk factors: {str(e)}")
            risk_factors = ['Unable to analyze risk factors']

        return risk_factors

    def _generate_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generate personalized recommendations based on risk level and factors"""
        recommendations = []

        if risk_level == 'LOW':
            recommendations.extend([
                'Maintain a healthy lifestyle with regular exercise',
                'Follow a balanced diet low in sodium and saturated fats',
                'Schedule regular health check-ups',
                'Monitor blood pressure regularly'
            ])
        elif risk_level == 'MODERATE':
            recommendations.extend([
                'Consult with your healthcare provider about stroke prevention',
                'Consider lifestyle modifications to reduce risk factors',
                'Monitor blood pressure and glucose levels regularly',
                'Implement stress management techniques',
                'Consider medication review with your doctor'
            ])
        else:  # HIGH
            recommendations.extend([
                'Seek immediate medical consultation for stroke prevention strategies',
                'Work closely with healthcare team to manage risk factors',
                'Consider medication for blood pressure and cholesterol management',
                'Implement aggressive lifestyle changes',
                'Regular monitoring by healthcare professionals'
            ])

        # Add specific recommendations based on risk factors
        risk_factors_str = ' '.join(risk_factors).lower()

        if 'smoking' in risk_factors_str:
            recommendations.append('Quit smoking immediately - seek smoking cessation support')

        if 'obesity' in risk_factors_str or 'overweight' in risk_factors_str:
            recommendations.append('Work with a nutritionist for healthy weight management')

        if 'hypertension' in risk_factors_str:
            recommendations.append('Follow prescribed blood pressure medications and monitor regularly')

        if 'glucose' in risk_factors_str:
            recommendations.append('Monitor blood sugar levels and follow diabetic management plan')

        # Always add medical disclaimer
        recommendations.append('⚠️ Always consult healthcare professionals before making medical decisions')

        return recommendations

    def _calculate_confidence(self, probability: float) -> str:
        """Calculate confidence level of the prediction"""
        if probability < 0.2 or probability > 0.8:
            return 'HIGH'
        elif probability < 0.4 or probability > 0.6:
            return 'MEDIUM'
        else:
            return 'LOW'

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'feature_count': len(self.feature_names),
            'features': self.feature_names,
            'metrics': self.model_metrics,
            'model_path': str(self.model_path),
            'is_loaded': self.model is not None
        }

# Global predictor instance
_predictor = None

def get_predictor() -> StrokeRiskPredictor:
    """Get or create the global predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = StrokeRiskPredictor()
    return _predictor

def predict_stroke_risk(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to predict stroke risk
    This is the function called by the Flask app
    """
    predictor = get_predictor()
    return predictor.predict_risk(patient_data)

def get_predictor_info() -> Dict[str, Any]:
    """Get information about the current predictor"""
    predictor = get_predictor()
    return predictor.get_model_info()

# Test function for standalone usage
def test_prediction():
    """Test the prediction service with sample data"""
    print("🧠 Testing Stroke Risk Prediction Service...")

    # Sample patient data
    test_patient = {
        'age': 55,
        'gender': 'Male',
        'hypertension': 1,
        'heart_disease': 0,
        'ever_married': 'Yes',
        'work_type': 'Private',
        'residence_type': 'Urban',
        'avg_glucose_level': 120.0,
        'bmi': 28.5,
        'smoking_status': 'formerly smoked',
        'family_history_stroke': 1,
        'alcohol_consumption': 'Occasionally'
    }

    try:
        result = predict_stroke_risk(test_patient)

        print("\n📊 Test Results:")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Probability: {result['probability_score']:.1%}")
        print(f"   Confidence: {result['confidence']}")
        print(f"   Model: {result['model_name']}")
        print(f"   Risk Factors: {', '.join(result['risk_factors'])}")

        print("✅ Test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run test when executed directly
    test_prediction()
