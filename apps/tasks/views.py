from datetime import date

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
from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin

from .filter_defs import TASK_FILTER_DIMENSIONS
from .forms import TaskCreateForm, TaskFilterForm, TaskUpdateForm
from .models import Task


def _task_qs():
    return Task.objects.select_related("asset", "assigned_to")


class TaskListView(EmptyStateMixin, LoginRequiredMixin, ListView):
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 25
    empty_icon = "task"
    empty_title = _("Keine offenen Aufgaben")
    empty_desc = _("Aufgaben entstehen automatisch aus Wartungsplänen oder werden manuell angelegt.")

    def get_queryset(self):
        return _apply_filters(_task_qs(), self._filter_form())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        ctx["can_write"] = self.request.user.has_role(Role.ADMIN, Role.USER)
        if ctx["can_write"]:
            ctx["empty_primary"] = {
                "label": _("Neue Aufgabe"), "url": reverse_lazy("tasks:create"), "icon": "+",
            }
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx.update(build_toolbar_context(
            self.request, form, TASK_FILTER_DIMENSIONS,
            search_placeholder=_("Titel, Anlage, Benutzer…"),
            hx_target="#task-list-body",
            inline_fields=[
                "status", "priority", "assigned_to", "asset", "overdue",
            ],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(
                self.request, "tasks/partials/_task_list_body.html", context
            )
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = TaskFilterForm(self.request.GET or None)
        return self._cached_filter_form


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

def _apply_filters(qs, form):
    if not form.is_valid():
        return qs
    cd = form.cleaned_data
    if cd.get("q"):
        qs = qs.filter(
            Q(title__icontains=cd["q"])
            | Q(description__icontains=cd["q"])
            | Q(assigned_to__username__icontains=cd["q"])
            | Q(asset__name__icontains=cd["q"])
        )
    if cd.get("status"):
        qs = qs.filter(status=cd["status"])
    if cd.get("priority"):
        qs = qs.filter(priority=cd["priority"])
    if cd.get("assigned_to"):
        qs = qs.filter(assigned_to=cd["assigned_to"])
    if cd.get("asset"):
        qs = qs.filter(asset=cd["asset"])
    if cd.get("overdue") == "yes":
        qs = qs.filter(due_date__lt=date.today()).exclude(status="done")
    elif cd.get("overdue") == "no":
        qs = qs.filter(Q(due_date__gte=date.today()) | Q(due_date__isnull=True) | Q(status="done"))
    return qs
