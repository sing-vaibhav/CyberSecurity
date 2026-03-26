import hashlib
import json
import logging

from django.core.cache import cache
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import PageVisit, QuizResult, Subscriber, ThreatReport

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_ip_hash(request):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    ip = ip.split(',')[0].strip()
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def rate_limit(key, max_calls=5, window=60):
    """Simple in-memory rate limiter. Returns True if limit exceeded."""
    count = cache.get(key, 0)
    if count >= max_calls:
        return True
    cache.set(key, count + 1, timeout=window)
    return False


def json_error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def json_ok(data=None, **kwargs):
    payload = {'success': True}
    if data:
        payload.update(data)
    payload.update(kwargs)
    return JsonResponse(payload)


# ── Page views ────────────────────────────────────────────────────────────────

def index(request):
    """Serve the main frontend page."""
    return render(request, 'awareness/index.html')


def admin_dashboard(request):
    """Simple stats dashboard (no auth for demo — add login_required in prod)."""
    return render(request, 'awareness/admin.html')


def resources(request):
    """Cybersecurity learning resources page."""
    PageVisit.objects.create(
        section='resources',
        ip_hash=get_ip_hash(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:256],
    )
    return render(request, 'awareness/resources.html')


# ── API: Subscribe ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def subscribe(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return json_error('Invalid JSON')

    email = body.get('email', '').strip().lower()
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        return json_error('Please enter a valid email address.')

    ip_hash = get_ip_hash(request)
    rl_key  = f'subscribe:{ip_hash}'
    if rate_limit(rl_key, max_calls=3, window=300):
        return json_error('Too many requests. Please try again later.', status=429)

    obj, created = Subscriber.objects.get_or_create(
        email=email,
        defaults={'ip_hash': ip_hash}
    )
    if not created:
        return json_error('This email is already subscribed.', status=409)

    logger.info('New subscriber: %s (hash %s)', email, ip_hash)
    total = Subscriber.objects.filter(is_active=True).count()
    return json_ok(message="You're on the list — stay safe! 🛡️", total_subscribers=total)


# ── API: Quiz result ───────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def submit_quiz(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return json_error('Invalid JSON')

    score   = int(body.get('score', 0))
    total   = int(body.get('total', 5))
    answers = body.get('answers', [])

    if not (0 <= score <= total <= 20):
        return json_error('Invalid score values.')

    ip_hash = get_ip_hash(request)
    rl_key  = f'quiz:{ip_hash}'
    if rate_limit(rl_key, max_calls=10, window=60):
        return json_error('Too many submissions.', status=429)

    QuizResult.objects.create(
        score=score,
        total=total,
        answers=answers,
        ip_hash=ip_hash,
    )

    # Return live global stats
    stats = QuizResult.objects.aggregate(avg=Avg('pct'), count=Count('id'))
    return json_ok(
        message='Result saved!',
        global_avg=round(stats['avg'] or 0, 1),
        total_attempts=stats['count'],
    )


# ── API: Threat report ─────────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def report_threat(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return json_error('Invalid JSON')

    threat_type = body.get('type', 'other')
    valid_types = [t[0] for t in ThreatReport.THREAT_TYPES]
    if threat_type not in valid_types:
        threat_type = 'other'

    description = body.get('description', '')[:1000]
    suspect_url = body.get('url', '')[:512]

    ip_hash = get_ip_hash(request)
    rl_key  = f'report:{ip_hash}'
    if rate_limit(rl_key, max_calls=5, window=300):
        return json_error('Too many reports. Please try again later.', status=429)

    report = ThreatReport.objects.create(
        threat_type=threat_type,
        description=description,
        suspect_url=suspect_url,
        ip_hash=ip_hash,
    )
    logger.info('Threat report #%d: %s', report.id, threat_type)

    total = ThreatReport.objects.count()
    return json_ok(message='Report received. Thank you for helping!', total_reports=total)


# ── API: Track page section visit ─────────────────────────────────────────────

@csrf_exempt
@require_POST
def track_visit(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return json_error('Invalid JSON')

    section = body.get('section', 'unknown')[:64]
    ip_hash = get_ip_hash(request)
    ua      = request.META.get('HTTP_USER_AGENT', '')[:256]

    PageVisit.objects.create(section=section, ip_hash=ip_hash, user_agent=ua)
    return json_ok()


# ── API: Stats (for dashboard) ─────────────────────────────────────────────────

@require_GET
def get_stats(request):
    sub_count   = Subscriber.objects.filter(is_active=True).count()
    quiz_stats  = QuizResult.objects.aggregate(avg=Avg('pct'), count=Count('id'))
    report_count = ThreatReport.objects.count()
    visit_count = PageVisit.objects.count()

    # Quiz score distribution
    buckets = {'0-39': 0, '40-59': 0, '60-79': 0, '80-100': 0}
    for r in QuizResult.objects.values_list('pct', flat=True):
        if r < 40:   buckets['0-39']   += 1
        elif r < 60: buckets['40-59']  += 1
        elif r < 80: buckets['60-79']  += 1
        else:        buckets['80-100'] += 1

    # Top threat types reported
    top_threats = list(
        ThreatReport.objects
        .values('threat_type')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # Section engagement
    top_sections = list(
        PageVisit.objects
        .values('section')
        .annotate(count=Count('id'))
        .order_by('-count')[:6]
    )

    # Recent quiz results (last 10)
    recent_quiz = list(
        QuizResult.objects
        .values('score', 'total', 'pct', 'created_at')
        .order_by('-created_at')[:10]
    )
    for r in recent_quiz:
        r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M')

    # Recent reports (last 10)
    recent_reports = list(
        ThreatReport.objects
        .values('threat_type', 'description', 'created_at')
        .order_by('-created_at')[:10]
    )
    for r in recent_reports:
        r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M')

    return json_ok(
        subscribers=sub_count,
        quiz_avg=round(quiz_stats['avg'] or 0, 1),
        quiz_attempts=quiz_stats['count'] or 0,
        reports=report_count,
        visits=visit_count,
        score_distribution=buckets,
        top_threats=top_threats,
        top_sections=top_sections,
        recent_quiz=recent_quiz,
        recent_reports=recent_reports,
    )
