from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and profile management"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # Relationship with predictions
    predictions = db.relationship('Prediction', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def __init__(self, name, email, password):
        self.name = name
        self.email = email.lower()
        self.set_password(password)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'dateOfBirth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'total_predictions': self.predictions.count()
        }

    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        return User.query.filter_by(email=email.lower()).first()

    @staticmethod
    def create_user(name, email, password):
        """Create new user"""
        if User.find_by_email(email):
            raise ValueError("User with this email already exists")

        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return user

    def __repr__(self):
        return f'<User {self.email}>'


class Prediction(db.Model):
    """Prediction model for storing stroke risk assessments"""

    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    # Prediction Results
    risk_level = db.Column(db.String(20), nullable=False)  # LOW, MODERATE, HIGH
    probability_score = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.String(20))  # HIGH, MEDIUM, LOW

    # Patient Data (input parameters)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    hypertension = db.Column(db.Boolean, nullable=False)
    heart_disease = db.Column(db.Boolean, nullable=False)
    ever_married = db.Column(db.String(10), nullable=False)
    work_type = db.Column(db.String(20), nullable=False)
    residence_type = db.Column(db.String(10), nullable=False)
    avg_glucose_level = db.Column(db.Float, nullable=False)
    bmi = db.Column(db.Float, nullable=False)
    smoking_status = db.Column(db.String(20), nullable=False)
    family_history_stroke = db.Column(db.Boolean, default=False)
    alcohol_consumption = db.Column(db.String(20), default='Never')

    # Model Information
    model_name = db.Column(db.String(50), default='Logistic Regression')
    model_version = db.Column(db.String(20), default='1.0.0')

    # Risk Factors & Recommendations (stored as JSON)
    risk_factors = db.Column(db.Text)  # JSON array
    recommendations = db.Column(db.Text)  # JSON array

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id, prediction_data, patient_data):
        self.user_id = user_id

        # Prediction results
        self.risk_level = prediction_data.get('risk_level', 'UNKNOWN')
        self.probability_score = prediction_data.get('probability_score', 0.0)
        self.confidence = prediction_data.get('confidence', 'MEDIUM')

        # Patient data
        self.age = patient_data.get('age')
        self.gender = patient_data.get('gender')
        self.hypertension = bool(patient_data.get('hypertension', 0))
        self.heart_disease = bool(patient_data.get('heart_disease', 0))
        self.ever_married = patient_data.get('ever_married', 'Unknown')
        self.work_type = patient_data.get('work_type', 'Unknown')
        self.residence_type = patient_data.get('Residence_type', patient_data.get('residence_type', 'Urban'))
        self.avg_glucose_level = patient_data.get('avg_glucose_level')
        self.bmi = patient_data.get('bmi')
        self.smoking_status = patient_data.get('smoking_status', 'Unknown')
        self.family_history_stroke = bool(patient_data.get('family_history_stroke', 0))
        self.alcohol_consumption = patient_data.get('alcohol_consumption', 'Never')

        # Model info
        self.model_name = prediction_data.get('model_name', 'Logistic Regression')
        self.model_version = prediction_data.get('model_version', '1.0.0')

        # Store arrays as JSON strings
        self.risk_factors = json.dumps(prediction_data.get('risk_factors', []))
        self.recommendations = json.dumps(prediction_data.get('recommendations', []))

    def get_risk_factors(self):
        """Get risk factors as Python list"""
        try:
            return json.loads(self.risk_factors) if self.risk_factors else []
        except (json.JSONDecodeError, TypeError):
            return []

    def get_recommendations(self):
        """Get recommendations as Python list"""
        try:
            return json.loads(self.recommendations) if self.recommendations else []
        except (json.JSONDecodeError, TypeError):
            return []

    def get_risk_color(self):
        """Get color code for risk level"""
        colors = {
            'LOW': '#4caf50',
            'MODERATE': '#ff9800',
            'HIGH': '#f44336'
        }
        return colors.get(self.risk_level, '#757575')

    def get_risk_emoji(self):
        """Get emoji for risk level"""
        emojis = {
            'LOW': '🟢',
            'MODERATE': '🟡',
            'HIGH': '🔴'
        }
        return emojis.get(self.risk_level, '⚪')

    def to_dict(self):
        """Convert prediction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'risk_level': self.risk_level,
            'probability_score': self.probability_score,
            'confidence': self.confidence,
            'risk_factors': self.get_risk_factors(),
            'recommendations': self.get_recommendations(),
            'patient_summary': {
                'age': self.age,
                'gender': self.gender,
                'bmi': round(self.bmi, 1) if self.bmi else None,
                'glucose_level': round(self.avg_glucose_level, 1) if self.avg_glucose_level else None,
                'hypertension': self.hypertension,
                'heart_disease': self.heart_disease,
                'smoking_status': self.smoking_status
            },
            'model_info': {
                'model_name': self.model_name,
                'model_version': self.model_version
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'risk_color': self.get_risk_color(),
            'risk_emoji': self.get_risk_emoji()
        }

    @staticmethod
    def get_user_predictions(user_id, limit=None):
        """Get predictions for a specific user"""
        query = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_user_statistics(user_id):
        """Get statistics for a user's predictions"""
        predictions = Prediction.query.filter_by(user_id=user_id).all()

        if not predictions:
            return {
                'total_predictions': 0,
                'risk_distribution': {'LOW': 0, 'MODERATE': 0, 'HIGH': 0},
                'average_age': 0,
                'recent_predictions': 0,
                'average_probability': 0
            }

        total = len(predictions)
        risk_counts = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0}
        ages = []
        probabilities = []

        # Calculate recent predictions (last 7 days)
        recent_count = 0
        recent_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = recent_date.replace(day=recent_date.day-7) if recent_date.day > 7 else recent_date.replace(month=recent_date.month-1, day=30)

        for pred in predictions:
            # Count risk levels
            if pred.risk_level in risk_counts:
                risk_counts[pred.risk_level] += 1

            # Collect ages and probabilities
            if pred.age:
                ages.append(pred.age)
            if pred.probability_score is not None:
                probabilities.append(pred.probability_score)

            # Count recent predictions
            if pred.created_at and pred.created_at >= week_ago:
                recent_count += 1

        return {
            'total_predictions': total,
            'risk_distribution': risk_counts,
            'average_age': round(sum(ages) / len(ages), 1) if ages else 0,
            'recent_predictions': recent_count,
            'average_probability': round(sum(probabilities) / len(probabilities), 3) if probabilities else 0
        }

    def __repr__(self):
        return f'<Prediction {self.id}: {self.risk_level} risk for User {self.user_id}>'


