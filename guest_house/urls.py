from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
router = DefaultRouter()
router.register(r'rooms', views.RoomViewSet)
router.register(r'meals', views.MealViewSet)
router.register(r'guests', views.GuestViewSet)
router.register(r'debitcards', views.DebitCardViewSet)
router.register(r'reservations', views.ReservationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    path('payments/', views.process_payment, name='process-payment'),
    path('deposit_funds/', views.deposit_funds, name='deposit-funds'),
]