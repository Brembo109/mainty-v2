from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.constants import Role
from apps.accounts.mixins import WriteAccessMixin

from .forms import TaskCreateForm, TaskUpdateForm
from .models import Task


def _task_qs():
    return Task.objects.select_related("asset", "assigned_to")


class TaskListView(LoginRequiredMixin, ListView):
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25

    def get_queryset(self):
        return _apply_filters(_task_qs(), self.request.GET)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["status_filter"] = self.request.GET.get("status", "")
        ctx["priority_filter"] = self.request.GET.get("priority", "")
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "tasks/partials/_task_table.html", context
            )
        return super().render_to_response(context, **kwargs)


class TaskDetailView(LoginRequiredMixin, DetailView):
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_queryset(self):
        return _task_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        return ctx


class TaskCreateView(LoginRequiredMixin, WriteAccessMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "tasks/task_form.html"

    def get_success_url(self):
        return reverse("tasks:detail", kwargs={"pk": self.object.pk})

    def get_initial(self):
        initial = super().get_initial()
        asset_pk = self.request.GET.get("asset")
        if asset_pk:
            initial["assets"] = [asset_pk]
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Neue Aufgabe")
        ctx["submit_label"] = _("Aufgabe erstellen")
        return ctx

    def form_valid(self, form):
        assets = list(form.cleaned_data.get("assets", []))
        template = form.save(commit=False)

        if not assets:
            template.save()
            self.object = template
            messages.success(self.request, _("Aufgabe wurde erfolgreich erstellt."))
            return redirect(self.get_success_url())

        if len(assets) == 1:
            template.asset = assets[0]
            template.save()
            self.object = template
            messages.success(self.request, _("Aufgabe wurde erfolgreich erstellt."))
            return redirect(self.get_success_url())

        for asset in assets:
            Task.objects.create(
                title=template.title,
                description=template.description,
                assigned_to=template.assigned_to,
                due_date=template.due_date,
                priority=template.priority,
                status=template.status,
                asset=asset,
            )
        messages.success(self.request, _("%(count)d Aufgaben wurden erstellt.") % {"count": len(assets)})
        return redirect(reverse("tasks:list"))


class TaskUpdateView(LoginRequiredMixin, WriteAccessMixin, UpdateView):
    form_class = TaskUpdateForm
    template_name = "tasks/task_form.html"

    def get_queryset(self):
        return _task_qs()

    def get_success_url(self):
        return reverse("tasks:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form_title"] = _("Aufgabe bearbeiten")
        ctx["submit_label"] = _("Änderungen speichern")
        ctx["is_update"] = True
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _("Aufgabe wurde aktualisiert."))
        return super().form_valid(form)


class TaskDeleteView(LoginRequiredMixin, WriteAccessMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    context_object_name = "task"
    success_url = reverse_lazy("tasks:list")

    def form_valid(self, form):
        messages.success(self.request, _("Aufgabe wurde gelöscht."))
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Shared filter logic
# ---------------------------------------------------------------------------

def _apply_filters(qs, get_params):
    q = get_params.get("q", "").strip()
    status = get_params.get("status", "").strip()
    priority = get_params.get("priority", "").strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(description__icontains=q)
            | Q(assigned_to__username__icontains=q)
            | Q(asset__name__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if priority:
        qs = qs.filter(priority=priority)
    return qs