def init_db(app):
    """Initialize database with Flask app"""
    with app.app_context():
        # Create all tables
        db.create_all()

        # Create indexes for better performance
        try:
            # Create indexes for better performance (compatible with both SQLite and PostgreSQL)
            with db.engine.connect() as conn:
                # Index on user email for faster lookups
                conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)'))

                # Index on prediction user_id and created_at for faster queries
                conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_predictions_user_created ON predictions(user_id, created_at DESC)'))

                # Index on prediction risk_level for statistics
                conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_predictions_risk_level ON predictions(risk_level)'))

                conn.commit()

        except Exception as e:
            print(f"Index creation warning: {e}")

        print("✅ Database tables created successfully!")


def seed_demo_data():
    """Seed database with demo data (optional)"""
    try:
        # Check if demo user already exists
        demo_user = User.find_by_email('demo@strokeprediction.com')

        if not demo_user:
            # Create demo user
            demo_user = User.create_user(
                name='Demo User',
                email='demo@strokeprediction.com',
                password='demo123'
            )

            # Create sample predictions
            sample_predictions = [
                {
                    'prediction_data': {
                        'risk_level': 'LOW',
                        'probability_score': 0.15,
                        'confidence': 'HIGH',
                        'risk_factors': ['Age within normal range', 'Healthy BMI', 'No smoking'],
                        'recommendations': ['Maintain healthy lifestyle', 'Regular checkups', 'Continue exercise routine']
                    },
                    'patient_data': {
                        'age': 28,
                        'gender': 'Female',
                        'hypertension': 0,
                        'heart_disease': 0,
                        'ever_married': 'Yes',
                        'work_type': 'Private',
                        'Residence_type': 'Urban',
                        'avg_glucose_level': 85.5,
                        'bmi': 22.3,
                        'smoking_status': 'never smoked',
                        'family_history_stroke': 0,
                        'alcohol_consumption': 'Occasionally'
                    }
                },
                {
                    'prediction_data': {
                        'risk_level': 'MODERATE',
                        'probability_score': 0.45,
                        'confidence': 'MEDIUM',
                        'risk_factors': ['Elevated glucose level', 'Overweight BMI', 'Hypertension'],
                        'recommendations': ['Consult healthcare provider', 'Monitor blood pressure', 'Consider dietary changes']
                    },
                    'patient_data': {
                        'age': 52,
                        'gender': 'Male',
                        'hypertension': 1,
                        'heart_disease': 0,
                        'ever_married': 'Yes',
                        'work_type': 'Govt_job',
                        'Residence_type': 'Rural',
                        'avg_glucose_level': 140.2,
                        'bmi': 28.7,
                        'smoking_status': 'formerly smoked',
                        'family_history_stroke': 1,
                        'alcohol_consumption': 'Regularly'
                    }
                }
            ]

            for pred_data in sample_predictions:
                prediction = Prediction(
                    user_id=demo_user.id,
                    prediction_data=pred_data['prediction_data'],
                    patient_data=pred_data['patient_data']
                )
                db.session.add(prediction)

            db.session.commit()
            print("✅ Demo data seeded successfully!")

    except Exception as e:
        print(f"Demo data seeding error: {e}")
        db.session.rollback()
