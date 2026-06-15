"""
Automated Model Retraining Pipeline
Periodically retrains models with new data for continuous improvement
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from demand_prediction import DemandPredictionEngine
from database import execute_query


class ModelRetrainingPipeline:
    """Manages automated model retraining and performance monitoring"""
    
    def __init__(self, check_interval_hours=24):
        """
        Initialize retraining pipeline
        
        Args:
            check_interval_hours: How often to check for retraining need (default: 24 hours)
        """
        self.check_interval = check_interval_hours
        self.models = {
            'random_forest': DemandPredictionEngine(model_type='random_forest'),
            'xgboost': DemandPredictionEngine(model_type='xgboost')
        }
        self.last_retrain = {}
        self.scheduler_running = False
        self.scheduler_thread = None
    
    def should_retrain(self, model_type='random_forest', force=False):
        """
        Determine if model should be retrained
        
        Conditions for retraining:
        1. No training data in last check_interval hours (force=False)
        2. New transactions since last retrain (> 100 new records)
        3. Model accuracy has degraded
        4. Force flag is set
        """
        if force:
            return True
        
        try:
            # Check if model exists
            last_train = self._get_last_training_date(model_type)
            
            if last_train is None:
                print(f"Model '{model_type}' never trained. Retraining recommended.")
                return True
            
            hours_since_retrain = (datetime.now() - last_train).total_seconds() / 3600
            
            if hours_since_retrain < self.check_interval:
                return False
            
            # Check for new transactions
            new_transactions = execute_query(
                """SELECT COUNT(*) as count FROM transactions 
                   WHERE transaction_date > %s""",
                (last_train,),
                fetch_one=True
            )
            
            new_count = new_transactions['count'] if new_transactions else 0
            
            if new_count > 100:
                print(f"Found {new_count} new transactions. Retraining recommended.")
                return True
            
            # Check if accuracy degraded
            model_metrics = execute_query(
                """SELECT accuracy FROM model_metrics 
                   WHERE model_type = %s 
                   ORDER BY training_date DESC LIMIT 2""",
                (model_type,),
                fetch_all=True
            )
            
            if len(model_metrics) >= 2:
                latest_accuracy = model_metrics[0]['accuracy']
                previous_accuracy = model_metrics[1]['accuracy']
                
                accuracy_drop = previous_accuracy - latest_accuracy
                
                if accuracy_drop > 0.05:  # 5% drop
                    print(f"Model accuracy degraded by {accuracy_drop:.2%}. Retraining recommended.")
                    return True
            
            return False
        
        except Exception as e:
            print(f"Error checking retrain condition: {e}")
            return False
    
    def retrain_model(self, model_type='random_forest'):
        """Retrain specified model"""
        try:
            print(f"\n{'='*50}")
            print(f"Starting {model_type.upper()} Model Retraining")
            print(f"Time: {datetime.now().isoformat()}")
            print(f"{'='*50}")
            
            model = self.models.get(model_type)
            
            if model is None:
                print(f"Model '{model_type}' not found")
                return False
            
            # Train model
            success = model.train()
            
            if success:
                self.last_retrain[model_type] = datetime.now()
                print(f"\n✓ {model_type.upper()} Model Retraining Completed Successfully")
                print(f"Next scheduled retrain: {self._next_retrain_time()}")
                return True
            else:
                print(f"\n✗ {model_type.upper()} Model Retraining Failed")
                return False
        
        except Exception as e:
            print(f"Error during model retraining: {e}")
            return False
    
    def retrain_all_models(self, force=False):
        """Retrain all models"""
        results = {}
        
        for model_type in self.models.keys():
            if self.should_retrain(model_type, force=force):
                results[model_type] = self.retrain_model(model_type)
            else:
                results[model_type] = None  # Skipped
        
        return results
    
    def start_scheduled_retraining(self):
        """Start background scheduler for automatic retraining"""
        if self.scheduler_running:
            print("Scheduler is already running")
            return
        
        def schedule_job():
            # Schedule retraining job
            schedule.every(self.check_interval).hours.do(self.retrain_all_models)
            
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(target=schedule_job, daemon=True)
        self.scheduler_thread.start()
        
        print(f"✓ Model Retraining Scheduler Started")
        print(f"  Check interval: {self.check_interval} hours")
        print(f"  Next check: {self._next_retrain_time()}")
    
    def stop_scheduled_retraining(self):
        """Stop background scheduler"""
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("✓ Model Retraining Scheduler Stopped")
    
    def get_model_performance_report(self):
        """Get comprehensive model performance report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'models': {}
            }
            
            for model_type in self.models.keys():
                metrics = execute_query(
                    """SELECT * FROM model_metrics 
                       WHERE model_type = %s 
                       ORDER BY training_date DESC LIMIT 10""",
                    (model_type,),
                    fetch_all=True
                )
                
                if metrics:
                    latest = metrics[0]
                    trend = self._calculate_performance_trend(metrics)
                    accuracy_drop = 0.0
                    if len(metrics) >= 2:
                        accuracy_drop = float(metrics[1]['accuracy']) - float(latest['accuracy'])

                    drift_warning = 'Stable'
                    if trend == 'degrading' or accuracy_drop > 0.03:
                        drift_warning = 'Model drift detected. Retraining recommended.'
                    elif trend == 'unknown':
                        drift_warning = 'Insufficient history to verify drift.'

                    report['models'][model_type] = {
                        'latest_training': latest['training_date'].isoformat(),
                        'accuracy': float(latest['accuracy']),
                        'accuracy_drop': round(accuracy_drop, 4),
                        'mse': float(latest['mse']),
                        'rmse': float(latest['rmse']),
                        'mae': float(latest['mean_absolute_error']),
                        'samples_used': latest['samples_used'],
                        'version': latest['model_version'],
                        'performance_trend': trend,
                        'drift_warning': drift_warning,
                        'status': 'trained'
                    }
                else:
                    report['models'][model_type] = {
                        'status': 'not_trained',
                        'accuracy': 0,
                        'message': 'Model has never been trained'
                    }
            
            return report
        
        except Exception as e:
            print(f"Error generating performance report: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _get_last_training_date(self, model_type):
        """Get the last training date for a model"""
        try:
            result = execute_query(
                """SELECT MAX(training_date) as last_train FROM model_metrics 
                   WHERE model_type = %s""",
                (model_type,),
                fetch_one=True
            )
            
            if result and result['last_train']:
                return result['last_train']
            return None
        except Exception as e:
            print(f"Error getting last training date: {e}")
            return None
    
    def _next_retrain_time(self):
        """Calculate next scheduled retrain time"""
        last_retrain = max(self.last_retrain.values()) if self.last_retrain else datetime.now()
        next_retrain = last_retrain + timedelta(hours=self.check_interval)
        return next_retrain.isoformat()
    
    def _calculate_performance_trend(self, metrics):
        """Calculate if performance is improving or degrading"""
        if len(metrics) < 2:
            return 'unknown'
        
        latest_accuracy = metrics[0]['accuracy']
        previous_accuracy = metrics[1]['accuracy']
        
        if latest_accuracy > previous_accuracy:
            return 'improving'
        elif latest_accuracy < previous_accuracy:
            return 'degrading'
        else:
            return 'stable'
    
    def export_model_diagnostics(self):
        """Export detailed model diagnostics for analysis"""
        try:
            diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'scheduler_status': 'running' if self.scheduler_running else 'stopped',
                'check_interval_hours': self.check_interval,
                'models': {}
            }
            
            for model_type, model in self.models.items():
                diagnostics['models'][model_type] = {
                    'model_type': model_type,
                    'model_loaded': model.model is not None,
                    'scaler_loaded': model.scaler is not None,
                    'features_count': len(model.feature_names),
                    'model_path': model.model_path,
                    'should_retrain': self.should_retrain(model_type),
                    'last_retrain': self.last_retrain.get(model_type, 'Never').isoformat() 
                                   if isinstance(self.last_retrain.get(model_type), datetime) 
                                   else self.last_retrain.get(model_type, 'Never')
                }
            
            return diagnostics
        
        except Exception as e:
            print(f"Error exporting diagnostics: {e}")
            return {'error': str(e)}
