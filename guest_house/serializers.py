from rest_framework import serializers
from .models import Room, Meal, Guest, Reservation, DebitCard, Transaction

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = '__all__'

class GuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guest
        fields = '__all__'

class DebitCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitCard
        fields = '__all__'

    def to_representation(self, instance):
        serialized_data = super(DebitCardSerializer, self).to_representation(instance)
        # serialized_data["has_guest"] = True if instance.guest else False
        return serialized_data

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('timestamp',)

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

# serializers.py
class ReservationCreateSerializer(serializers.Serializer):
    guest_email = serializers.EmailField()
    guest_name = serializers.CharField()
    room_id = serializers.IntegerField(required=False)
    meal_id = serializers.IntegerField(required=False)
    check_in_date = serializers.DateField()
    check_out_date = serializers.DateField()

    def validate(self, attrs):
        if not attrs.get('room_id') and not attrs.get('meal_id'):
            raise serializers.ValidationError("At least a room or a meal must be selected.")
        
        if attrs['check_out_date'] <= attrs['check_in_date']:
            raise serializers.ValidationError("Check-out date must be after check-in date.")

        return attrs

class PaymentSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    cvc = serializers.CharField(max_length=4)  # 3 for Visa/MC, 4 for Amex
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    reservation_id = serializers.IntegerField()

class DepositSerializer(serializers.Serializer):
    card_number = serializers.CharField(max_length=20)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)