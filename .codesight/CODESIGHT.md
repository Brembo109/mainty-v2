# mainty-v2 — AI Context Map

> **Stack:** raw-http | none | unknown | javascript

> 0 routes | 0 models | 0 components | 70 lib files | 24 env vars | 2 middleware | 44 import links
> **Token savings:** this file is ~2,200 tokens. Without it, AI exploration would cost ~28,200 tokens. **Saves ~26,000 tokens per conversation.**

---

# Libraries

- `apps/accounts/admin.py` — class UserAdmin
- `apps/accounts/apps.py` — class AccountsConfig
- `apps/accounts/constants.py` — class Role
- `apps/accounts/forms.py`
  - class LoginForm
  - class StyledPasswordChangeForm
  - class StyledSetPasswordForm
  - class UserCreateForm
  - class UserUpdateForm
  - class AdminSetPasswordForm
- `apps/accounts/management/commands/bootstrap_roles.py` — class Command
- `apps/accounts/management/commands/create_initial_admin.py` — class Command
- `apps/accounts/middleware.py` — class PasswordExpiryMiddleware
- `apps/accounts/migrations/0001_initial.py` — class Migration
- `apps/accounts/migrations/0002_user_theme.py` — class Migration
- `apps/accounts/mixins.py` — class WriteAccessMixin, class RoleRequiredMixin
- `apps/accounts/models.py` — class User
- `apps/accounts/tests.py`
  - class UserThemeDefaultTest
  - class SetThemeViewTest
  - class UserCreateFormTest
  - class UserUpdateFormTest
  - class AdminSetPasswordFormTest
  - class UserListViewTest
  - _...5 more_
- `apps/accounts/utils.py` — function axes_lockout_response: (request, credentials, *args, **kwargs)
- `apps/accounts/views.py`
  - function set_theme: (request)
  - class LoginView
  - class LogoutView
  - class PasswordChangeView
  - class PasswordChangeDoneView
  - class PasswordResetView
  - _...11 more_
- `apps/assets/admin.py` — class AssetAdmin
- `apps/assets/apps.py` — class AssetsConfig
- `apps/assets/constants.py` — class AssetStatus, class Department
- `apps/assets/forms.py` — class AssetForm, class AssetFilterForm
- `apps/assets/migrations/0001_initial.py` — class Migration
- `apps/assets/migrations/0002_asset_extended_fields.py` — class Migration
- `apps/assets/migrations/0003_remove_device_code_inventory_number_defaults.py` — class Migration
- `apps/assets/models.py` — class Asset
- `apps/assets/tests.py`
  - function make_user: (username)
  - function make_asset: (**kwargs)
  - class AssetDepartmentFieldTest
  - class AssetIdentificationFieldsTest
  - class AssetResponsibilityFieldsTest
  - class AssetFormValidationTest
  - _...1 more_
- `apps/assets/views.py`
  - class AssetListView
  - class AssetDetailView
  - class AssetCreateView
  - class AssetUpdateView
  - class AssetDeleteView
- `apps/audit/admin.py` — class AuditLogAdmin
- `apps/audit/apps.py` — class AuditConfig
- `apps/audit/constants.py` — class Action
- `apps/audit/forms.py` — class AuditFilterForm
- `apps/audit/middleware.py`
  - function get_current_user: ()
  - function get_current_ip: ()
  - class AuditMiddleware
- `apps/audit/migrations/0001_initial.py` — class Migration
- `apps/audit/mixins.py` — class AuditedModel
- `apps/audit/models.py` — class AuditLog
- `apps/audit/signals.py`
  - function connect_audit_signals: (model_class)
  - function on_login: (sender, request, user, **kwargs)
  - function on_logout: (sender, request, user, **kwargs)
  - function on_login_failed: (sender, credentials, request, **kwargs)
- `apps/audit/views.py` — class AuditLogListView, class AuditLogExportView
- `apps/contracts/admin.py` — class ContractAdmin
- `apps/contracts/apps.py` — class ContractsConfig
- `apps/contracts/constants.py` — class ContractStatus
- `apps/contracts/forms.py` — class ContractForm, class ContractFilterForm
- `apps/contracts/migrations/0001_initial.py` — class Migration
- `apps/contracts/models.py` — class Contract
- `apps/contracts/views.py`
  - class ContractListView
  - class ContractDetailView
  - class ContractCreateView
  - class ContractUpdateView
  - class ContractDeleteView
- `apps/core/apps.py` — class CoreConfig
- `apps/core/management/commands/send_reminders.py` — class Command
- `apps/core/migrations/0001_initial.py` — class Migration
- `apps/core/models.py` — class ReminderLog
- `apps/core/tests.py` — function test_health_endpoint: (client)
- `apps/core/views.py` — function health: (request), function index: (request)
- `apps/maintenance/admin.py`
  - class MaintenanceRecordInline
  - class MaintenancePlanAdmin
  - class MaintenanceRecordAdmin
