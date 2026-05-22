from django.utils import timezone

from .models import CompanyProfile, User


def _get_total_chats():
    try:
        from apps.chat.models import ChatSession

        return ChatSession.objects.count()
    except Exception:
        return 0


def _get_total_revenue():
    """Return total revenue in currency units (e.g. USD) from paid Stripe invoices."""
    try:
        from djstripe.models import Invoice as StripeInvoice

        total_cents = sum((inv.stripe_data or {}).get("amount_paid", 0) for inv in StripeInvoice.objects.all())
        return round(total_cents / 100, 2)
    except Exception:
        return 0


def dashboard_callback(request, context):
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timezone.timedelta(days=7)

    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    new_this_month = User.objects.filter(date_joined__gte=month_start).count()
    new_this_week = User.objects.filter(date_joined__gte=week_ago).count()

    total_companies = CompanyProfile.objects.count()
    paid_companies = CompanyProfile.objects.filter(subscription_plan=CompanyProfile.SubscriptionPlan.PAID).count()
    free_companies = total_companies - paid_companies

    total_chats = _get_total_chats()
    total_revenue = _get_total_revenue()

    active_pct = round(active_users / total_users * 100) if total_users else 0
    verified_pct = round(verified_users / total_users * 100) if total_users else 0
    paid_pct = round(paid_companies / total_companies * 100) if total_companies else 0

    context.update(
        {
            "kpis": [
                {
                    "title": "Total Users",
                    "metric": total_users,
                    "icon": "group",
                    "description": f"+{new_this_week} this week",
                },
                {
                    "title": "Active Users",
                    "metric": active_users,
                    "icon": "check_circle",
                    "description": f"{active_pct}% of total",
                },
                {
                    "title": "Email Verified",
                    "metric": verified_users,
                    "icon": "mark_email_read",
                    "description": f"{verified_pct}% of total",
                },
                {
                    "title": "New This Month",
                    "metric": new_this_month,
                    "icon": "person_add",
                    "description": f"+{new_this_week} last 7 days",
                },
                {
                    "title": "Companies",
                    "metric": total_companies,
                    "icon": "business",
                    "description": f"{paid_companies} paid · {free_companies} free",
                },
                {
                    "title": "Paid Plans",
                    "metric": paid_companies,
                    "icon": "workspace_premium",
                    "description": f"{paid_pct}% conversion",
                },
                {
                    "title": "Total Chats",
                    "metric": total_chats,
                    "icon": "chat",
                    "description": "All time chat sessions",
                },
                {
                    "title": "Total Revenue",
                    "metric": f"${total_revenue}",
                    "icon": "payments",
                    "description": "From paid Stripe invoices",
                },
            ],
            "recent_users": User.objects.order_by("-date_joined")[:8],
            "plan_breakdown": {
                "free": free_companies,
                "paid": paid_companies,
                "total": total_companies,
            },
        }
    )
    return context
