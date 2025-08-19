from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils import timezone
from datetime import timedelta


class Room(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[A-Za-z0-9\s]+$', "Room name must contain only letters, numbers, and spaces.")]
    )
    price_per_night = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Meal(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[RegexValidator(r'^[A-Za-z0-9\s]+$', "Meal name must contain only letters, numbers, and spaces.")]
    )
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    def __str__(self):
        return self.name


class Guest(models.Model):
    first_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[A-Za-z]+$', "First name must only contain letters.")]
    )
    last_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(r'^[A-Za-z]+$', "Last name must only contain letters.")]
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=13,  # ✅ supports +2507XXXXXXXX
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+2507\d{8}$',
                message="Phone number must be in format +2507XXXXXXXX"
            )
        ]
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name


class DebitCard(models.Model):
    guest = models.OneToOneField(Guest, on_delete=models.CASCADE, related_name="card", null=True, blank=True)
    cardholder_name = models.CharField(
        max_length=255,
        validators=[RegexValidator(r'^[A-Za-z\s]+$', "Cardholder name must only contain letters and spaces.")],
        blank=True,
        null=True
    )
    card_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^\d{16}$', "Card number must be 16 digits.")]
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    cvc = models.CharField(
        max_length=4,
        validators=[RegexValidator(r'^\d{3,4}$', "CVC must be 3 or 4 digits.")],
        null=True,
        blank=True
    )
    expiration_date = models.CharField(max_length=5)  # MM/YY
    is_active = models.BooleanField(default=True)

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

    # automation
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Auto-calculate total cost: (nights × room price) + meal price"""
        if self.check_in_date and self.check_out_date:
            nights = (self.check_out_date - self.check_in_date).days
            room_cost = self.room.price_per_night * nights if self.room else 0
            meal_cost = self.meal.price if self.meal else 0
            self.total_cost = room_cost + meal_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation for {self.guest.full_name}"

    def should_send_reminder(self):
        return (
            self.status == "pending"
            and not self.reminder_sent
            and timezone.now() >= self.created_at + timedelta(minutes=2)
        )

    def should_cancel(self):
        return (
            self.status == "pending"
            and timezone.now() >= self.created_at + timedelta(minutes=5)
        )


class Transaction(models.Model):
    debit_card = models.ForeignKey(DebitCard, on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=[('deposit', 'Deposit'), ('payment', 'Payment')]
    )
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type}: {self.amount} on {self.debit_card}"
