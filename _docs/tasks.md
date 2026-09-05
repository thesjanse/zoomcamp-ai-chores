# Backlog

Each issue is groomed using `_docs/task-template.md` (Goal, Acceptance
criteria, Out of scope, Constraints). Acceptance criteria are checkable by
looking at the result. Everything moved out of scope links to a GitHub issue
via its URL/number.

## 1. Project Setup with Passing Test

Goal: Have a runnable Django project with one passing test.

Acceptance criteria:
- [ ] `uv sync` installs all dependencies without error
- [ ] `uv run pytest` passes green (at least `tests/test_home.py`)
- [ ] `uv run python manage.py runserver` starts without error
- [ ] The home view at `/` returns HTTP 200 on GET
- [ ] A test for the home view exists and asserts the 200 response
- [ ] All scaffolding (manage.py, settings, urls, wsgi) is committed

Out of scope:
- Any real application UI or model — added in later issues
- HTMX / Alpine.js / Bootstrap setup — issue #18

Constraints:
- Stay inside the `app` Django project directory (or equivalent root package)
- Use Django and pytest (pytest-django) via `uv` in `pyproject.toml`
- Follow `_docs/AGENTS.md`; only add dependencies by asking first

## 2. Household Model & Admin Registration

Goal: Persist a household so it can be stored in the database and managed via Django Admin.

Acceptance criteria:
- [ ] A `Household` model exists with a required `name` field (max length defined)
- [ ] A non-editable `created_at` field is auto-set on creation
- [ ] The model is registered in Django Admin
- [ ] A household record can be created, viewed, and edited from Admin
- [ ] Creating a household with an empty `name` is rejected (validation error)
- [ ] A test creates a household via the ORM and asserts it exists in the database

Out of scope:
- `invite_code` generation and uniqueness — issue #6
- Linking users to a household — issue #5
- Admin vs member roles — issue #14

Constraints:
- Live in a `households` Django app
- Use standard Django model and admin patterns

## 3. User Registration

Goal: Let a new user sign up with username, email, and password.

