from django.db import models
from django.contrib.auth.models import User

class FitnessPlan(models.Model):
    title = models.CharField(max_length=255)
    text = models.TextField()
    premium = models.BooleanField(default=True) # meaning does this require a premium account to be able to access it

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) #The OneToOneField is a type of field that establishes a one-to-one relationship between two models(table) Customer w User tsama user hna rah foreign key(remarque ki nebgho nekhedmo many to many ndiro ForeignKey)
    stripeid = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255)
    cancel_at_period_end= models.BooleanField(default=False)
    membership = models.BooleanField(default=False)

