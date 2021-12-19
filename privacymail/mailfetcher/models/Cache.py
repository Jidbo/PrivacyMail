import logging
import pickle
import base64
from model_utils.models import TimeStampedModel
from django.db import models

logger = logging.getLogger(__name__)


class Cache(TimeStampedModel):
    key = models.CharField(max_length=200, db_index=True)
    value = models.TextField()
    
    def __str__(self):
        return f"({self.type}): {self.word}"

    @classmethod
    def set(cls, key, value):
        pickled = pickle.dumps(value)
        b64encoded = base64.b64encode(pickled).decode('latin1')
        try:
            obj = cls.objects.get(key=key)
            obj.value = b64encoded
        except cls.DoesNotExist:
            obj = cls(key=key, value=b64encoded)

        obj.save()

    @classmethod
    def get(cls, key):
        try:
            obj = cls.objects.get(key=key)
        except cls.DoesNotExist:
            return None

        pickled = base64.b64decode(obj.value)
        return pickle.loads(pickled)

    @classmethod
    def delete(cls, key):
        try:
            obj = cls.objects.filter(key=key).delete()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def clear(cls):
        cls.objects.all().delete()
