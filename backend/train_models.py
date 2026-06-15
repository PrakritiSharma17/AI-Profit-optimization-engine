"""
Train AI demand models manually.
"""
from database import create_tables
from model_retraining import ModelRetrainingPipeline


def main():
    create_tables()
    pipeline = ModelRetrainingPipeline(check_interval_hours=24)
    pipeline.retrain_all_models(force=True)

if __name__ == '__main__':
    main()
