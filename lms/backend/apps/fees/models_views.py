"""
Fees module — fee structures, payment recording, and receipt generation.
Admin creates fee structures; students pay and view receipts.
"""

from django.db import models
from django.utils import timezone
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from apps.users.permissions import IsAdmin, IsStudent


# ─── Models ───────────────────────────────────────────────────────────────────

class FeeStructure(models.Model):
    """Defines how much fee a student in a particular branch and semester must pay."""
    branch = models.CharField(max_length=50)
    semester = models.IntegerField()
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'fee_structure'
        unique_together = ['branch', 'semester']

    def save(self, *args, **kwargs):
        # Auto-calculate total fee
        self.total_fee = self.tuition_fee + self.hostel_fee + self.library_fee + self.lab_fee
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.branch} Sem {self.semester} — ₹{self.total_fee}"


class FeePayment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    student = models.ForeignKey('users.Student', on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'fee_payments'

    def save(self, *args, **kwargs):
        # Auto-generate receipt number if not set
        if not self.receipt_number:
            self.receipt_number = f"RCP{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} — {self.student.roll_number} — ₹{self.amount_paid}"


# ─── Serializers ──────────────────────────────────────────────────────────────

class FeeStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeStructure
        fields = '__all__'


class FeePaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.name', read_only=True)
    roll_number = serializers.CharField(source='student.roll_number', read_only=True)
    fee_branch = serializers.CharField(source='fee_structure.branch', read_only=True)
    fee_semester = serializers.IntegerField(source='fee_structure.semester', read_only=True)

    class Meta:
        model = FeePayment
        fields = ['id', 'student', 'student_name', 'roll_number', 'fee_structure',
                  'fee_branch', 'fee_semester', 'amount_paid', 'payment_date',
                  'transaction_id', 'payment_status', 'receipt_number', 'created_at']


class InitiatePaymentSerializer(serializers.Serializer):
    fee_structure_id = serializers.IntegerField()
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.CharField(max_length=100, required=False, default='')


# ─── Views ────────────────────────────────────────────────────────────────────

class FeeStructureListView(APIView):
    """GET /api/fees/structures — all fee structures."""

    def get(self, request):
        branch = request.query_params.get('branch')
        semester = request.query_params.get('semester')
        structures = FeeStructure.objects.all()
        if branch:
            structures = structures.filter(branch=branch)
        if semester:
            structures = structures.filter(semester=semester)
        return Response(FeeStructureSerializer(structures, many=True).data)

    def post(self, request):
        """Admin creates/updates a fee structure."""
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin only.'}, status=403)
        serializer = FeeStructureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class StudentFeeView(APIView):
    """
    GET  /api/fees/my       — student sees their fee status
    POST /api/fees/my/pay   — student initiates a payment
    """
    permission_classes = [IsStudent]

    def get(self, request):
        student = request.user.student_profile
        # Find the fee structure for this student's branch and semester
        try:
            fee_structure = FeeStructure.objects.get(
                branch=student.branch, semester=student.semester
            )
        except FeeStructure.DoesNotExist:
            return Response({'message': 'No fee structure defined for your branch/semester.'})

        # Check if already paid
        payment = FeePayment.objects.filter(
            student=student, fee_structure=fee_structure, payment_status='COMPLETED'
        ).first()

        return Response({
            'fee_structure': FeeStructureSerializer(fee_structure).data,
            'payment': FeePaymentSerializer(payment).data if payment else None,
            'is_paid': payment is not None,
        })


class InitiatePaymentView(APIView):
    """POST /api/fees/pay — student records a fee payment."""
    permission_classes = [IsStudent]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        student = request.user.student_profile
        data = serializer.validated_data

        try:
            fee_structure = FeeStructure.objects.get(id=data['fee_structure_id'])
        except FeeStructure.DoesNotExist:
            return Response({'error': 'Fee structure not found.'}, status=404)

        # Prevent duplicate payments
        if FeePayment.objects.filter(student=student, fee_structure=fee_structure, payment_status='COMPLETED').exists():
            return Response({'error': 'Fee for this semester already paid.'}, status=400)

        payment = FeePayment.objects.create(
            student=student,
            fee_structure=fee_structure,
            amount_paid=data['amount_paid'],
            transaction_id=data.get('transaction_id', ''),
            payment_status='COMPLETED',  # In real life, this would be PENDING until payment gateway confirms
        )

        return Response({
            'message': 'Payment recorded successfully.',
            'receipt_number': payment.receipt_number,
            'payment': FeePaymentSerializer(payment).data,
        }, status=201)


class FeeReceiptView(APIView):
    """GET /api/fees/receipt/<receipt_number> — view payment receipt."""
    permission_classes = [IsStudent]

    def get(self, request, receipt_number):
        try:
            payment = FeePayment.objects.select_related(
                'student__user', 'fee_structure'
            ).get(receipt_number=receipt_number, student=request.user.student_profile)
        except FeePayment.DoesNotExist:
            return Response({'error': 'Receipt not found.'}, status=404)

        return Response(FeePaymentSerializer(payment).data)


class AdminFeeReportView(APIView):
    """GET /api/fees/admin/report — admin views all payments."""
    permission_classes = [IsAdmin]

    def get(self, request):
        payments = FeePayment.objects.select_related(
            'student__user', 'fee_structure'
        ).filter(payment_status='COMPLETED')

        total_collected = sum(p.amount_paid for p in payments)
        return Response({
            'total_collected': float(total_collected),
            'payment_count': payments.count(),
            'payments': FeePaymentSerializer(payments, many=True).data,
        })
