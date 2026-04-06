from django.urls import path
from .models_views import FeeStructureListView, StudentFeeView, InitiatePaymentView, FeeReceiptView, AdminFeeReportView

urlpatterns = [
    path('structures/', FeeStructureListView.as_view(), name='fee-structures'),
    path('my/', StudentFeeView.as_view(), name='my-fees'),
    path('pay/', InitiatePaymentView.as_view(), name='pay-fee'),
    path('receipt/<str:receipt_number>/', FeeReceiptView.as_view(), name='fee-receipt'),
    path('admin/report/', AdminFeeReportView.as_view(), name='fee-report'),
]