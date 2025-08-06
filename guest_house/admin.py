from django.contrib import admin
from .models import Room, Meal, Guest, DebitCard, Reservation, Transaction

# Register basic models with default admin interface
admin.site.register(Room)
admin.site.register(Meal)

# Register Guest with a custom admin for better display/search
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email', 'phone')
    list_filter = ('first_name', 'last_name')

# Register DebitCard with a custom admin to display new fields and add search/filter
@admin.register(DebitCard)
class DebitCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'cardholder_name', 'guest', 'balance', 'expiration_date', 'cvc', 'is_active')
    search_fields = ('card_number', 'cardholder_name', 'guest__first_name', 'guest__last_name')
    list_filter = ('is_active', 'expiration_date')
    # Optional: Uncomment the lines below if you want to control form fields or make CVC read-only
    # fields = ('guest', 'cardholder_name', 'card_number', 'balance', 'expiration_date', 'is_active')
    # readonly_fields = ('cvc',)

# Register Reservation with a custom admin
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('guest', 'room', 'meal', 'check_in_date', 'check_out_date', 'total_cost', 'status')
    list_filter = ('status', 'check_in_date', 'check_out_date')
    search_fields = ('guest__first_name', 'guest__last_name', 'room__name')
    raw_id_fields = ('guest', 'room', 'meal')

# Register Transaction with a custom admin
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('debit_card', 'amount', 'transaction_type', 'reservation', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('debit_card__card_number', 'reservation__guest__first_name')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('debit_card', 'reservation')
