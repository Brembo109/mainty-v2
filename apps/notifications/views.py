from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Notification


class DropdownView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = (
            Notification.objects.filter(user=request.user, is_read=False)
            .order_by("-created_at")[:50]
        )
        return render(
            request,
            "notifications/dropdown.html",
            {"notifications": notifications},
        )


class MarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return HttpResponse("")


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return render(request, "notifications/dropdown.html", {"notifications": []})
