from django.contrib import admin
from .models import Subscriber, QuizResult, ThreatReport, PageVisit


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display  = ('email', 'is_active', 'created_at')
    list_filter   = ('is_active',)
    search_fields = ('email',)
    readonly_fields = ('ip_hash', 'created_at')
    ordering = ('-created_at',)


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display  = ('score', 'total', 'pct', 'created_at')
    list_filter   = ()
    readonly_fields = ('ip_hash', 'pct', 'answers', 'created_at')
    ordering = ('-created_at',)


@admin.register(ThreatReport)
class ThreatReportAdmin(admin.ModelAdmin):
    list_display  = ('threat_type', 'description_short', 'created_at')
    list_filter   = ('threat_type',)
    search_fields = ('description', 'suspect_url')
    readonly_fields = ('ip_hash', 'created_at')
    ordering = ('-created_at',)

    def description_short(self, obj):
        return obj.description[:60] + ('…' if len(obj.description) > 60 else '')
    description_short.short_description = 'Description'


@admin.register(PageVisit)
class PageVisitAdmin(admin.ModelAdmin):
    list_display  = ('section', 'created_at')
    list_filter   = ('section',)
    readonly_fields = ('ip_hash', 'user_agent', 'created_at')
    ordering = ('-created_at',)
