from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoomViewSet, MealViewSet, GuestViewSet, DebitCardViewSet,
    ReservationViewSet, TransactionViewSet, PaymentViewSet, DepositViewSet
)

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'meals', MealViewSet)
router.register(r'guests', GuestViewSet)
router.register(r'debitcards', DebitCardViewSet)
router.register(r'reservations', ReservationViewSet)
router.register(r'transactions', TransactionViewSet, basename='transaction')

# ✅ Payment & Deposit: handled manually, not via router
payment_list = PaymentViewSet.as_view({'get': 'list', 'post': 'create'})
deposit_list = DepositViewSet.as_view({'get': 'list', 'post': 'create'})

urlpatterns = [
    path('', include(router.urls)),
    path('payments/', payment_list, name='payments'),
    path('deposits/', deposit_list, name='deposits'),
]
