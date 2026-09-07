# Backlog

## Task 1: Project Setup & Database Models Configuration

- **Status**: To Do
- **Priority**: High
- **Description**: Initialize the project environment, create the main app module, configure database settings, and define core models (`User`, `Chore`, `ChoreSubmission`, and `PointLedger`).
- **Acceptance Criteria**:
  - Application structure initialized and running.
  - Database schema defined with proper relationships and constraints.
  - Initial database migrations created and applied successfully.

---

## Task 2: User Profiles & Seed Data Setup

- **Status**: To Do
- **Priority**: High
- **Description**: Set up user management for Parent and Child roles, including admin registration and a seed script for default household profiles.
- **Acceptance Criteria**:
  - Parent (Admin) and Child (Member) roles configured.
  - Seed script successfully populates test accounts.

---

## Task 3: Chore Management & Scheduling API

- **Status**: To Do
- **Priority**: Medium
- **Description**: Build views/endpoints to create, update, list, and soft-delete daily, weekly, and one-off chores.
- **Acceptance Criteria**:
  - Parent can create chores with title, description, recurrence cadence, and point values.
  - Children can fetch list of available assigned tasks.

---

## Task 4: Chore Submission & Parent Approval Engine

- **Status**: To Do
- **Priority**: High
- **Description**: Implement task completion flow (`Pending Approval` status) and parent approval/rejection logic.
- **Acceptance Criteria**:
  - Child submitting a task sets status to `PENDING_APPROVAL` without instantly awarding points.
  - Parent approving a task atomically adds points to child balance and writes entry to `PointLedger`.
  - Rejection allows task to be re-attempted.

---

## Task 5: Household Scoreboard & Responsive Frontend Views

- **Status**: To Do
- **Priority**: Medium
- **Description**: Develop mobile-responsive web templates for Parent Dashboard, Child Portal, and Scoreboard leaderboard.
- **Acceptance Criteria**:
  - Child can mark tasks complete with single tap.
  - Scoreboard displays real-time point totals and activity feed.

---

## Task 6: Integration Testing & Test Automation

- **Status**: To Do
- **Priority**: Medium
- **Description**: Write test cases for user creation, chore submission state transitions, and atomic point ledger transactions.
- **Acceptance Criteria**:
  - Automated test suite passes successfully.
  - Prevents duplicate point credits on repeated approvals.
