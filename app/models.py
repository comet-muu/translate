from django.db import models
from django.contrib.auth.models import User
import os

class Photo(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    image = models.ImageField(
        upload_to='photos/'
    )

    manga_image = models.ImageField(
        upload_to='manga/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def delete(self, *args, **kwargs):

        if self.image:

            if os.path.isfile(self.image.path):

                os.remove(self.image.path)

        super().delete(*args, **kwargs)
