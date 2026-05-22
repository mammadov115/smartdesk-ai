from django.db import models


class MonthlyUsage(models.Model):
    """
    Tracks per-company usage counters for the current month.
    A new row is created automatically on the first limit check of each month.
    The Celery reset_monthly_usage task pre-creates rows on the 1st of each month.
    """

    company = models.ForeignKey(
        "accounts.CompanyProfile",
        on_delete=models.CASCADE,
        related_name="monthly_usages",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    conversations_count = models.PositiveIntegerField(default=0)
    documents_count = models.PositiveIntegerField(default=0)
    # Set to True once the 80 % warning email has been sent this month.
    # Prevents duplicate warnings within the same billing period.
    limit_warning_sent = models.BooleanField(default=False)

    class Meta:
        unique_together = [("company", "year", "month")]
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.company.name} - {self.year}/{self.month:02d}"
