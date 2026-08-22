from celery import Celery

celery_app = Celery(
    'gaia',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

celery_app.conf.task_routes = {
    'backend.services.ml_service.*': {'queue': 'ml'},
}

@celery_app.task
def diagnose_image_async(image_path: str, model_key: str):
    # Load model and run inference
    pass

@celery_app.task
def send_sms_async(phone: str, message: str):
    from backend.services.sms_service import SMSService
    sms = SMSService()
    sms.send_sms(phone, message)
