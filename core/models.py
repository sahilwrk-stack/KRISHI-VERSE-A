from django.db import models


class AnalysisHistory(models.Model):
    """Optional: stores past analyses for audit/history purposes."""
    state = models.CharField(max_length=100)
    crop = models.CharField(max_length=100)
    land_size_acres = models.FloatField()
    soil_type = models.CharField(max_length=50)
    irrigation = models.CharField(max_length=10)
    investment_capacity = models.FloatField()
    suitability_score = models.FloatField(null=True)
    net_profit = models.FloatField(null=True)
    roi = models.FloatField(null=True)
    farmer_emotion = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Analysis Histories"

    def __str__(self):
        return f"{self.crop} in {self.state} ({self.created_at:%Y-%m-%d})"
