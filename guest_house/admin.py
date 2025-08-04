from django.contrib import admin
from .models import Room, Meal, Guest, DebitCard

admin.site.register(Room)
admin.site.register(Meal)
admin.site.register(Guest)
admin.site.register(DebitCard)
# You might choose not to register Reservation and Transaction initially
# or register them later as needed for testing.
# admin.site.register(Reservation)
# admin.site.register(Transaction)