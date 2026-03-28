from django.contrib import admin
from .models import Guest, Sender

admin.site.register(Sender)
admin.site.register(Guest)
