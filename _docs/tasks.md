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

Goal: Each household gets a unique, shareable, human-readable invite code.

Acceptance criteria:
- [ ] An invite code is auto-generated whenever a household is created
- [ ] The code matches a short format such as `HOME-7X9B` (uppercase letters/digits)
- [ ] The code is non-empty and present for every household
- [ ] Two different households never share the same code (collisions regenerated)
- [ ] The code is visible in Django Admin for the household
- [ ] A test creates households and asserts the code is present and unique

Out of scope:
- Regenerating an existing code from Admin — issue #13
- Onboarding/join flow using the code — issue #5
- Sharing UI beyond displaying the code

Constraints:
- Generate on model `save()` or via a signal in the `households` app
- Use Django unique constraints on the `invite_code` field

## 7. Chore Model & CRUD

Goal: Create, read, update, and delete chores within a household.

Acceptance criteria:
- [ ] A `Chore` model exists: `title` (required), `description` (optional), `assigned_to` (nullable user), `due_date` (nullable), `status` (open/in_progress/done), `household` FK, `created_at`
- [ ] A page lists chores for the current user's household
- [ ] Views exist to create, edit, and delete a chore
- [ ] Deleting requires a confirmation step
- [ ] A user can only see and modify chores belonging to their own household
- [ ] Tests cover create, read, update, and delete operations

Out of scope:
- Claiming/unassigned-chore market — issue #8
- Marking a chore done — issue #10
- Calendar view — issue #9

Constraints:
- Live in a `chores` Django app
- All querysets scoped to the current user's household
- Use Django template views with the household guard

## 8. Chore Market — Browse & Claim Tasks

Goal: Users pick unassigned chores from a shared household pool.

Acceptance criteria:
- [ ] A "Chore Market" page lists all open, unassigned chores for the current user's household
- [ ] Each listed chore has a "Claim" button
- [ ] Clicking Claim (HTMX) assigns the chore to the current user and sets status to `in_progress`
- [ ] After claiming, the chore leaves the market list
- [ ] An already-assigned chore cannot be claimed twice (race-safe)
- [ ] A user not part of the household cannot see or claim its chores
- [ ] A test verifies a user can claim a chore and that it moves out of the market list

Out of scope:
- HTMX setup in the base template — issue #18
- Marking a claimed chore done — issue #10
- Late-task notifications — issue #12

Constraints:
- Use HTMX for the claim action
- Guard against double-claim with `select_for_update` or a conditional update
- Scope to the current user's household

## 9. Calendar View with Deadlines

Goal: Users see their assigned chores on a month-grid calendar by due date.

Acceptance criteria:
- [ ] A calendar page renders a month-grid layout
- [ ] Chores are displayed in the cell matching their `due_date`
- [ ] Cells are color-coded: green = on time, yellow = due soon, red = overdue
- [ ] Only the current user's household chores are shown
- [ ] Chores due in the current (default) month are visible
- [ ] A test creates chores with various due dates and asserts the calendar renders correctly

Out of scope:
- Multi-month navigation — issue #16
- Shared late-task indicator logic — issue #11
- Notification generation — issue #12

Constraints:
- Pure Django template rendering (no external calendar library)
- Reuse a shared late-detection helper used by issue #11
- Use `django.utils.timezone` for deterministic date handling in tests

## 10. Task Completion (Honor System)

Goal: Users mark their claimed chores as done on the honor system.

Acceptance criteria:
- [ ] A "Mark Done" button appears on a claimed chore (detail or list page)
- [ ] Clicking Mark Done (HTMX) sets status to `done` and records a `completed_at` timestamp
- [ ] Done chores no longer appear in the active calendar/market views
- [ ] A user cannot mark an unclaimed chore done
- [ ] A chore already `done` cannot be marked done again
- [ ] A test verifies clicking Done changes the status and removes it from the active view

Out of scope:
- Unclaiming or reassigning a chore
- Late-task notifications — issue #12
- HTMX setup in the base template — issue #18

Constraints:
- Use HTMX for the done action
- Set `completed_at` automatically at completion (not editable)
- Guard against double-completion with a conditional update

## 11. Late Task Indicators

Goal: Overdue chores are visually highlighted in the calendar and chore list.

Acceptance criteria:
- [ ] A chore with `due_date` in the past and status not `done` receives a red CSS class or indicator
- [ ] The red highlight appears in both calendar and chore list views
- [ ] A chore due today (not yet past) is not marked overdue
- [ ] An overdue but `done` chore is not marked overdue
- [ ] A test creates an overdue chore and asserts the expected CSS class/indicator in the HTML

Out of scope:
- Generating notifications for late chores — issue #12
- Configurable overdue thresholds / strike times

Constraints:
- Reuse the shared late-detection helper from issue #9
- "overdue" = due_date before today AND status != done
- Use `django.utils.timezone` for deterministic date handling in tests

## 12. System Notifications for Late Tasks

Goal: Users receive in-app notifications when a chore becomes overdue.

Acceptance criteria:
- [ ] A `Notification` model exists: `title`, `body`, `recipient` (FK to user), `is_read`, `created_at`
- [ ] An overdue check (management command or signal) creates a notification for each user whose assigned, non-done chore passed its due date
- [ ] Exactly one notification per chore/recipient (idempotent)
- [ ] Already-notified chores are not re-notified
- [ ] Unread notifications appear in a dropdown in the site header
- [ ] Notifications can be marked as read
- [ ] A test creates an overdue chore and asserts a notification is generated

Out of scope:
- Email/push delivery — issue #17
- Notification preferences / settings
- Alpine.js setup in the header — issue #18

Constraints:
- Live in a `notifications` app
- Overdue check must be idempotent (track what has already been notified)
- Use Alpine.js for the dropdown toggle
