#!/usr/bin/env python3
"""
Brain Stroke Risk Prediction API with PostgreSQL Database
Production-ready Flask application for Railway deployment
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_migrate import Migrate
import traceback
import bcrypt
from flask import send_from_directory

# Import our modules
from config import get_config
from models import db, User, Prediction, init_db, seed_demo_data

# Import ML service
try:
    from ml_service import predict_stroke_risk, get_predictor_info
    ML_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML service not available - {e}")
    ML_SERVICE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_class = get_config()
    else:
        from config import config
        config_class = config[config_name]

    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app,
         origins=[
             'https://web-production-4ea93.up.railway.app', 
             'http://localhost:3000',
             'https://*.up.railway.app',  # Allow all Railway frontend deployments
             'https://frontend-production-*.up.railway.app'  # Specific pattern for frontend service
         ],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Accept'],
         supports_credentials=False)

    # Initialize database migration
    migrate = Migrate(app, db)

    # Initialize database
    with app.app_context():
        init_db(app)

        # Seed demo data in development
        if app.config.get('DEBUG', False):
            seed_demo_data()

    # Register error handlers
    register_error_handlers(app)

    # Register routes
    register_routes(app)

    return app

def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required',
            'status_code': 401
        }), 401

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested endpoint does not exist',
            'status_code': 404,
            'available_endpoints': [
                '/', '/api/info', '/api/auth/signup', '/api/auth/login',
                '/api/predict', '/api/history', '/api/statistics'
            ]
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

def register_routes(app):
    """Register all application routes"""

    @app.route('/', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'Brain Stroke Risk Prediction API',
            'version': '2.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if db.engine else 'disconnected',
            'ml_service': 'available' if ML_SERVICE_AVAILABLE else 'unavailable',
            'environment': os.environ.get('FLASK_ENV', 'development')
        })

    @app.route('/api/info', methods=['GET'])
    def api_info():
        """API information endpoint"""
        try:
            if ML_SERVICE_AVAILABLE:
                model_info = get_predictor_info()
            else:
                model_info = {'status': 'ML service not available'}

            return jsonify({
                'api_version': '2.0.0',
                'database': 'PostgreSQL',
                'endpoints': {
                    '/': 'Health check',
                    '/api/info': 'API information',
                    '/api/auth/signup': 'User registration',
                    '/api/auth/login': 'User authentication',
                    '/api/predict': 'Stroke risk prediction',
                    '/api/history': 'Get prediction history',
                    '/api/statistics': 'Get user statistics',
                    '/api/predictions/<id>': 'Delete specific prediction'
                },
                'model_info': model_info,
                'ml_service_status': 'available' if ML_SERVICE_AVAILABLE else 'unavailable'
            })
        except Exception as e:
            logger.error(f"Error in api_info: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    # Authentication Routes
    @app.route('/api/auth/signup', methods=['POST'])
    def signup():
        """User registration endpoint"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400

            data = request.get_json()
            required_fields = ['name', 'email', 'password']

            # Validate required fields
            for field in required_fields:
                if not data.get(field):
                    return jsonify({
                        'error': f'{field.title()} is required'
                    }), 400

            # Validate email format
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                return jsonify({'error': 'Invalid email format'}), 400

            # Check if user already exists
            if User.find_by_email(data['email']):
                return jsonify({'error': 'Email already registered'}), 400

            # Create new user
            user = User.create_user(
                name=data['name'].strip(),
                email=data['email'].strip(),
                password=data['password']
            )

            logger.info(f"New user registered: {user.email}")

            return jsonify({
                'status': 'success',
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201

        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            db.session.rollback()
            return jsonify({
                'error': 'Registration failed',
                'message': str(e)
            }), 500

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """User authentication endpoint"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400

            data = request.get_json()

            # Validate required fields
            if not data.get('email') or not data.get('password'):
                return jsonify({'error': 'Email and password required'}), 400

            # Find user
            user = User.find_by_email(data['email'])
            if not user:
                return jsonify({'error': 'Invalid credentials'}), 401

            # Check password
            if not user.check_password(data['password']):
                return jsonify({'error': 'Invalid credentials'}), 401

            # Check if user is active
            if not user.is_active:
                return jsonify({'error': 'Account is deactivated'}), 401

            # Update last login
            user.update_last_login()

            # Generate access token (simple token for demo)
            access_token = f"user_token_{user.id}_{datetime.utcnow().timestamp()}"

            logger.info(f"User logged in: {user.email}")

            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'access_token': access_token,
                'user': user.to_dict()
            })

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({
                'error': 'Login failed',
                'message': str(e)
            }), 500

    @app.route('/api/auth/validate', methods=['GET'])
    def validate_token():
        """Token validation endpoint"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'valid': False, 'error': 'No token provided'}), 401

            token = auth_header.split(' ')[1]

            # Simple token validation for demo
            if token.startswith('user_token_'):
                parts = token.split('_')
                if len(parts) >= 3:
                    user_id = int(parts[2])
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        return jsonify({
                            'valid': True,
                            'user': user.to_dict()
                        })

            return jsonify({'valid': False, 'error': 'Invalid token'}), 401

        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return jsonify({'valid': False, 'error': 'Token validation failed'}), 401

    # Helper function to get current user
    def get_current_user():
        """Get current user from token"""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return None

            token = auth_header.split(' ')[1]

            # Simple token parsing for demo
            if token.startswith('user_token_'):
                parts = token.split('_')
                if len(parts) >= 3:
                    user_id = int(parts[2])
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        return user
            return None
        except:
            return None

    # Prediction Routes
    @app.route('/api/predict', methods=['POST'])
    def predict():
        """Main prediction endpoint"""
        try:
            # Get current user (optional for demo)
            current_user = get_current_user()

            # Validate request
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400

            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400

            # Define required fields
            required_fields = [
                'age', 'gender', 'hypertension', 'heart_disease', 'ever_married',
                'work_type', 'avg_glucose_level', 'bmi', 'smoking_status'
            ]

            # Check for missing fields
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)

            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400

            # Validate data ranges
            try:
                age = float(data['age'])
                if age < 0 or age > 120:
                    return jsonify({'error': 'Age must be between 0 and 120'}), 400

                glucose_level = float(data['avg_glucose_level'])
                if glucose_level < 0 or glucose_level > 500:
                    return jsonify({'error': 'Glucose level must be between 0 and 500'}), 400

                bmi = float(data['bmi'])
                if bmi < 10 or bmi > 60:
                    return jsonify({'error': 'BMI must be between 10 and 60'}), 400

            except (ValueError, TypeError) as e:
                return jsonify({'error': f'Invalid numeric values: {str(e)}'}), 400

            # Prepare data for ML model
            patient_data = {
                'age': age,
                'gender': str(data['gender']),
                'hypertension': int(bool(data['hypertension'])),
                'heart_disease': int(bool(data['heart_disease'])),
                'ever_married': str(data['ever_married']),
                'work_type': str(data['work_type']),
                'Residence_type': str(data.get('residence_type', data.get('Residence_type', 'Urban'))),
                'avg_glucose_level': glucose_level,
                'bmi': bmi,
                'smoking_status': str(data['smoking_status']),
                'family_history_stroke': int(bool(data.get('family_history_stroke', 0))),
                'alcohol_consumption': str(data.get('alcohol_consumption', 'Never'))
            }

            logger.info(f"Processing prediction request for age={age}, gender={patient_data['gender']}")

            # Get ML prediction
            if ML_SERVICE_AVAILABLE:
                try:
                    prediction_result = predict_stroke_risk(patient_data)
                except Exception as e:
                    logger.error(f"ML prediction failed: {str(e)}")
                    return jsonify({'error': f'ML service error: {str(e)}'}), 500
            else:
                # Fallback prediction for demo
                prediction_result = {
                    'risk_level': 'MODERATE',
                    'probability_score': 0.35,
                    'confidence': 'MEDIUM',
                    'risk_factors': ['Demo mode - ML service not available'],
                    'recommendations': ['Consult healthcare provider', 'Regular health monitoring'],
                    'model_name': 'Demo Model',
                    'model_version': '1.0.0'
                }

            # Store prediction in database if user is authenticated
            if current_user:
                try:
                    prediction = Prediction(
                        user_id=current_user.id,
                        prediction_data=prediction_result,
                        patient_data=patient_data
                    )
                    db.session.add(prediction)
                    db.session.commit()

                    prediction_id = prediction.id
                    logger.info(f"Prediction saved with ID: {prediction_id}")
                except Exception as e:
                    logger.error(f"Failed to save prediction: {str(e)}")
                    db.session.rollback()
                    # Continue without saving - don't fail the prediction

            # Format response
            response = {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'prediction': prediction_result,
                'patient_summary': {
                    'age': int(age),
                    'gender': patient_data['gender'],
                    'bmi': round(bmi, 1),
                    'glucose_level': round(glucose_level, 1)
                }
            }

            logger.info(f"Prediction completed: {prediction_result.get('risk_level', 'UNKNOWN')} risk")
            return jsonify(response)

        except Exception as e:
            logger.error(f"Error in prediction endpoint: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500

    @app.route('/api/history', methods=['GET'])
    def get_history():
        """Get prediction history"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Authentication required'}), 401

            # Get user's predictions
            predictions = Prediction.get_user_predictions(current_user.id)

            return jsonify({
                'status': 'success',
                'predictions': [pred.to_dict() for pred in predictions],
                'total_count': len(predictions),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in history endpoint: {str(e)}")
            return jsonify({
                'error': 'Failed to retrieve history',
                'message': str(e)
            }), 500

    @app.route('/api/statistics', methods=['GET'])
    def get_statistics():
        """Get user statistics"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Authentication required'}), 401

            # Get statistics for user
            stats = Prediction.get_user_statistics(current_user.id)

            return jsonify({
                'status': 'success',
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in statistics endpoint: {str(e)}")
            return jsonify({
                'error': 'Failed to retrieve statistics',
                'message': str(e)
            }), 500

    @app.route('/api/predictions/<int:prediction_id>', methods=['DELETE'])
    def delete_prediction(prediction_id):
        """Delete a specific prediction"""
        try:
            current_user = get_current_user()
            if not current_user:
                return jsonify({'error': 'Authentication required'}), 401

            # Find prediction
            prediction = Prediction.query.filter_by(
                id=prediction_id,
                user_id=current_user.id
            ).first()

            if not prediction:
                return jsonify({
                    'error': 'Prediction not found',
                    'message': f'No prediction found with ID {prediction_id}'
                }), 404

            # Delete prediction
            db.session.delete(prediction)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': f'Prediction {prediction_id} deleted successfully',
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in delete prediction endpoint: {str(e)}")
            db.session.rollback()
            return jsonify({
                'error': 'Failed to delete prediction',
                'message': str(e)
            }), 500

# Create app instance
app = create_app()

if __name__ == '__main__':
    print("🧠 Starting Brain Stroke Risk Prediction API...")
    print("=" * 60)
    print("API Endpoints:")
    print("  GET    /                 - Health check")
    print("  GET    /api/info         - API information")
    print("  POST   /api/auth/signup  - User registration")
    print("  POST   /api/auth/login   - User login")
    print("  GET    /api/auth/validate - Token validation")
    print("  POST   /api/predict      - Stroke risk prediction")
    print("  GET    /api/history      - Get prediction history")
    print("  GET    /api/statistics   - Get user statistics")
    print("  DELETE /api/predictions/<id> - Delete specific prediction")
    print("=" * 60)
    print(f"Database: {'✅ PostgreSQL' if 'postgresql' in app.config['SQLALCHEMY_DATABASE_URI'] else '⚠️ SQLite'}")
    print(f"ML Service: {'✅ Available' if ML_SERVICE_AVAILABLE else '❌ Available'}")
    print(f"Environment: {app.config.get('FLASK_ENV', 'development')}")
    print("=" * 60)

    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )
