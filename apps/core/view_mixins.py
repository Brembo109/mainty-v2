from django.utils.translation import gettext_lazy as _


class EmptyStateMixin:
    """Adds empty-state context for ListViews used with templates/partials/empty_state.html.

    Subclasses set:
      empty_icon          — icon slug (asset, task, qualification, …)
      empty_title         — first-run heading
      empty_desc          — first-run one-sentence description
      empty_primary       — optional dict {label, url, icon} for primary CTA
      empty_secondary     — optional dict {label, url} for secondary CTA

    Auto-derived:
      filters_active        — True if any GET param other than `page` is set
      reset_filters_action  — secondary CTA pointing back to the bare path
    """

    empty_icon = "search"
    empty_title = _("Keine Einträge")
    empty_desc = ""
    empty_primary = None
    empty_secondary = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = {k: v for k, v in self.request.GET.items() if k != "page" and v}
        ctx["filters_active"] = bool(params)
        ctx["reset_filters_action"] = {
            "label": _("Filter zurücksetzen"),
            "url": self.request.path,
        }
        ctx["empty_icon"] = self.empty_icon
        ctx["empty_title"] = self.empty_title
        ctx["empty_desc"] = self.empty_desc
        ctx["empty_primary"] = self.empty_primary
        ctx["empty_secondary"] = self.empty_secondary
        return ctx
