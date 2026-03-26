from django.db import models
from django.utils import timezone


class Subscriber(models.Model):
    """Newsletter / awareness alert subscriber."""
    email      = models.EmailField(unique=True)
    ip_hash    = models.CharField(max_length=64, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class QuizResult(models.Model):
    """Stores every quiz submission with per-question answer log."""
    score      = models.PositiveSmallIntegerField()
    total      = models.PositiveSmallIntegerField(default=5)
    pct        = models.FloatField()               # score/total * 100
    answers    = models.JSONField(default=list)    # [{q_idx, chosen, correct}]
    ip_hash    = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.score}/{self.total} — {self.created_at:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        self.pct = round(self.score / self.total * 100, 1) if self.total else 0
        super().save(*args, **kwargs)


class ThreatReport(models.Model):
    """User-submitted reports of threats / suspicious activity encountered."""

    THREAT_TYPES = [
        ('phishing',       'Phishing'),
        ('scam',           'Online Scam'),
        ('malware',        'Malware / Suspicious Download'),
        ('impersonation',  'Impersonation / Fake Support'),
        ('public_wifi',    'Suspicious Wi-Fi / Network'),
        ('ransomware',     'Ransomware'),
        ('other',          'Other'),
    ]

    threat_type = models.CharField(max_length=32, choices=THREAT_TYPES)
    description = models.TextField(max_length=1000, blank=True)
    suspect_url = models.URLField(max_length=512, blank=True)
    ip_hash     = models.CharField(max_length=64, blank=True)
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_threat_type_display()} — {self.created_at:%Y-%m-%d}"


class PageVisit(models.Model):
    """Tracks which sections visitors engage with."""
    section    = models.CharField(max_length=64)
    ip_hash    = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.section} — {self.created_at:%Y-%m-%d %H:%M}"
