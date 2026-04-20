import csv
import io

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.template.response import TemplateResponse
from django.views.generic import ListView, View

from apps.accounts.constants import Role
from apps.accounts.mixins import RoleRequiredMixin
from apps.core.filters import build_toolbar_context
from apps.core.view_mixins import EmptyStateMixin
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .filter_defs import AUDIT_FILTER_DIMENSIONS
from .forms import AuditFilterForm
from .models import AuditLog


class AuditLogListView(EmptyStateMixin, LoginRequiredMixin, RoleRequiredMixin, ListView):
    model = AuditLog
    template_name = "audit/audit_log_list.html"
    context_object_name = "entries"
    paginate_by = 50
    required_role = Role.ADMIN
    empty_icon = "audit"
    empty_title = _("Keine Audit-Ereignisse")
    empty_desc = _("Audit-Ereignisse werden bei jeder GMP-relevanten Änderung automatisch erfasst.")

    def get_queryset(self):
        return _apply_filters(
            AuditLog.objects.select_related("actor", "content_type"),
            self._filter_form(),
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        form = self._filter_form()
        ctx["filter_form"] = form
        # Pre-encoded filter params without 'page' — used to build pagination links.
        get_params = self.request.GET.copy()
        get_params.pop("page", None)
        ctx["filter_params"] = get_params.urlencode()
        ctx.update(build_toolbar_context(
            self.request, form, AUDIT_FILTER_DIMENSIONS,
            search_placeholder=_("Benutzer, Objekt…"),
            hx_target="#audit-list-body",
            inline_fields=["action", "model"],
        ))
        return ctx

    def render_to_response(self, context, **kwargs):
        # Return the wrapped list body so the toolbar re-renders with chips.
        if self.request.headers.get("HX-Request") and not self.request.headers.get("HX-Boosted"):
            return TemplateResponse(self.request, "audit/partials/_audit_list_body.html", context)
        return super().render_to_response(context, **kwargs)

    def _filter_form(self):
        if not hasattr(self, "_cached_filter_form"):
            self._cached_filter_form = AuditFilterForm(self.request.GET or None)
        return self._cached_filter_form


class AuditLogExportView(LoginRequiredMixin, RoleRequiredMixin, View):
    required_role = Role.ADMIN

    _HEADERS = [
        "Zeitstempel",
        "Benutzer",
        "Aktion",
        "Objekttyp",
        "Objekt-ID",
        "Objekt",
        "IP-Adresse",
    ]

    def get(self, request, fmt):
        qs = _apply_filters(
            AuditLog.objects.select_related("actor", "content_type"),
            AuditFilterForm(request.GET or None),
        )
        if fmt == "csv":
            return self._export_csv(qs)
        if fmt == "xlsx":
            return self._export_xlsx(qs)
        raise Http404

    def _rows(self, qs):
        for entry in qs:
            yield [
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                entry.actor_username,
                entry.get_action_display(),
                entry.content_type.model if entry.content_type else "",
                entry.object_id,
                entry.object_repr,
                entry.ip_address or "",
            ]

    def _export_csv(self, qs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="audit-trail.csv"'
        response.write("\ufeff")  # UTF-8 BOM so Excel opens it correctly
        writer = csv.writer(response)
        writer.writerow(self._HEADERS)
        for row in self._rows(qs):
            writer.writerow(row)
        return response

    def _export_xlsx(self, qs):
        import openpyxl
        from openpyxl.styles import Font

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Audit-Trail"

        ws.append(self._HEADERS)
        for cell in ws[1]:
            cell.font = Font(bold=True)

        for row in self._rows(qs):
            ws.append(row)

        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=0)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        response = HttpResponse(
            buf.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="audit-trail.xlsx"'
        return response


# ---------------------------------------------------------------------------
# Shared filter logic
# ---------------------------------------------------------------------------

def _apply_filters(qs, form):
    if not form.is_valid():
        return qs
    cd = form.cleaned_data
    if cd.get("date_from"):
        qs = qs.filter(timestamp__date__gte=cd["date_from"])
    if cd.get("date_to"):
        qs = qs.filter(timestamp__date__lte=cd["date_to"])
    if cd.get("q"):
        qs = qs.filter(
            Q(actor_username__icontains=cd["q"])
            | Q(object_repr__icontains=cd["q"])
        )
    if cd.get("action"):
        qs = qs.filter(action=cd["action"])
    if cd.get("model"):
        qs = qs.filter(content_type_id=cd["model"])
    return qs