Acceptance criteria:
- [ ] A `/register` page renders a registration form on GET
- [ ] Submitting valid data creates a new user with username, email, and password
- [ ] The newly registered user is logged in automatically
- [ ] After registration the user is redirected to onboarding (issue #5)
- [ ] An already-taken username shows a validation error and re-renders the form
- [ ] Mismatched or too-weak passwords are rejected with an error
- [ ] A test posts valid registration data and asserts the user is created and logged in

Out of scope:
- Login/logout — issue #4
- Onboarding (create/join household) — issue #5
- Password reset — issue #15

Constraints:
- Use Django's `UserCreationForm` or a thin subclass
- Templates live in the app's templates directory

## 4. User Login & Logout

Goal: Authenticate users with username and password.

Acceptance criteria:
- [ ] A `/login` page renders a login form on GET
- [ ] A registered user with correct credentials is logged in and redirected
- [ ] The `next` query parameter is honored safely (no open redirect)
- [ ] Invalid credentials are rejected and an error message is shown
- [ ] An already-authenticated user visiting `/login` is redirected away
- [ ] Logout ends the session and redirects to a confirmation page or `/`
- [ ] A protected view redirects an anonymous user to `/login`
- [ ] Tests cover: successful login, rejected invalid credentials, and logout

Out of scope:
- Registration — issue #3
- Password reset — issue #15

Constraints:
- Use Django's built-in `LoginView` and `LogoutView`
- Templates live in the app's templates directory

## 5. Onboarding Flow — Create or Join Household

Goal: After registration, a new user chooses to create a new household or join an existing one via invite code.

Acceptance criteria:
- [ ] After successful registration the user is redirected to an `/onboarding` page
- [ ] The page presents two options: "Create a New Household" and "Join via Invite Code"
- [ ] Choosing Create prompts for a household name, creates the household, and links the user
- [ ] The creating user is linked as admin (see issue #14)
- [ ] Choosing Join prompts for an invite code, validates it, and links the user
- [ ] An invalid invite code shows an error and does not link the user
- [ ] A user who already has a household is redirected away from onboarding
- [ ] A test follows the full flow and verifies the user ends up linked to a household

Out of scope:
- Invite code generation/format/uniqueness — issue #6
- Admin vs member role handling — issue #14

Constraints:
- Defines/uses a `HouseholdMember` join model linking user to household
- Depends on issue #6 for generating the invite code on household creation

## 6. Invite Code Generation

Goal: Each household gets a unique, shareable, human-readable invite code, auto-generated on creation and visible (read-only) in Django Admin.

Acceptance criteria:
- [ ] Creating a household via the ORM (`Household.objects.create(...)`) results in a non-empty `invite_code` on the saved instance
- [ ] The generated code matches the pattern `^HOME-[A-Z0-9]{4}$` (e.g. `HOME-7X9B`)
- [ ] Every household in the database has a non-empty `invite_code`
- [ ] Two different households never share the same `invite_code`: the field is unique at the database level (unique constraint) and `generate_invite_code()` regenerates on collision
- [ ] Saving a household that already carries an `invite_code` used by another household is rejected (uniqueness is not bypassed)
- [ ] The `invite_code` is shown in Django Admin's household list and is read-only (not editable) in the change form
- [ ] A test creates multiple households and asserts each has a non-empty code matching the format and that all codes are mutually unique

Out of scope:
- Regenerating an existing code from Admin — issue #13
- Onboarding/join flow using the code — issue #5
- Sharing UI beyond displaying the code

Constraints:
- Generate on model `save()` or via a signal in the `households` app
- The `invite_code` field is unique (`unique=True` or a `UniqueConstraint`) and non-editable (`editable=False`)

## 7. Chore Model & CRUD

Goal: A `Chore` model exists and household members can create, list, view, edit, and delete chores within their own household.

Acceptance criteria:
- Model (`chores` app, `chores/models.py`):
  - [ ] A `Chore` model exists with fields: `title` (CharField, required), `description` (TextField, optional/nullable), `assigned_to` (FK to `auth.User`, nullable, `on_delete=SET_NULL`, default unassigned/`None`), `due_date` (DateField, nullable/optional), `status` (CharField with choices `open`/`in_progress`/`done`, default `open`), `household` (FK to `Household`, `on_delete=CASCADE`, `related_name="chores"`), `created_at` (DateTimeField, auto-set), `completed_at` (DateTimeField, nullable — schema only, not editable here; recording it is issue #10's job)
  - [ ] A `Chore` belonging to a given household can be created via the ORM and read back with the correct field values
  - [ ] `status` choices are exactly `open` / `in_progress` / `done` and the default for a new chore is `open` (fixed now because issues #8/#10 depend on them)
  - [ ] `assigned_to` and `status` default to unassigned / `open` on a new chore (chores enter the pool unassigned; claiming is issue #8)
  - [ ] The `chores` app is listed in `INSTALLED_APPS` in `app/settings.py`
- Routes and views (function or class-based, `chores/urls.py` wired from `app/urls.py`):
  - [ ] `GET /chores/` renders a list of the current user's household chores (name `chore_list`)
  - [ ] `GET /chores/new/` renders a create form; `POST /chores/new/` creates a chore and redirects to the list (name `chore_create`)
  - [ ] `GET /chores/<int:pk>/` renders a single chore's details (name `chore_detail`)
  - [ ] `GET /chores/<int:pk>/edit/` renders an edit form; `POST /chores/<int:pk>/edit/` saves changes and redirects to the list (name `chore_update`)
  - [ ] `GET /chores/<int:pk>/delete/` renders a delete-confirmation page; `POST /chores/<int:pk>/delete/` deletes the chore and redirects to the list (name `chore_delete`)
  - [ ] The create/edit forms expose only `title`, `description`, and `due_date` — `status` and `assigned_to` are NOT form fields (set by issues #8 and #10)
- Authentication and household guard (single household per user via `HouseholdMember`):
  - [ ] An anonymous user hitting any `/chores/...` route is redirected to `/login` (`login_required` / `LOGIN_URL='login'`)
  - [ ] A logged-in user with no `HouseholdMember` (not onboarded) is redirected to `/onboarding` on any `/chores/...` route
  - [ ] Accessing a chore by a pk belonging to a household the user is NOT a member of returns HTTP 404 on list/detail/edit/delete (never revealed or modified)
  - [ ] All querysets are scoped to the current user's household
- Templates:
  - [ ] List, detail, create/edit, and delete-confirmation templates live under `chores/templates/chores/` and extend `accounts/base.html`
  - [ ] The delete-confirmation page shows the chore's title and only `POST` deletes (GET shows the confirm step and does not delete)
- Tests (`tests/test_chores.py`, matching existing `TestCase`/`Client` conventions):
  - [ ] Creating a chore persists it with `status=open` and `assigned_to=None`
  - [ ] The list page shows only the current user's household chores (foreign chore absent)
  - [ ] Create, update, and delete each work end to end (POST → redirect → verify DB)
  - [ ] GET `/chores/<pk>/delete/` does NOT delete; POST does
  - [ ] Anonymous access to a chore route redirects to `/login`
  - [ ] A logged-in user with no household is redirected to `/onboarding`
  - [ ] Detail/edit/delete of a foreign household's chore returns 404 without modifying/deleting it
  - [ ] A chore can be created with an empty description and no due date (both optional)

Out of scope:
- Chore market / claiming unassigned chores — issue #8
- Marking a chore done / recording `completed_at` — issue #10
- Calendar view — issue #9
- Late-task indicators and notifications — issues #11 and #12
- HTMX / Alpine.js / Bootstrap UI work — issue #18
- Managing `status` / `assigned_to` through the edit form (governed by #8/#10)

Constraints:
- Live in a new `chores` Django app, added to `INSTALLED_APPS`
- Reuse `Household` / `HouseholdMember` from the `households` app; single household per user resolved via `HouseholdMember`
- Use Django template views (function or class based) and Django forms
- All querysets scoped to the current user's household; never reveal or mutate foreign chores
- Status is a CharField with choices `open` / `in_progress` / `done`, default `open`
- Follow `_docs/AGENTS.md`; add dependencies (if any) only after asking

## 8. Chore Market — Browse & Claim Tasks

Goal: A "Chore Market" page lists all unassigned chores in the current user's household and lets the user claim one with a single in-place click (HTMX swap, no full page reload), removing it from the pool.

Acceptance criteria:
- Market page (`GET /chores/market/`, name `chore_market`):
  - [ ] Renders only chores where `status == 'open'` AND `assigned_to is None` for the current user's household
  - [ ] Each listed chore shows its title (and clicking it links to its detail page if already present) plus a "Claim" button
  - [ ] The market template extends `accounts/base.html`, is served at `/chores/market/`, and renders a Claim button for every listed chore
- Claim action (`POST /chores/<int:pk>/claim/`, name `chore_claim`):
  - [ ] A successful claim sets `assigned_to = request.user` and `status = 'in_progress'`, then returns `HTTP 200` with an empty/blank body (partial HTMX response) — no full page redirect
  - [ ] The claimed chore disappears from the market list on a refresh (its old row is replaced by nothing)
  - [ ] The "Claim" button is a plain `<form method="post" action="{% url 'chore_claim' chore.pk %}">` enhanced with HTMX attributes so the click does an in-place swap of just that row to nothing (no full page reload)
- Race-safety and guarding:
  - [ ] An already-assigned chore (`assigned_to` no longer `None`) cannot be claimed a second time (double-claim prevention is atomic)
  - [ ] Claiming a chore that is already `in_progress`/`done` or assigned does nothing and returns `HTTP 200` with an empty body (idempotent no-op, not an error)
- Auth and household guard (reuse the exact #7 pattern):
  - [ ] An anonymous user hitting `/chores/market/` or any `/chores/<pk>/claim/` is redirected to `/login`
  - [ ] A logged-in user with no `HouseholdMember` is redirected to `/onboarding` on both routes
  - [ ] A user who is not a member of the chore's household gets `HTTP 404` on the market and claim routes (never reveals or claims foreign chores)
- Tests (`tests/test_chores.py`, existing `TestCase`/`Client` conventions):
  - [ ] The market page lists only `open` + unassigned chores in the user's household, and excludes assigned, done, and foreign chores
  - [ ] POSTing a claim sets the chore to `assigned_to=user`, `status='in_progress'`, returns `HTTP 200`, and the chore no longer appears in the market query
  - [ ] Double-claim prevention: after one claim, a second claim (by the same or another member) does not change the chore and the original assignee is preserved
  - [ ] A user from a foreign household gets `HTTP 404` when claiming and the chore is not modified
  - [ ] Anonymous claim redirects to `/login`; a logged-in user with no household is redirected to `/onboarding`

Out of scope:
- Setting up HTMX / Alpine.js / Bootstrap in the base template and any shared design-system work — issue #18
- Marking a claimed chore done / recording `completed_at` — issue #10
- Late-task notifications — issue #12
- Linking the market page from the site navigation/header — issue #18 (base-template work); for now link from the chore list template only if convenient
- Any changes to `accounts/base.html` — that is #18's file; do not touch it

Constraints:
- Files: `chores/views.py`, `chores/urls.py`, `chores/templates/chores/chore_market.html`, `tests/test_chores.py`. Do NOT modify `accounts/base.html` (owned by #18).
- URLs (flat, matching the existing `chores/urls.py` style, no namespacing):
  - `path("chores/market/", views.chore_market, name="chore_market")`
  - `path("chores/<int:pk>/claim/", views.chore_claim, name="chore_claim")`
- Market definition of "open, unassigned": `Chore.objects.filter(household=request.household, status="open", assigned_to__isnull=True)` — this exact queryset drives both the page and the claim guard.
- Household guard: reuse identical logic to #7 — decorate both views with `@login_required` + the existing `_household_or_redirect_decorator` (no household → `/onboarding`), and scope the chore fetch to `household=request.household` so a foreign pk is `HTTP 404` (`get_object_or_404(Chore, pk=pk, household=request.household, status="open", assigned_to__isnull=True)` for the claim).
- HTMX inclusion — resolving the #8 / #18 tension WITHOUT doing #18's base-template/design-system work:
  - Do NOT edit `accounts/base.html`.
  - The claim works as a normal conditional POST that returns a tiny partial fragment; HTMX is an enhancement only.
  - Include HTMX for this page only via a single CDN `<script src="https://unpkg.com/htmx.org@1.9.12"></script>` tag placed inside the `content` block of `chore_market.html` (top of the block is fine). This is a page-local, self-contained include and deliberately does not set up the shared base template — that is exactly #18's scope.
  - The Claim button/row: render each market chore inside an element with HTMX attributes, e.g. `<form method="post" hx-post="{% url 'chore_claim' chore.pk %}" hx-target="closest li" hx-swap="outerHTML">` so a successful claim swaps that row out with the (empty) response, removing it from the DOM in place. For non-JS/no-HTMX clients the form still POSTs and the server returns 200; include `{% csrf_token %}` in each claim form.
  - The claim view itself must work with or without HTMX: it does the claim, then returns `HttpResponse(status=200)` (empty) after a successful claim, and the same empty 200 for the race-lost no-op case. It never redirects.
- Race-safety: use a single atomic conditional UPDATE (chosen over `select_for_update` because it is simpler and race-safe for this single-row swap and matches the #10 pattern):
  - `updated = Chore.objects.filter(pk=pk, household=request.household, status="open", assigned_to__isnull=True).update(assigned_to=request.user, status="in_progress")`
  - This is atomic in the DB: only one concurrent claim's `UPDATE ... WHERE assigned_to IS NULL` can match. If `updated == 0`, the chore was already claimed/not open — return `HttpResponse(status=200)` empty (no-op) and do not touch it.
- Auth requirement: claim requires login + membership. The claim form submits `POST` with a CSRF token.
- Use Django template views (function or class based) and Django forms as in #7. Follow `_docs/AGENTS.md`; do not add dependencies without asking (the HTMX CDN script is loaded from the network at runtime, no Python package).
- Read `_docs/testing-guidelines.md` before writing tests.

## 9. Calendar View with Deadlines

Goal: Users see their household's chores placed on a month-grid calendar by `due_date`, with each cell color-coded by how soon (or overdue) the chore is. This task also introduces the small shared late-detection helper that issue #11 will reuse.

Acceptance criteria:

Month-grid rendering:
- [ ] `GET /chores/calendar/` (URL name `chore_calendar`) renders a month-grid layout of seven columns labeled Mon–Sun (or Sun–Sat) with date rows for the current month, built purely with Django templates (no external calendar library, no JS grid construction)
- [ ] The view uses Python's `calendar` module only to compute dates; all rendering is plain Django template `for` loops inside `chores/calendar.html`
- [ ] The default displayed month is the current month; "today" is computed in the view as `timezone.localdate()` so it is deterministic under `USE_TZ=True` and in tests
- [ ] The rendered page shows the month name/year (e.g. "September 2026") so an observer can identify which month is shown

Chores placed in cells:
- [ ] Every chore in the current user's household that has a `due_date` falling within the displayed month appears in the grid cell matching its `due_date` day; the title is rendered inside that cell
- [ ] A chore with no `due_date` is never placed in any cell (omitted from the grid entirely)
- [ ] Chores whose `due_date` is in another month are not shown, and no cell ever contains a chore that does not belong there
- [ ] Both `done` and non-`done` chores with a `due_date` in the month are shown (done chores render green, see color rule)

Color coding (green / yellow / red), applied per chore, decided in strict priority order using TODAY = `timezone.localdate()` and the shared helper in `chores/utils.py`:
- [ ] **No due date** -> no color class (renders with the neutral `calendar-none` class)
- [ ] **`status == "done"`** -> always green (`calendar-on-time`), regardless of how old `due_date` is (a done chore is never overdue/red; matches issue #11)
- [ ] **`due_date < TODAY`** and status is `open`/`in_progress` -> red (`calendar-overdue`) — the "overdue" definition shared with #11 = `due_date` before today AND status != `done`
- [ ] **TODAY <= `due_date` <= TODAY + 3 days** and status is `open`/`in_progress` -> yellow (`calendar-due-soon`) — "due soon" is defined as due within the next 3 days inclusive, not yet past
- [ ] **`due_date > TODAY + 3 days`** and status is `open`/`in_progress` -> green (`calendar-on-time`)
- [ ] A chore that is overdue but `done` renders green, not red
- [ ] The exact color is checkable in rendered HTML by asserting the cell/link carries the matching CSS class name above

Shared helper ownership (resolves the #9 / #11 tension):
- [ ] A helper `chore_color_class(chore, today)` exists in `chores/utils.py` and implements exactly the priority-order color rule above (it is the single source of truth for green/yellow/red/none)
- [ ] The view/template call this helper for every chore; no color logic is duplicated in the template
- [ ] Issue #11 (Late Task Indicators) is documented to reuse this same helper for its red highlighting; #9 owns creating the helper, #11 only consumes it

Only the current user's household chores:
- [ ] Anonymous access to `/chores/calendar/` redirects to `/login` (reuse `@login_required`)
- [ ] A logged-in user with no `HouseholdMember` is redirected to `/onboarding` (reuse the existing `_household_or_redirect_decorator`)
- [ ] Chores from other households never appear on the calendar (query scoped to `household=request.household`)

Tests (`tests/test_chores.py`, existing `TestCase`/`Client` conventions; dates via `date.today()`/`timedelta` or `timezone.localdate()` so they are relative and deterministic):
- [ ] A test renders the calendar for the current month and asserts each household chore is shown in the cell of its `due_date`
- [ ] A test creates chores with due dates relative to today (overdue in the past, due today, due soon within 3 days, and comfortably far away) and asserts the matching `calendar-overdue` / `calendar-due-soon` / `calendar-on-time` classes appear in the HTML
- [ ] A test creates a `done` chore with a past due date and asserts it renders green (`calendar-on-time`), not red
- [ ] A test creates a chore with no `due_date` and asserts it is not rendered on the calendar
- [ ] A test asserts foreign-household chores are not shown
- [ ] A test with a chore due in a different month asserts it is not shown in the current month's grid
- [ ] A test asserts anonymous access redirects to `/login` and a user without a household is redirected to `/onboarding`
- [ ] A unit test on `chore_color_class` covers all branches: no-due-date, done, overdue, due-soon, on-time

Out of scope:
- Multi-month navigation (previous/next month) — issue #16
- The red-overdue highlighting / "late indicator" surfacing in the chore list and its UI polish — issue #11 consumes the helper created here but is implemented separately in #11
- Generating notifications for late chores — issue #12
- HTMX / Alpine.js / Bootstrap styling and design-system work in the base template — issue #18
- Any changes to `accounts/base.html` — that is #18's file

Constraints:
- Files: `chores/views.py`, `chores/urls.py`, `chores/utils.py` (new, contains the shared `chore_color_class` helper), `chores/templates/chores/calendar.html` (new), `tests/test_chores.py`. Do NOT modify `accounts/base.html` (owned by #18).
- URL (flat, matching the existing `chores/urls.py` style, no namespacing): `path("chores/calendar/", views.chore_calendar, name="chore_calendar")` — URL name `chore_calendar`, template `chores/calendar.html`.
- The calendar view is `@login_required` + the existing `_household_or_redirect_decorator`; query is `Chore.objects.filter(household=request.household, due_date__isnull=False)` so only the current household's dated chores are considered.
- "Today" is `timezone.localdate()` computed in the view (or the equivalent timezone-aware date), passed to the template/helper. Do not call `date.today()` directly.
- Color decision helper contract (single source of truth in `chores/utils.py`, reused by #11): `chore_color_class(chore, today)` returns one of `"calendar-overdue"`, `"calendar-due-soon"`, `"calendar-on-time"`, `"calendar-none"` following the strict priority order above.
  - Overdue (shared with #11): `due_date < today AND status != "done"`.
  - Due soon: `today <= due_date <= today + 3 days AND status != "done"`.
- Pure Django template rendering — the grid data (weeks/rows of day cells, `today`, and a `{date: [chores]}` mapping) is computed in the view; no external calendar library, no JavaScript for building the grid.
- The grid template extends `accounts/base.html` and extends the `content` block like the other `chores/*.html` templates.
- Use `django.utils.timezone` for deterministic date handling in tests. Follow `_docs/AGENTS.md`; add dependencies (if any) only after asking.

## 10. Task Completion (Honor System)

Goal: Users mark their own claimed chores as done. When marked done, the chore's status becomes `done` and `completed_at` is recorded. Done chores disappear from the active working views (the chore list and the market).

Acceptance criteria:

Chore detail page — "Mark Done" button:
- [ ] On `GET /chores/<int:pk>/`, a "Mark Done" button/form is rendered when AND ONLY when: the current user is the chore's `assigned_to`, AND the chore's `status` is `in_progress`
- [ ] The "Mark Done" button is NOT shown when: the chore is `open`/unassigned, the chore is already `done`, or the current user is not the assignee
- [ ] The button is a `<form method="post">` with HTMX attributes (`hx-post`, `hx-target`, `hx-swap`) following the same page-local HTMX pattern as #8's market/claim — include a CDN `<script>` in the detail template's `content` block, do NOT touch `accounts/base.html`

Done action — server-side:
- [ ] `POST /chores/<int:pk>/done/` (URL name `chore_done`) sets `status='done'` and `completed_at=timezone.now()` atomically via a conditional UPDATE: `Chore.objects.filter(pk=pk, household=request.household, status='in_progress', assigned_to=request.user).update(status='done', completed_at=timezone.now())`
- [ ] A successful done action returns HTTP 200 with an empty body (HTMX partial swap response)
- [ ] Double-completion is prevented: if the chore is already `done` (or not `in_progress`, or not assigned to the current user), the UPDATE matches zero rows and returns HTTP 200 empty (idempotent no-op, not an error)
- [ ] On a successful done action, the "Mark Done" form is swapped out of the DOM (HTMX `hx-swap="outerHTML"` replaces the target with the empty response, removing the button)

Auth and household guard (reuse existing pattern):
- [ ] An anonymous user hitting `POST /chores/<pk>/done/` is redirected to `/login`
- [ ] A logged-in user with no `HouseholdMember` is redirected to `/onboarding`
- [ ] A user from a foreign household gets HTTP 404 (never modifies a foreign chore)

View changes — chore list:
- [ ] The chore list view (`GET /chores/`) excludes chores with `status='done'` — done chores no longer appear in the list page
- [ ] A chore that is `in_progress` or `open` still appears in the list as before

View changes — calendar (no change from #9):
- [ ] The calendar view continues to show done chores (colored green, per #9's spec) — this issue does NOT change the calendar's behavior

View changes — market:
- [ ] The market view (`GET /chores/market/`) already excludes done chores (filters `status='open'`) — no change needed, but verify this remains true after the list changes

Tests (`tests/test_chores.py`):
- [ ] `test_mark_done_sets_status_and_completed_at`: POST to `chore_done` on an `in_progress` chore assigned to the current user; assert `status == 'done'` and `completed_at` is set (not None, close to `timezone.now()`)
- [ ] `test_mark_done_removes_chore_from_list`: after marking done, `GET /chores/` no longer contains the chore's title
- [ ] `test_unclaimed_chore_cannot_be_marked_done`: POST to `chore_done` on an `open`/unassigned chore; assert status remains `open` and assigned_to remains None (200 response, idempotent no-op)
- [ ] `test_already_done_chore_not_marked_done_again`: POST to `chore_done` on a chore already `done`; assert `completed_at` is unchanged and status remains `done` (idempotent 200)
- [ ] `test_foreign_chore_done_404`: POST to `chore_done` with a pk from another household; assert HTTP 404 and the chore is not modified
- [ ] `test_anonymous_done_redirected_to_login`: unauthenticated POST to `chore_done` redirects to `/login`
- [ ] `test_no_household_user_done_redirected_to_onboarding`: logged-in user with no household POST to `chore_done`; redirects to `/onboarding`

Out of scope:
- Unclaiming or reassigning a chore — no follow-up issue yet
- Late-task notifications — issue #12
- HTMX setup in the base template (shared CDN include, design system) — issue #18
- Any changes to `accounts/base.html` — that file is owned by #18
- Changing the calendar view to exclude done chores — #9's calendar is designed to show done chores green; a change to that is a separate issue
- Editing `completed_at` manually — field is `editable=False`

Constraints:
- Files: `chores/views.py`, `chores/urls.py`, `chores/templates/chores/chore_detail.html`, `chores/templates/chores/chore_list.html`, `tests/test_chores.py`. Do NOT modify `accounts/base.html`.
- URL: `path("chores/<int:pk>/done/", views.chore_done, name="chore_done")` — flat, matching existing `chores/urls.py` style.
- The done view uses the same atomic conditional-update pattern as #8's claim: a single `QuerySet.update()` that only matches when `status='in_progress' AND assigned_to=request.user`, making double-completion safe without locks.
- The done view uses the same decorators as all other chore views: `@login_required` + `_household_or_redirect_decorator`. Household scoping via `household=request.household` in the queryset filter.
- HTMX inclusion: page-local `<script src="https://unpkg.com/htmx.org@1.9.12"></script>` in the `content` block of `chore_detail.html` — same pattern as #8's market template.
- The "Mark Done" form: `<form method="post" hx-post="{% url 'chore_done' chore.pk %}" hx-target="closest form" hx-swap="outerHTML">{% csrf_token %}<button>Mark Done</button></form>`. For non-JS clients the plain POST still works and returns 200.
- Set `completed_at` with `timezone.now()`, not `date.today()` — `completed_at` is a `DateTimeField`.
- The chore list view queryset adds `.exclude(status='done')` to the existing `Chore.objects.filter(household=request.household)`.
- Follow `_docs/testing-guidelines.md` before writing tests. Follow `_docs/AGENTS.md`; do not add dependencies without asking.

## 11. Late Task Indicators

Goal: Overdue chores are visually highlighted in red on the chore list page and the chore market page, reusing the shared color helper from #9 for consistency. The calendar already gets the red highlight via #9 — verified, no re-work here.

Scope note: #9's `chore_color_class` helper already turns overdue calendar cells red. The **new** work for this issue is applying the overdue indicator to the chore **list** and **market** row lists (and verifying the calendar is already covered).

Acceptance criteria:
- [ ] The chore list template reuses the existing `chore_color` templatetag (which calls `chore_color_class(chore)` from `chores/utils.py`) on each chore row — no overdue logic is re-implemented in the template or view
- [ ] In the list view, an overdue open/in_progress chore (due_date before today, status != `done`) renders with the CSS class `calendar-overdue` on its row element
- [ ] In the market view, an overdue open/unassigned chore renders with the CSS class `calendar-overdue` on its row element
- [ ] A chore due today is NOT marked overdue: it does not carry `calendar-overdue` (the helper returns `calendar-due-soon`, i.e. yellow, not red)
- [ ] A chore that is overdue but already `done` is NOT marked overdue (returns `calendar-on-time`); inherent to the helper and already covered by #9's unit tests — confirm the helper rule is unchanged
- [ ] The calendar view is already covered by #9: an overdue chore's calendar cell renders `calendar-overdue`. Verify this still holds after this issue's changes (no re-work, only a regression check)
- [ ] A test creates an overdue chore, GETs the chore list, and asserts the rendered HTML row carries `calendar-overdue` (e.g. `class="calendar-overdue"`)
- [ ] A test creates a due-today chore, GETs the chore list, and asserts the row does NOT carry `calendar-overdue`
- [ ] The list/market querysets remain scoped to the current user's household (overdue rows never leak foreign-household chores)

Out of scope:
- Generating notifications for late chores — issue #12
- Configurable overdue thresholds / strike times (no tracking of how long a chore has been overdue) — not filed separately; noted for a follow-up if product wants it, currently no issue
- Red styling/polish on the chore detail page — #19
- The actual CSS rules that make `calendar-overdue` red and any design-system/theme work — #18 (this issue only applies the class names; the styling is rendered by the base template/design-system in #18)

Constraints:
- Consume the shared `chore_color_class(chore, today)` helper introduced by issue #9 in `chores/utils.py` via the existing `chore_color` template filter — do NOT re-implement the color/overdue decision
- Reuse the exact CSS class name `calendar-overdue` that the helper returns, so the list/market rows share one testable class with the calendar (do not invent a new list-specific class name)
- "overdue" = due_date before today AND status != `done` (per the helper's rule); a chore due today is NOT overdue
- Files: `chores/templates/chores/chore_list.html`, `chores/templates/chores/chore_market.html`, `tests/test_chores.py`. No view/URL changes expected. Do NOT modify `accounts/base.html`, `chores/utils.py`, or the calendar template
- Templates must `{% load chore_tags %}` (as `calendar.html` already does) to use the `chore_color` filter
- Use `django.utils.timezone` (or mock `localdate`) for deterministic date handling in tests; follow `_docs/testing-guidelines.md`

## 13. Admin: Regenerate Invite Code

Goal: A household admin can regenerate a household's invite code from Django Admin, replacing it with a fresh unique code while invalidating the old one.

Acceptance criteria:
- [ ] A ModelAdmin action named `regenerate_invite_code` exists on `HouseholdAdmin`
- [ ] The action appears in Django Admin's action dropdown on the household list page
- [ ] Selecting one household and running the action regenerates its invite code
- [ ] Selecting multiple households and running the action regenerates each one's invite code
- [ ] The regenerated code is non-empty, matches the format `^HOME-[A-Z0-9]{4}$` (e.g. `HOME-7X9B`), and is saved to the database
- [ ] The regenerated code differs from the household's previous invite code
- [ ] The old invite code no longer exists in the database (unique constraint; old row's value is replaced)
- [ ] The action does not modify any other fields on the Household (`name` and `created_at` are unchanged)
- [ ] The admin sees a success message listing how many households were regenerated (standard Django admin messages framework)
- [ ] A test calls the admin action method directly on a Household instance, asserts: new code differs from old, new code matches the format, new code is persisted in DB (re-fetched from DB), old code is not found in DB
- [ ] A test verifies the action works for a bulk selection (multiple households in one action call)

Out of scope:
- Pending join flows that still reference the old invite code — old codes simply fail the lookup (future issue if needed)
- Non-admin users regenerating codes outside Django Admin
- Confirmation dialog before regeneration — Django Admin's built-in "Are you sure?" page covers this
- Regeneration audit log or history — follow-up if product wants it
- Batch regeneration via CLI or API

Constraints:
- Files: `households/admin.py` (add the action), `tests/test_household.py` (add tests)
- Reuse `Household.generate_invite_code()` from #6 — do not write a new code generator
- The action must call `instance.save(update_fields=["invite_code"])` to persist only the regenerated field
- Do not modify `Household.save()`, `Household.generate_invite_code()`, or the `invite_code` field definition
- Do not touch any other app or model
- Follow `_docs/AGENTS.md` and `_docs/testing-guidelines.md` (if present)
- Run `uv run pytest tests/test_household.py` to verify tests pass

## 14. Household Roles & Permissions

Goal: Every household member carries a role of either `admin` or `member`, the household creator becomes its first admin, and role-dependent actions are gated so only admins can manage household configuration or promote/demote members, while all members can still view and claim chores.

Acceptance criteria:

Role on the HouseholdMember model (`households/models.py`):
- [ ] `HouseholdMember` gains a `role` CharField with `choices` exactly `("admin", "admin")` and `("member", "member")`, a default of `"member"`, and `max_length` large enough for `"admin"`
- [ ] A member created without an explicit role (e.g. an existing member from before this change, or any code path that does not set `role`) is saved as `member` — the field's default guarantees a never-admin unless explicitly set
- [ ] Creating two `HouseholdMember` rows for the same (household, user) is still rejected (the existing `unique_together` is preserved)
- [ ] The Django Admin `HouseholdMemberAdmin` list displays `role` alongside `household`, `user`, and `joined_at`, so an observer can point at any member row in `/admin/` and read its role

Creator becomes admin (wired into the existing onboarding flow in `households/views.py`):
- [ ] On the "Create a New Household" onboarding branch, the `HouseholdMember` created for the creator is saved with `role="admin"`
- [ ] On the "Join via Invite Code" onboarding branch, the `HouseholdMember` created for the joiner is saved with `role="member"`
- [ ] After creating a household, an observer can confirm the creator's membership row shows `admin` and a later-joining user's row shows `member` (Django Admin / shell)

Member management page — promote & demote (admin-only):
- [ ] A route `GET /households/members/` (URL name `household_members`) renders a list of every member of the current user's household, each showing the member's username and role
- [ ] The page renders a "Make Admin" control next to each `member` and a "Make Member" control next to each `admin`
- [ ] `POST /households/members/<int:pk>/promote/` (URL name `member_promote`) changes that member's role to `admin`; the member list page reflects the new role immediately after
- [ ] `POST /households/members/<int:pk>/demote/` (URL name `member_demote`) changes that member's role to `member`; the member list page reflects the new role immediately after

Role gating (the core rule):
- [ ] A `member` (non-admin) requesting `GET` or `POST` on ANY of `/households/members/`, `/households/members/<pk>/promote/`, `/households/members/<pk>/demote/`, `/households/members/settings/` (or whichever settings route is used) receives `HTTP 403` and the action is NOT performed — the controls are also not rendered for them
- [ ] An anonymous user on these household-management routes is redirected to `/login`
- [ ] A logged-in user with no `HouseholdMember` on these household-management routes is redirected to `/onboarding`
- [ ] Promoting or demoting a member of a FOREIGN household (one the acting user is not a member of) returns `HTTP 404` and does not change that membership (querysets scoped to the acting user's own household)
- [ ] Ordinary members can still view chores and claim chore via the market as before (no behavior change): the existing `/chores/...` routes remain accessible to `member`-role users, verified by a member successfully viewing the chore list and claiming a chore

Edge cases the original issue missed:
- [ ] A `member` cannot promote themselves to `admin` (the promote action is only offered/applied by an `admin`, and a member is never an actor on these routes)
- [ ] The last remaining `admin` of a household cannot be demoted: demoting the only admin leaves that member as `admin` (the role is unchanged) and returns a 403 with a visible message such as "A household must have at least one admin"
- [ ] Demoting the only admin is the only case where an admin's own demote action is blocked; if another admin exists, either admin may demote the other (still protected by the last-admin rule so the household never has zero admins)
- [ ] Promote/demote are idempotent-friendly and safe: promoting an already-`admin` or demoting an already-`member` member does not error
- [ ] Changing a member's role never modifies the member's `user`, `household`, or `joined_at` and never affects their existing chore assignments

Tests (`tests/test_household.py`, existing `TestCase`/`Client` conventions):
- [ ] A new `HouseholdMember` created without a role defaults to `member`
- [ ] The onboarding CREATE branch creates a member whose `role` is `admin`; the JOIN branch creates a member whose `role` is `member`
- [ ] A `member` user gets `HTTP 403` on the member-list page, on promote, and on demote, and the target role is unchanged
- [ ] An `admin` promoting a member changes that member to `admin` (persisted in DB); an `admin` demoting an admin changes them to `member`
- [ ] A member attempting to promote/demote/self-promote does not change any role and receives 403
- [ ] Demoting the only admin returns 403 and the member remains `admin`
- [ ] A user from a foreign household gets `HTTP 404` on promote/demote and the foreign membership is unchanged
- [ ] A `member`-role user can still GET the chore list and POST a chore claim successfully

Out of scope:
- Building the household **onboarding** create/join UI or the invite-code flow — already completed in #5 (closed); this issue only adds the `role` plumbing to the existing created onboarding code so the creator is admin
- Building the **Household** model itself — already completed in #2 (closed)
- **Leaving / removing a member from a household** (there is no remove-from-household action anywhere yet) — no dedicated issue; noted for a follow-up if product wants it
- **Members (non-admins) viewing the household member roster or the household settings** — this issue restricts member/settings pages to admins; letting regular members read the roster is an un-filed follow-up if product wants it
- **Household configuration beyond renaming the household name** — the only configurable `Household` field is `name`; invite-code regeneration is already covered by #13 (admin/Admin action) and the code itself is `editable=False`. Any future settings (local timezone, icon, member removal) are separate un-filed follow-ups
- **Role-based gating inside Django Admin** — Django Admin is staff-only by its own auth layer; this issue only gates the application routes, not `/admin/`
- **Role badges / avatar / visual polish** for the member list — that styling belongs to the shared design-system work #18

Constraints:
- Files (primary): `households/models.py` (add `role` field), `households/admin.py` (list display), `households/views.py` (role assignment in the existing create/join branches + new member-management and settings views), `households/urls.py` (new routes), new templates under `households/templates/households/` extending `accounts/base.html`, `tests/test_household.py`
- Reuse the existing `@login_required` + household-resolution pattern from `chores/views.py` (`_household_or_redirect_decorator` / `_current_household`) so foreign-household access is `HTTP 404` and no-household users are redirected to `/onboarding`; do not reinvent it
- Add a small role-helper (e.g. `_is_admin(membership)` or a `HouseholdMember.is_admin` / `HouseholdMember.role` check) as the single source of truth for "is this user an admin of this household" used by both the views and the templates
- URL style: flat `path(...)`, no namespacing, matching `households/urls.py` and `chores/urls.py`:
  - `path("households/members/", views.household_members, name="household_members")`
  - `path("households/members/<int:pk>/promote/", views.member_promote, name="member_promote")`
  - `path("households/members/<int:pk>/demote/", views.member_demote, name="member_demote")`
  - `path("households/settings/", views.household_settings, name="household_settings")`
- The `role` field must use Django's `choices` (not a free-text field) with values exactly `admin` and `member`, default `"member"`; generate and apply a migration
- Enforce the last-admin rule server-side (in the `demote` view), not just by hiding the button, so it holds even on a direct POST
- Do NOT modify `accounts/base.html` (owned by #18); new templates extend it only
- Follow `_docs/AGENTS.md` (add dependencies only after asking) and `_docs/testing-guidelines.md` before writing tests

## 12. System Notifications for Late Tasks

Goal: Users receive in-app notifications when a chore they are assigned to becomes overdue, plus a working (minimal, page-local) unread-notifications dropdown in the site header so they can see and dismiss the late-task alerts.

Acceptance criteria:

Model (`notifications` app, `notifications/models.py`):
- [ ] A `Notification` model exists with exactly these fields:
  - `title` (`CharField`, `max_length=255`, required)
  - `body` (`TextField`, `blank=True`)
  - `recipient` (FK to `AUTH_USER_MODEL`, `on_delete=CASCADE`, `related_name="notifications"`)
  - `chore` (FK to `"chores.Chore"` via a **string reference**, `on_delete=CASCADE`, `null=True`, `blank=True`, `related_name="notifications"`)
  - `is_read` (`BooleanField`, `default=False`)
  - `created_at` (`DateTimeField`, `auto_now_add=True`, set automatically on creation, non-editable)
- [ ] The model declares `class Meta: unique_together = ("recipient", "chore")` — this is the idempotency guarantee: a unique (recipient, chore) pair means at most one notification per assignee per chore
- [ ] The `notifications` app is in `INSTALLED_APPS` in `app/settings.py`
- [ ] A migration for the `notifications` app is generated (engineer runs `makemigrations notifications` and applies it)

Overdue check (a **management command**, chosen over a signal because it is deterministic and directly testable):
- [ ] A management command `notify_overdue` exists at `notifications/management/commands/notify_overdue.py`
- [ ] The command iterates overdue AND assigned chores via `Chore.objects.filter(due_date__lt=today, assigned_to__isnull=False).exclude(status="done")` where `today = timezone.localdate()` — uses the shared overdue definition (due before today AND status != "done")
- [ ] For each such chore it creates one `Notification` to `assigned_to` using `get_or_create(recipient=..., chore=chore, defaults={...})`, so `created_at` plus the `unique_together` guarantee idempotency
- [ ] Re-running the command does NOT create a second notification for an already-notified (chore, recipient) pair (verified by the unique constraint + `get_or_create`)

Header dropdown (minimal, page-local, does NOT build the #18 design system):
- [ ] A context processor `notifications` (registered in `TEMPLATES` `OPTIONS.context_processors` in `app/settings.py`) adds to every authenticated page: `unread_notifications` (the current user's unread notifications, newest first, limited to the 5 most recent) and `unread_count` (the count of the user's unread notifications). Anonymous users get `unread_notifications=[]` and `unread_count=0`.
- [ ] `accounts/base.html` is modified to render a small header containing the unread-count bell and an Alpine-toggled dropdown listing `unread_notifications` (title + created date + a per-item "Mark read" form). This header element is REQUIRED by this issue, so editing `accounts/base.html` for this header is **in-scope here** and supersedes the prior "do not touch base.html" notes from #8/#9/#10/#11 — but ONLY this header addition; nothing else in base.html is changed.
- [ ] Alpine.js for the dropdown is loaded **page-locally within `accounts/base.html`** via a single CDN `<script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>` inside the base template (mirroring how #8/#10 load HTMX per-page). Deliberately minimal and self-contained; the full shared design system/library setup remains #18.
- [ ] The dropdown is hidden by default and toggled by Alpine `x-data`/`x-show` attributes on the bell; an unread count of 0 still renders ("0" / "No new notifications")

Mark as read (POST endpoints, scoped to the current user only):
- [ ] `POST /notifications/<int:pk>/read/` (URL name `notification_read`) marks that single notification `is_read=True`; idempotent (re-marking an already-read one is a `HTTP 200` no-op), scoped so a notification belonging to another user returns `HTTP 404`, and anonymous -> `/login`
- [ ] `POST /notifications/read-all/` (URL name `notification_read_all`) marks ALL of the current user's unread notifications read; idempotent; anonymous -> `/login`
- [ ] Each read endpoint returns `HTTP 200` with an empty body (HTMX-style partial response, no redirect), so the header dropdown can swap out the item/empty the unread list without a full page reload

Tests (`tests/test_notifications.py`, existing `TestCase`/`Client` conventions in `tests/test_chores.py`; dates via `date`/`timedelta` or `mock.patch("django.utils.timezone.localdate", return_value=...)`):
- [ ] Creating an overdue chore assigned to a user and running the command (`call_command("notify_overdue")`) creates exactly one `Notification` to that user
- [ ] Re-running the command creates no additional notification (idempotent — count stays at 1)
- [ ] A `done` chore (even with a past due date and an `assigned_to`) creates NO notification
- [ ] A chore due today (not yet overdue) creates NO notification
- [ ] An unassigned chore (whatever its due date) creates NO notification
- [ ] An authenticated page renders the header with the user's unread notification count and the unread title(s); a read notification does not appear as unread
- [ ] `POST notification_read` on the user's own notification sets `is_read=True` (200); a second POST stays 200 and does not error (idempotent)
- [ ] `POST notification_read` on a notification whose `recipient` is another user returns `HTTP 404` and does not mutate it
- [ ] `POST notification_read` / `notification_read_all` as an anonymous user redirects to `/login`
- [ ] `POST notification_read_all` marks all of the user's unread notifications read and returns 200

Out of scope:
- Email/push delivery of these notifications — issue #17 (builds on the `Notification` model created here)
- Notification preferences / settings (which chores trigger, frequency, disable) — not filed; noted for a follow-up if product wants it
- The full design system / shared HTMX + Alpine + Bootstrap base-template setup — issue #18. This issue only adds the minimal page-local Alpine dropdown; the polish, styling, and shared library wiring are #18's job.

Constraints:
- Live in a new `notifications` Django app (`notifications/`), added to `INSTALLED_APPS`
- **Idempotency mechanism (decided):** a nullable `chore` FK on `Notification` referenced as a **string** `"chores.Chore"` (avoiding an app-isolation import from the chores app) plus `unique_together = ("recipient", "chore")`; the command uses `get_or_create` keyed on `(recipient, chore)`. The unique constraint is the authoritative guarantee that already-notified chores are not re-notified, and `get_or_create` makes re-runs no-ops.
- **Overdue definition (reuse #9/#11):** `due_date < today AND status != "done"`. The command's queryset must explicitly exclude done chores — `Chore.objects.filter(due_date__lt=today, assigned_to__isnull=False).exclude(status="done")` — and `due_date` must not be null. `today = timezone.localdate()`.
- **Header/base.html (decided):** editing `accounts/base.html` to add the notifications header/dropdown is IN SCOPE for this issue (the header is a required deliverable) and supersedes the "do not touch base.html" note from #8/#9/#10/#11 for this header addition. Keep the change to a small, self-contained header block inside the `body` (after the messages block, before `{% block content %}`). Do NOT restyle/rework base.html beyond this header.
- **Context processor (decided):** put the notification data in the header via a context processor `notifications`, because base.html (and therefore every page) is shared — this is the clean way to give every authenticated page the unread count/list. Register it in `TEMPLATES` `OPTIONS.context_processors`.
- **Files to touch:** `notifications/models.py`, `notifications/migrations/0001_initial.py` (generated), `notifications/management/commands/notify_overdue.py` (+ `__init__.py` files), `notifications/views.py`, `notifications/urls.py` (wired from `app/urls.py`), `notifications/context_processors.py`, `notifications/apps.py`, `notifications/__init__.py`, `accounts/base.html` (header/dropdown only), `app/settings.py` (INSTALLED_APPS + context processor), `tests/test_notifications.py`
- **URLs (flat, matching existing style, no namespacing), wired from `app/urls.py` via `include('notifications.urls')`:**
  - `path("notifications/<int:pk>/read/", views.notification_read, name="notification_read")`
  - `path("notifications/read-all/", views.notification_read_all, name="notification_read_all")`
- **Read endpoints are `@login_required`** and use `get_object_or_404(Notification, pk=pk, recipient=request.user)` so a foreign notification is `HTTP 404`. They do NOT require a household (a user can have in-app notifications independent of household membership), so do NOT use the chore `_household_or_redirect_decorator`.
- **Alpine (decided):** a single CDN script tag for Alpine loaded inside `accounts/base.html`'s body (page-local, mirroring the per-page HTMX approach). Toggle-only (`x-data`, `x-show`) and self-contained. Full Alpine/shared setup is #18.
- **`created_at` is `auto_now_add=True`** (set automatically on creation, `editable=False`). There is no separate "notified date" field — the unique (recipient, chore) pair is the entire idempotency record.
- Use Django function views and Django templates as in the other apps. Follow `_docs/testing-guidelines.md` before writing tests. Follow `_docs/AGENTS.md`; do not add Python dependencies without asking (Alpine is a runtime CDN `<script>`, no package).

## 15. Password Reset

Goal: A user who has forgotten their password can request a reset link, receive a tokenized email, and set a new password through Django's built-in password-reset flow.

Acceptance criteria:
- [ ] A "Forgot your password?" link is visible on the `/login` page and navigates to `/password-reset/`
- [ ] `GET /password-reset/` renders a form asking for an email address
- [ ] `POST /password-reset/` with a registered email address sends a password-reset email and redirects to `/password-reset/done/`
- [ ] `GET /password-reset/done/` shows a message telling the user to check their email
- [ ] The password-reset email appears in the console output (dev email backend)
- [ ] The email contains a clickable link with a valid token that leads to `/password-reset/<uidb64>/<token>/`
- [ ] `GET /password-reset/<uidb64>/<token>/` renders a form with "New password" and "Confirm password" fields
- [ ] `POST /password-reset/<uidb64>/<token>/` with a valid new password sets the user's password and redirects to `/password-reset/complete/`
- [ ] `GET /password-reset/complete/` shows a success message with a link to the login page
- [ ] The user can log in with the new password at `/login`
- [ ] The old password no longer works (rejected at `/login`)
- [ ] Requesting a reset for a non-existent email address still shows the "check your email" message (no user-enumeration leak)
- [ ] An expired or invalid token shows an error on the reset form (the user is not silently logged in or shown a misleading success)
- [ ] The `EMAIL_BACKEND` setting in `app/settings.py` is wired to `django.core.mail.backends.console.EmailBackend` so the console email backend actually works in dev
- [ ] A test posts a valid email to `/password-reset/`, follows the console email to extract the reset link, and asserts the user can set a new password and log in with it
- [ ] A test requests a reset for a non-existent email and asserts the response is the same "check your email" page (no different response that reveals whether the email exists)

Out of scope:
- User registration — issue #3
- Login/logout — issue #4
- Customizing the email template beyond Django's default (e.g. branded HTML email) — follow-up if product wants it
- Deploying a real SMTP/SendGrid email backend — dev console backend only
- Rate limiting password-reset requests — follow-up if product wants it

Constraints:
- Use Django's bundled password-reset views (`PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, `PasswordResetCompleteView`) — do not write custom views
- URLs live in `accounts/urls.py`, wired from `app/urls.py` via the existing `include('accounts.urls')`
- Templates live in `accounts/templates/accounts/` and extend `accounts/base.html`
- The console email backend must be configured via the standard `EMAIL_BACKEND` setting in `app/settings.py` (the existing `MAILERS` dict does not activate it)
- `LOGIN_URL = 'login'` is already set; password-reset URLs should not conflict
- Django's default token expiry (24 hours) is acceptable — no customisation needed
- Follow `_docs/AGENTS.md`; do not add dependencies without asking

## 16. Calendar: Month Navigation

Goal: Users can navigate between months in the calendar view to view chores by due date in any month, not just the current one.

Acceptance criteria:

- [ ] `GET /chores/calendar/` (no query params) defaults to the current month (same behavior as today, no regression)
- [ ] `GET /chores/calendar/?year=2026&month=10` renders the calendar grid for October 2026
- [ ] `GET /chores/calendar/?year=2026&month=0` falls back to the current month (invalid month value)
- [ ] `GET /chores/calendar/?year=2026&month=13` falls back to the current month (out-of-range month value)
- [ ] `GET /chores/calendar/?month=2026-10` falls back to the current month (missing `year` param)
- [ ] The page shows the month name and year for the displayed month (e.g. "October 2026") — always matches the grid, never the current month when a different month is requested
- [ ] A "Previous" link is rendered that navigates to the month before the displayed month (e.g. when viewing September 2026, Previous links to `/chores/calendar/?year=2026&month=8`)
- [ ] A "Next" link is rendered that navigates to the month after the displayed month (e.g. when viewing September 2026, Next links to `/chores/calendar/?year=2026&month=10`)
- [ ] When viewing January of any year, the "Previous" link goes to December of the previous year (e.g. `/chores/calendar/?year=2025&month=12`)
- [ ] When viewing December of any year, the "Next" link goes to January of the next year (e.g. `/chores/calendar/?year=2027&month=1`)
- [ ] The year and month values in navigation links are always valid integers (no month=0 or month=13 in any generated link)
- [ ] Chores from the requested month are shown; chores from other months are not (same query scoping rule as #9, just pointed at a different year/month)
- [ ] "Today" is still computed as `timezone.localdate()` regardless of which month is displayed, so color coding rules (`calendar-overdue`, `calendar-due-soon`, `calendar-on-time`) are correct even when viewing a past or future month
- [ ] A chore with `due_date` in the displayed month appears in the correct grid cell with the correct color class, same as #9
- [ ] A chore with no `due_date` is not shown in any cell
- [ ] Foreign-household chores are never shown, regardless of which month is viewed
- [ ] Anonymous access to `/chores/calendar/` (with or without query params) redirects to `/login`
- [ ] A logged-in user with no `HouseholdMember` is redirected to `/onboarding`
- [ ] A test GETs the calendar without params and asserts it shows the current month (baseline regression)
- [ ] A test GETs `?year=2026&month=10` with a chore due in October 2026 and asserts the chore is shown and the month label reads "October 2026"
- [ ] A test GETs `?year=2026&month=10` with a chore due in September 2026 and asserts the chore is NOT shown
- [ ] A test asserts the "Previous" link contains `year=2026&month=9` when viewing October 2026
- [ ] A test asserts the "Next" link contains `year=2026&month=11` when viewing October 2026
- [ ] A test asserts January's "Previous" link goes to `year=<prev>&month=12` and December's "Next" link goes to `year=<next>&month=1`
- [ ] A test with invalid params (month=0, month=13, missing year) asserts the response falls back to the current month's grid (status 200, current month label)
- [ ] A test asserts anonymous access redirects to `/login` and a user without a household is redirected to `/onboarding`

Out of scope:
- Base month-grid rendering — issue #9 (this issue reuses the existing grid)
- Color-coding / late indicators — issue #9 and #11 (rules are reused, not changed)
- Multi-month "jump to" picker or date-range views — not filed; follow-up if product wants it
- HTMX / Alpine.js / Bootstrap styling — issue #18
- Any changes to `accounts/base.html` — owned by #18

Constraints:
- Files: `chores/views.py`, `chores/templates/chores/calendar.html`, `chores/urls.py` (no new routes, query-param-driven on the existing route), `tests/test_chores.py`
- The existing URL pattern `path("chores/calendar/", views.chore_calendar, name="chore_calendar")` is reused; navigation is driven by `?year=YYYY&month=M` query parameters on the same route
- Parse `year` and `month` from `request.GET` using `.get()` with `int()` conversion and try/except; validate: month must be 1–12, year must be a positive integer; clamp or fall back to `today.year, today.month` on invalid input
- The `chore_calendar` view reads `year` and `month` from validated query params instead of hardcoding `today.year, today.month`
- "Today" (`timezone.localdate()`) is still computed in the view for color coding; the displayed month/year comes from validated query params
- `calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)` generates the grid weeks for the requested month (already used in #9)
- The queryset filter stays `Chore.objects.filter(household=request.household, due_date__isnull=False, due_date__year=year, due_date__month=month)` where `year`/`month` come from validated query params
- The template is modified to add Previous/Next navigation links above or below the month label, using `{% url 'chore_calendar' %}?year=...&month=...`
- Month navigation links must never point to month=0 or month=13 — the view computes previous/next month boundaries correctly across year boundaries (Jan → Dec prev year, Dec → Jan next year)
- Date clamping: out-of-range or missing params fall back to current month silently (no error page, no 400)
- Color coding (`chore_color_class` helper) is unchanged — the `today` passed to the helper is always `timezone.localdate()`, not the displayed month, so overdue/due-soon rules are correct for past and future months
- The template still extends `accounts/base.html` and the `content` block; do NOT modify `accounts/base.html`
- Follow `_docs/AGENTS.md`; add dependencies (if any) only after asking
- Follow `_docs/testing-guidelines.md` before writing tests

## 17. Email & Push Notifications

Goal: When the `notify_overdue` management command creates new in-app notifications for overdue chores, the affected users also receive a digest email listing their newly-notified overdue chores, so they are alerted even when not logged into the app.

Acceptance criteria:

Email template and sending:
- [ ] An email template exists at `notifications/templates/notifications/overdue_digest.txt` (plain text)
- [ ] The template renders a list of each overdue chore's title and due date for the recipient
- [ ] The email subject contains the count of overdue chores (e.g. "You have 2 overdue chore(s)")
- [ ] The email is sent via `django.core.mail.send_mail()`, which respects the existing `EMAIL_BACKEND` setting (console in dev)
- [ ] The email from address uses Django's `DEFAULT_FROM_EMAIL` setting

Command behavior (`notifications/management/commands/notify_overdue.py`):
- [ ] The command collects all newly-created notifications during its run (where `get_or_create` returned `created=True`)
- [ ] After processing all overdue chores, the command groups new notifications by recipient and sends one digest email per recipient who has at least one new notification
- [ ] A user with two overdue chores receives one email listing both, not two separate emails
- [ ] Two different users each receive their own email
- [ ] A chore that already had a notification from a previous run does NOT trigger a new email
- [ ] Re-running the command does not send duplicate emails for the same (recipient, chore) pair
- [ ] The command's stdout still reports the total number of overdue chores notified

Edge cases:
- [ ] If a user has no email address, no email is sent but in-app notification is still created
- [ ] If a user's account is inactive, no email is sent but in-app notification is still created
- [ ] If send_mail() raises an exception, the error is logged and the command continues
- [ ] A chore that becomes done between overdue query and email sending still had a valid notification created

Tests:
- [ ] Test: overdue chore → 1 email with correct recipient, subject, body
- [ ] Test: 2 overdue chores same user → 1 digest email listing both
- [ ] Test: 2 users → 2 separate emails
- [ ] Test: user with no email → no email, in-app notification created
- [ ] Test: inactive user → no email, in-app notification created
- [ ] Test: idempotent — second run sends no new email
- [ ] Test: send_mail exception → command completes, notification still in DB

Out of scope:
- Push notifications — future follow-up
- Notification preferences/settings — follow-up
- HTML email templates — plain text only
- Links to chore detail pages — follow-up
- Notification model, overdue check, in-app UI — issue #12
- Real SMTP backend — dev console only

Constraints:
- Files: `notifications/management/commands/notify_overdue.py`, `notifications/templates/notifications/overdue_digest.txt` (new), `tests/test_notifications.py`
- Use `django.core.mail.send_mail()`
- Use Django template engine for email body
- Deduplication via `unique_together` + `get_or_create` from #12
- Wrap `send_mail` in try/except, log via `self.stderr`
- Skip users with empty email or inactive accounts
- Use Django test `mail.outbox`
- Follow `_docs/AGENTS.md`

## 18. Frontend Dependencies: HTMX, Alpine.js & Bootstrap

Goal: All three frontend libraries (HTMX, Alpine.js, Bootstrap) are loaded once in `accounts/base.html` so every template inherits them; page-local CDN script tags from issues #8 and #10 are removed as redundant.

Acceptance criteria:
- [ ] `accounts/base.html` includes CDN script tag for HTMX (`https://unpkg.com/htmx.org@1.9.12`) making HTMX available on every page
- [ ] `accounts/base.html` includes CDN script tag for Alpine.js (`https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js` with `defer`) — verify it remains and is not duplicated
- [ ] `accounts/base.html` includes CDN link tag for Bootstrap CSS (`https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css` or latest v5 stable) in `<head>`
- [ ] Page-local HTMX script tag removed from `chores/templates/chores/chore_market.html`
- [ ] Page-local HTMX script tag removed from `chores/templates/chores/chore_detail.html`
- [ ] After removing page-local scripts, HTMX features (chore claim, mark-done) still work
- [ ] Alpine.js notifications dropdown continues to work
- [ ] `[x-cloak]` style rule remains in `base.html`
- [ ] No duplicate script tags for HTMX or Alpine on any page
- [ ] Templates extending `base.html` inherit all three libraries

Out of scope:
- Full design system — separate follow-up
- Specific features using HTMX/Alpine/Bootstrap — belong to their respective issues
- Migrating Bootstrap markup into templates — follow-up
- Vendoring libraries locally — CDN is acceptable
- Adding Python packages — CDN loads only

Constraints:
- Files: `accounts/templates/accounts/base.html`, `chores/templates/chores/chore_market.html`, `chores/templates/chores/chore_detail.html`
- CDN only, no new Python packages
- HTMX pinned to 1.9.12
- Bootstrap CSS only (no JS bundle unless needed)
- No other template/view/URL/Python changes
- Follow `_docs/AGENTS.md`

## 19. Overdue Indicator on Chore Detail Page

Goal: The single-chore detail page (`GET /chores/<pk>/`) shows the overdue indicator (`calendar-overdue` CSS class) when the chore is overdue, matching the same rule used by the chore list, market, and calendar views.

Acceptance criteria:
- [ ] The `chore_detail.html` template loads the `chore_tags` template tag library
- [ ] The `<h1>` element (or top-level page element) carries the CSS class returned by `{{ chore|chore_color }}` — no overdue logic is duplicated in the template or view
- [ ] A chore with `due_date` before today and `status` = `open` or `in_progress` renders with `calendar-overdue` on the detail page
- [ ] A chore with `due_date` before today and `status` = `done` does NOT render with `calendar-overdue` (done overrides overdue)
- [ ] A chore with `due_date` equal to today does NOT render with `calendar-overdue` (due today is not overdue)
- [ ] A chore with `due_date` in the future does NOT render with `calendar-overdue`
- [ ] A chore with `due_date = None` does NOT render with `calendar-overdue`
- [ ] No view or URL changes are needed — the `chore_detail` view already passes the `chore` object to the template
- [ ] `accounts/base.html` is not modified
- [ ] A test creates an overdue chore (due_date in the past, status = `open`), GETs its detail page, and asserts the rendered HTML contains `calendar-overdue`
- [ ] A test creates an overdue chore with `status` = `done`, GETs its detail page, and asserts the rendered HTML does NOT contain `calendar-overdue`
- [ ] A test creates a chore due today, GETs its detail page, and asserts the rendered HTML does NOT contain `calendar-overdue`

Out of scope:
- The shared `chore_color_class` helper and its unit tests — owned by #9
- Overdue highlighting on the chore list and market pages — issue #11
- CSS rules that make `calendar-overdue` visually red — issue #18
- Any changes to `accounts/base.html` — owned by #18

Constraints:
- Files: `chores/templates/chores/chore_detail.html`, `tests/test_chores.py` — minimal surface area
- Reuse the existing `chore_color` template filter from `chores/templatetags/chore_tags.py` (which calls `chore_color_class` from `chores/utils.py`); do NOT re-implement the color/overdue decision
- The `chore_detail` view in `chores/views.py` already passes the `chore` object to the template — no view changes needed
- Apply the class to an existing element (e.g. `<h1>`) rather than adding a wrapper div, to keep the change minimal
- No new URL patterns, no new views, no new template tags
- Follow `_docs/testing-guidelines.md` before writing tests; follow `_docs/AGENTS.md`; do not add dependencies without asking

## 20. UI: Navigation Bar in base template

Goal: Add a Bootstrap navbar to the shared base template so users can navigate between all pages.

Acceptance criteria:
- A Bootstrap `<nav class="navbar ...">` in `accounts/base.html` inside `<body>` before content
- Navbar brand/link pointing to home
- Authenticated: Chores, Market, Calendar, Logout links
- Authenticated admin additionally: Members, Settings links
- Anonymous: Register, Login links
- Admin-only links only shown for admins
- Alpine notifications dropdown preserved and functional
- `[x-cloak]` style rule remains
- HTMX and Alpine scripts exactly once each
- Navbar renders without error on all pages (login, register, onboarding, chores list, market, calendar, members, settings, home)

Out of scope:
- Restyling individual page content — separate follow-up
- Custom home page — issue #21
- Any new Python dependency

Constraints:
- Modify only `accounts/templates/accounts/base.html`
- Use Bootstrap 5.3.3 CDN classes (no new packages)
- Named URL references via `{% url '...' }`
- Determine admin via existing HouseholdMember / is_admin
- Preserve notification dropdown markup and HTMX/Alpine behavior
- Run `uv run pytest`, all pass

## 21. UI: Home page template

Goal: Replace the plain-text home page with a real rendered template.

Acceptance criteria:
- GET / renders a template (app/templates/app/home.html) instead of plain HttpResponse
- Extends accounts/base.html and sets a title block
- Anonymous: tagline + Register/Login links
- Authenticated non-member: prompt/link to onboarding
- Authenticated member: welcome (household name if available) + quick links to Chores, Market, Calendar
- Authenticated admin: additionally Members, Settings quick links
- Navbar from #20 shows on home page
- uv run pytest passes

Out of scope:
- Restyling other pages — separate follow-up
- Any new Python dependency

Constraints:
- Modify app/views.py (home) and add app/templates/app/home.html
- Extend accounts/base.html; do not modify it
- Determine membership/admin via HouseholdMember / is_admin
- Keep view name home and URL name home
- Reuse Bootstrap CDN classes
- Run uv run pytest, all pass

## 22. UI: Bootstrap styling across templates

Goal: Apply Bootstrap 5.3.3 classes across templates so forms, buttons, lists, messages, tables, and cards look like a real UI.

Acceptance criteria:
- Messages in base.html render as Bootstrap alerts
- Chore forms (chore_form.html) render fields with form-control styling and btn btn-primary submit
- Login/Register/password-reset forms render with Bootstrap styling and btn; Login/Register in a card
- Onboarding create/join forms styled with primary buttons
- Chore list as a list group/cards with status; keeper chore_color class
- Chore market claim buttons styled Bootstrap; HTMX preserved
- Chore detail status/due badges; Mark Done/Edit/Delete as Bootstrap buttons; HTMX preserved
- Chore delete confirmation uses danger styling
- Calendar uses Bootstrap table, color-coded cells intact
- Members page styled rows/cards with Bootstrap buttons
- Settings page styled layout with invite code
- uv run pytest passes

Out of scope:
- Changing view/URL/business logic
- Nav bar (#20) and home (#21)
- New Python dependency (crispy-forms)

Constraints:
- Preserve HTMX attributes on claim/done buttons exactly
- Preserve chore_color class everywhere it exists (list, market, detail, calendar)
- Keep named URL references unchanged
- Reuse Bootstrap CDN; no new packages
- Run uv run pytest, all pass
