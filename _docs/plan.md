# Project Plan: Shared Household Chores Manager (MVP)

## 1. Project Scope
*   **Target Audience:** Adults only (focus on clarity, fairness, and accountability).
*   **Task Assignment:** Manual ("Chore Market" — users pick tasks from a shared pool).
*   **Motivation & Tracking:** Calendar and hard deadlines (no points, karma, or gamification).
*   **Task Verification:** Honor system (users click "Done", tasks close immediately without approval).
*   **Task Generation:** Fully manual (no automatic recurring or scheduled tasks).
*   **Late Tasks:** Visual indicator only (highlighted in red) + system notifications.

## 2. Technology Stack
*   **Backend:** Django (Python) — utilizing built-in Admin panel and Auth system.
*   **Frontend Logic:** Django Templates + HTMX (for dynamic, SPA-like AJAX updates without page reloads) + Alpine.js (for lightweight client-side interactivity: dropdowns, modals, tooltips).
*   **Frontend Styling:** Bootstrap (for fast, responsive, and clean layout/grid system).
*   **Database:** SQLite (zero configuration, database stored in a single file for rapid development).

## 3. Household & Authentication Flow
*   **Auth Type:** Classical Username/Password login using Django's built-in forms.
*   **Onboarding (Fork Screen):** Right after registration, users must choose to either:
    1. "Create a New Household" (becomes the Admin).
    2. "Join via Invite Code" (enters code to join an existing house).
*   **Invitations:** Unique, short invite codes generated per household (e.g., `HOME-7X9B`).
*   **Roles:** The creator is the Household Admin. Admins can promote other roommates to become Admins too.
