from django.contrib import admin
from django.utils.html import format_html
from .models import Room, Meal, Guest, DebitCard, Reservation, Transaction


# ---------------------------
# ROOM
# ---------------------------
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price_per_night', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)


# ---------------------------
# MEAL
# ---------------------------
@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price')
    search_fields = ('name',)


# ---------------------------
# GUEST
# ---------------------------
@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email', 'phone')

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = "Guest Name"


# ---------------------------
# DEBIT CARD
# ---------------------------
@admin.register(DebitCard)
class DebitCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'cardholder_name', 'guest', 'balance', 'expiration_date', 'is_active')
    search_fields = ('card_number', 'cardholder_name', 'guest__first_name', 'guest__last_name')
    list_filter = ('is_active', 'expiration_date')
    # readonly_fields = ('cvc',)   # Optional: keep CVC hidden


# ---------------------------
# TRANSACTION INLINE for Reservation
# ---------------------------
class TransactionInline(admin.TabularInline):  
    """Show related transactions inside Reservation admin"""
    model = Transaction
    extra = 0
    fields = ('debit_card', 'amount', 'transaction_type_badge', 'timestamp')
    readonly_fields = ('debit_card', 'amount', 'transaction_type_badge', 'timestamp')

    def transaction_type_badge(self, obj):
        color_map = {
            "deposit": "#2ecc71",   # green
            "payment": "#2980b9"    # blue
        }
        color = color_map.get(obj.transaction_type, "#7f8c8d")
        return format_html(
            '<span style="padding:3px 8px; border-radius:12px; color:white; background:{};">{}</span>',
            color,
            obj.transaction_type.capitalize()
        )
    transaction_type_badge.short_description = "Transaction Type"


# ---------------------------
# RESERVATION (with status badge + inline transactions)
# ---------------------------
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'guest', 'room', 'meal', 'check_in_date', 'check_out_date', 'total_cost', 'status_badge')
    list_filter = ('status', 'check_in_date', 'check_out_date')
    search_fields = ('guest__first_name', 'guest__last_name', 'room__name')
    raw_id_fields = ('guest', 'room', 'meal')
    readonly_fields = ('total_cost', 'status')
    inlines = [TransactionInline]   # ✅ show transactions inline

    def status_badge(self, obj):
        """Show reservation status with a pill-shaped colored badge"""
        color_map = {
            "pending": "#f39c12",   # orange
            "paid": "#27ae60",      # green
            "cancelled": "#c0392b"  # red
        }
        color = color_map.get(obj.status, "#7f8c8d")
        return format_html(
            '<span style="padding:3px 8px; border-radius:12px; color:white; background:{};">{}</span>',
            color,
            obj.status.capitalize()
        )

    status_badge.admin_order_field = "status"
    status_badge.short_description = "Status"


# ---------------------------
# TRANSACTION (standalone view with badge)
# ---------------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'debit_card', 'amount', 'transaction_type_badge', 'reservation', 'timestamp')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('debit_card__card_number', 'reservation__guest__first_name', 'reservation__guest__last_name')
    readonly_fields = ('timestamp',)
    raw_id_fields = ('debit_card', 'reservation')

    def transaction_type_badge(self, obj):
        """Show transaction type with badge colors"""
        color_map = {
            "deposit": "#2ecc71",   # green
            "payment": "#2980b9"    # blue
        }
        color = color_map.get(obj.transaction_type, "#7f8c8d")
        return format_html(
            '<span style="padding:3px 8px; border-radius:12px; color:white; background:{};">{}</span>',
            color,
            obj.transaction_type.capitalize()
        )

    transaction_type_badge.admin_order_field = "transaction_type"
    transaction_type_badge.short_description = "Transaction Type"
