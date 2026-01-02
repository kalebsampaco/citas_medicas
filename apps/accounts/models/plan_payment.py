from django.db import models

from .company import Company
from .plan import Plan


class PlanPayment(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='plan_payments')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    # Fecha del mes pagado (normalizada al primer día del mes)
    paid_month = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "paid_month"]),
        ]
        unique_together = ("company", "paid_month", "reference")
        ordering = ["-paid_month", "-created_at"]

    def __str__(self) -> str:
        month = self.paid_month.strftime("%Y-%m") if self.paid_month else "?"
        return f"Payment {self.amount} {month} - {self.company_id}"
