from django.db import models
from users.models import User
from medical_stores.models import MedicalStore

class Review(models.Model):


    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # [SENU]: store can have more than one review
    medical_store = models.ForeignKey(MedicalStore, on_delete=models.CASCADE, related_name='reviews')
    review_text = models.TextField()
    rating = models.PositiveSmallIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # [SENU]: user can create only one review and update it if needed
        constraints = [models.UniqueConstraint(fields=['user', 'medical_store'], name='unique_user_store_review')]

    def __str__(self):
        return f"{self.user.name} review on {self.medical_store.store_name}"
