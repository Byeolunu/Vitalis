from django.db import models
from datetime import date
GenderChoices = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]
class User(models.Model) :
    FirstName = models.CharField(max_length=50)
    LastName = models.CharField(max_length=50)
    Gender = models.CharField(max_length=50, choices=GenderChoices)
    BirthDate = models.DateField()
    weight = models.FloatField(help_text="Weight in Kg")
    height = models.FloatField(help_text="Height in Cm")

    def __str__(self):
        return f"{self.FirstName} {self.LastName}"

    def get_age(self):
        today = date.today()
        age = today.year - self.BirthDate.year
        # Check if the user has already had their birthday this year
        if today.month < self.BirthDate.month or (today.month == self.BirthDate.month and today.day < self.BirthDate.day):
            age -= 1
        return age