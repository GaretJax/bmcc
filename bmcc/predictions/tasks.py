from django.apps import apps

from celery import shared_task

from bmcc.predictions.backends.tawhiri import TawhiriBackend


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True)
def run_prediction(self, prediction_id):
    Prediction = apps.get_model("predictions", "Prediction")
    try:
        prediction = Prediction.objects.get(pk=prediction_id)
    except Prediction.DoesNotExist:
        return

    backend = TawhiriBackend()
    backend.run(prediction)
