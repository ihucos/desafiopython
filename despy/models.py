import uuid

from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):

    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def dictify(self):
        return dict(
            name=self.get_full_name(),
            email=self.username,
            id=self.pk,
            created=self.date_joined,

            # by the API specification there is not way to modify the user
            modified=self.date_joined,

            token=self.token,
            last_login=self.last_login or self.date_joined,
            phones=[phone.dictify() for phone in self.phones.all()])

    def get_absolute_url(self):
        return reverse('view-user', kwargs={'pk': self.pk})


class Phone(models.Model):

    user = models.ForeignKey(User, related_name='phones')
    number = PhoneNumberField()
    ddd = models.CharField(max_length=2)

    def dictify(self):
        return dict(
            number=self.number.as_international,
            ddd=self.ddd)

    class Meta:
        unique_together = (("user", "ddd", "number"),)
