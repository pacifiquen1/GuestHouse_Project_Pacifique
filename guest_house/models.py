from django.db import models
from django.core.validators import RegexValidator

class Room(models.Model):
    name = models.CharField(max_length=100)
    price_per_night = models.DecimalField(max_digits=9, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Meal(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=9, decimal_places=2)

    def __str__(self):
        return self.name

# In models.py
class Guest(models.Model):
    first_name = models.CharField(max_length=50)  # Remove null=True
    last_name = models.CharField(max_length=50)   # Remove null=True
    # ... rest of your fields ...
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[0-9]{10}$',
                message='Phone number must be exactly 10 digits (numbers only)'
            )
        ]
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

class DebitCard(models.Model):
    # Link to the Guest model (One-to-One relationship)
    # This means each guest can have one debit card, and each debit card belongs to one guest.
    guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name="card", null=True, blank=True)
    
    cardholder_name = models.CharField(max_length=255, blank=True, null=True) # New field
    card_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cvc = models.CharField(max_length=4, null=True, blank=True) # Already updated to 4
    expiration_date = models.CharField(max_length=5) # MM/YY

    # You might want to add a field to track if the card is active
    is_active = models.BooleanField(default=True) # New field

    def __str__(self):
        return f"Card ending in {self.card_number[-4:]} ({self.cardholder_name or 'N/A'})"

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

    def __str__(self):
        return f"Reservation for {self.guest.full_name}"

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
	