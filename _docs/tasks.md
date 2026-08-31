# Backlog

## 1. Project Setup with Passing Test
Goal: Have a runnable Django project with one passing test.
Description: Initialize the Django project skeleton (manage.py, settings, URLs, wsgi) inside the repository. Add a pytest or Django TestCase that verifies the home view returns HTTP 200. Commit all scaffolding so the project runs with `python manage.py runserver` and `pytest` passes green.

## 2. Household Model & Admin Registration
Goal: Persist a household and manage it via Django Admin.
Description: Create a Django model for `Household` with fields like name, invite_code, and created_at. Register it in Django Admin so records can be viewed and edited. Write a test that creates a household through the ORM and verifies it exists in the database.

## 3. User Registration
Goal: Let a new user sign up with username, email, and password.
Description: Build a registration form using Django's `UserCreationForm` or a custom form. Create a `/register` view and template. Write a test that posts valid registration data and asserts the user is created and logged in.

## 4. User Login & Logout
Goal: Authenticate users with username and password.
Description: Wire up Django's `LoginView` and `LogoutView` with templates. Create a login page at `/login` and a logout confirmation or redirect. Write tests that verify a registered user can log in, that invalid credentials are rejected, and that logout works.

## 5. Onboarding Flow — Create or Join Household
Goal: New users choose to create or join a household after registration.
Description: After a successful registration, redirect to an onboarding page that presents two options: "Create a New Household" (prompts for a name) or "Join via Invite Code" (prompts for a code). Create the corresponding views and templates. Write a test that follows the onboarding flow and verifies the user ends up linked to a household.

## 6. Invite Code Generation
Goal: Each household gets a unique, shareable invite code.
Description: When a household is created, auto-generate a short, human-readable invite code (e.g., `HOME-7X9B`). Write a test that creates a household and asserts the invite code is present and unique. Optionally add a "regenerate code" action in the Admin.

## 7. Chore Model & CRUD
Goal: Create, read, update, and delete chores within a household.
Description: Define a `Chore` model with fields such as title, description, assigned_to (nullable), due_date, status (open/in_progress/done), and a foreign key to Household. Build list, create, edit, and delete views with Django templates. Write tests for each CRUD operation.

## 8. Chore Market — Browse & Claim Tasks
Goal: Users pick unassigned chores from a shared pool.
Description: Create a "Chore Market" page that lists all open, unassigned chores for the user's household. Add a "Claim" button (HTMX) that assigns the chore to the current user and updates the status to in_progress. Write a test that verifies a user can claim a chore and see it move out of the market list.

## 9. Calendar View with Deadlines
Goal: Users see their assigned chores on a calendar.
Description: Build a calendar page that displays chores by due date using a simple month-grid. Each cell shows chores due that day, color-coded (green = on time, yellow = due soon, red = overdue). Write a test that creates chores with various due dates and asserts the calendar renders them correctly.

## 10. Task Completion (Honor System)
Goal: Users mark their claimed chores as done.
Description: Add a "Mark Done" button on the chore detail or list page (HTMX). When clicked, update the status to done and record a completed_at timestamp. Write a test that verifies clicking "Done" changes the chore status and removes it from the active calendar.

## 11. Late Task Indicators
Goal: Overdue chores are visually highlighted.
Description: In the calendar view and chore list, apply a red CSS class to any chore whose due_date is in the past and status is not done. Write a test that creates an overdue chore and asserts the expected CSS class or indicator is present in the rendered HTML.

## 12. System Notifications for Late Tasks
Goal: Users receive in-app notifications when a chore becomes overdue.
Description: Create a `Notification` model (title, body, recipient, is_read, created_at). Add a periodic check or signal that creates a notification when a chore passes its due date without being completed. Display unread notifications in a dropdown in the site header. Write a test that creates an overdue chore and asserts a notification is generated.