- `apps/maintenance/apps.py` — class MaintenanceConfig
- `apps/maintenance/constants.py` — class MaintenanceStatus
- `apps/maintenance/forms.py`
  - class MaintenancePlanCreateForm
  - class MaintenancePlanUpdateForm
  - class MaintenanceRecordForm
- `apps/maintenance/migrations/0001_initial.py` — class Migration
- `apps/maintenance/models.py` — class MaintenancePlan, class MaintenanceRecord
- `apps/maintenance/views.py`
  - class MaintenancePlanListView
  - class MaintenancePlanDetailView
  - class MaintenancePlanCreateView
  - class MaintenancePlanUpdateView
  - class MaintenancePlanDeleteView
  - class MaintenanceRecordCreateView
- `apps/qualification/admin.py` — class QualificationCycleAdmin, class QualificationSignatureAdmin
- `apps/qualification/apps.py` — class QualificationConfig
- `apps/qualification/constants.py` — class QualType, class QualStatus
- `apps/qualification/forms.py`
  - class QualificationCycleCreateForm
  - class QualificationCycleUpdateForm
  - class SignatureForm
- `apps/qualification/migrations/0001_initial.py` — class Migration
- `apps/qualification/models.py` — class QualificationCycle, class QualificationSignature
- `apps/qualification/views.py`
  - class QualificationCycleListView
  - class QualificationCycleDetailView
  - class QualificationCycleCreateView
  - class QualificationCycleUpdateView
  - class QualificationCycleDeleteView
  - class QualificationSignView
- `apps/tasks/admin.py` — class TaskAdmin
- `apps/tasks/apps.py` — class TasksConfig
- `apps/tasks/constants.py` — class TaskStatus, class TaskPriority
- `apps/tasks/forms.py` — class TaskCreateForm, class TaskUpdateForm
- `apps/tasks/migrations/0001_initial.py` — class Migration
- `apps/tasks/models.py` — class Task
- `apps/tasks/tests.py` — class TaskCreateFormAssetsFieldTest, class TaskCreateViewBulkTest
- `apps/tasks/views.py`
  - class TaskListView
  - class TaskDetailView
  - class TaskCreateView
  - class TaskUpdateView
  - class TaskDeleteView
- `manage.py` — function main: ()

---

# Config

## Environment Variables

- `ADMINS` (has default) — .env.example
- `ALLOWED_HOSTS` (has default) — .env.example
- `CONTRACT_EXPIRY_WARNING_DAYS` (has default) — .env.example
- `DATABASE_URL` (has default) — .env.example
- `DEBUG` (has default) — .env.example
- `DEFAULT_FROM_EMAIL` (has default) — .env.example
- `DJANGO_ADMIN_EMAIL` (has default) — .env.example
- `DJANGO_ADMIN_PASSWORD` (has default) — .env.example
- `DJANGO_ADMIN_USER` (has default) — .env.example
- `EMAIL_BACKEND` (has default) — .env.example
- `EMAIL_HOST` (has default) — .env.example
- `EMAIL_HOST_PASSWORD` **required** — .env.example
- `EMAIL_HOST_USER` **required** — .env.example
- `EMAIL_PORT` (has default) — .env.example
- `EMAIL_USE_TLS` (has default) — .env.example
- `PASSWORD_EXPIRY_DAYS` (has default) — .env.example
- `POSTGRES_DB` (has default) — .env.example
- `POSTGRES_HOST` (has default) — .env.example
- `POSTGRES_PASSWORD` (has default) — .env.example
- `POSTGRES_PORT` (has default) — .env.example
- `POSTGRES_USER` (has default) — .env.example
- `REMINDER_EMAIL_SUBJECT` (has default) — .env.example
- `SECRET_KEY` (has default) — .env.example
- `SITE_URL` (has default) — .env.example

## Config Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `tailwind.config.js`

---

# Middleware

## auth
- middleware — `apps/accounts/middleware.py`
- middleware — `apps/audit/middleware.py`

---

# Dependency Graph

## Most Imported Files (change these carefully)

- `/models.py` — imported by **20** files
- `/constants.py` — imported by **13** files
- `/forms.py` — imported by **7** files
- `/base.py` — imported by **2** files
- `/mixins.py` — imported by **1** files
- `/middleware.py` — imported by **1** files

## Import Map (who imports what)

- `/models.py` ← `apps/accounts/admin.py`, `apps/accounts/forms.py`, `apps/accounts/views.py`, `apps/assets/admin.py`, `apps/assets/forms.py` +15 more
- `/constants.py` ← `apps/accounts/forms.py`, `apps/accounts/mixins.py`, `apps/accounts/views.py`, `apps/assets/forms.py`, `apps/assets/models.py` +8 more
- `/forms.py` ← `apps/accounts/views.py`, `apps/assets/views.py`, `apps/audit/views.py`, `apps/contracts/views.py`, `apps/maintenance/views.py` +2 more
- `/base.py` ← `mainty/settings/development.py`, `mainty/settings/production.py`
- `/mixins.py` ← `apps/accounts/views.py`
- `/middleware.py` ← `apps/audit/signals.py`

---

_Generated by [codesight](https://github.com/Houseofmvps/codesight) — see your codebase clearly_