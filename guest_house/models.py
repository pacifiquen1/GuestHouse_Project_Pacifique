from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=100)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    # Add other room-related fields

    def __str__(self):
        return self.name

class Meal(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    # Add other meal-related fields

    def __str__(self):
        return self.name

class Guest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    # Add other guest-related fields

    def __str__(self):
        return self.name

class DebitCard(models.Model):
    # guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name="card", null=True, blank=True)
    card_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cvc = models.CharField(max_length=3, null=True, blank=True)
    expiration_date = models.CharField(max_length=5) # MM/YY
    # Add other debit card-related fields

    # models.py
    def __str__(self):
        return f"Card ending in {self.card_number[-4:]}"

class Reservation(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ]
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    meal = models.ForeignKey(Meal, on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Add other reservation-related fields

    def __str__(self):
        return f"Reservation for {self.guest.name}"

class Transaction(models.Model):
    debit_card = models.ForeignKey(DebitCard, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=[('deposit', 'Deposit'), ('payment', 'Payment')]
    )
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} on {self.debit_card}"