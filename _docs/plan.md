# Project Plan: Family Chore & Rewards Manager (MVP)

A lightweight web application for managing household chores with role-based access, chore scheduling, parent approval workflows, and a point-based reward ledger.

---

## 1. Executive Summary & Goals

- **Goal**: Enable families to track household chores, encourage completion through points, and maintain parental oversight.
- **Target Users**:
  - **Parents (Admin)**: Task creators and approvers.
  - **Children (Members)**: Task performers and point earners.
- **MVP Success Metric**: A working end-to-end flow where a parent creates a recurring chore, a child submits it, the parent approves it, and the points reflect on the child's scoreboard.

---

## 2. System Architecture & Tech Stack

```text
   ┌─────────────────────────────────────────────────────────┐
   │             Client Layer (Browser)                      │
   │  • HTML5 + Tailwind CSS (via CDN) + Vanilla JS          │
   │  • Mobile-responsive Parent & Child views               │
   └──────────────────────────┬──────────────────────────────┘
                              │ HTTP / REST
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │             Application Layer (FastAPI)                 │
   │  • Routers: /users, /chores, /completions, /scoreboard  │
   │  • Business logic: Recurrence, Approval & Points engine │
   └──────────────────────────┬──────────────────────────────┘
                              │ SQLAlchemy ORM
                              ▼
   ┌─────────────────────────────────────────────────────────┐
   │             Storage Layer (SQLite)                      │
   │  • Tables: users, chores, chore_logs, point_ledger      │
   └─────────────────────────────────────────────────────────┘
```

- **Backend**: Python 3.11+ with **FastAPI**
- **ORM & Database**: **SQLAlchemy** + **SQLite**
- **Frontend**: Server-rendered HTML / Jinja2 or lightweight static HTML + Vanilla JS + Tailwind CSS CDN
- **Testing**: `pytest` + `httpx` (FastAPI `TestClient`)

---

## 3. Data Model

### 3.1 Entities & Relationships

1. `User`
   - `id`: Integer (Primary Key)
   - `name`: String
   - `role`: Enum (`PARENT`, `CHILD`)
   - `pin`: String (Optional 4-digit PIN for parent actions)
   - `current_points`: Integer (Default: 0)

2. `Chore`
   - `id`: Integer (Primary Key)
   - `title`: String
   - `description`: Text (Optional)
   - `points`: Integer (e.g., 5, 10, 20)
   - `cadence`: Enum (`DAILY`, `WEEKLY`, `ONE_OFF`)
   - `assigned_to_user_id`: Integer (Foreign Key → `User.id`, nullable for open pool)
   - `is_active`: Boolean (Default: True)

3. `ChoreSubmission`
   - `id`: Integer (Primary Key)
   - `chore_id`: Integer (Foreign Key → `Chore.id`)
   - `user_id`: Integer (Foreign Key → `User.id`)
   - `status`: Enum (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`)
   - `submitted_at`: DateTime (Default: UTC now)
   - `reviewed_at`: DateTime (Nullable)
   - `reviewed_by_user_id`: Integer (Foreign Key → `User.id`, Nullable)
   - `notes`: Text (Optional)

4. `PointLedger`
   - `id`: Integer (Primary Key)
   - `user_id`: Integer (Foreign Key → `User.id`)
   - `chore_submission_id`: Integer (Foreign Key → `ChoreSubmission.id`, Nullable)
   - `amount`: Integer (Positive for rewards, negative for manual adjustments)
   - `reason`: String
   - `created_at`: DateTime

---

## 4. REST API Specification

| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `GET` | `/api/users` | List family members and balances | Any |
| `POST` | `/api/users` | Create a new family member | Parent |
| `GET` | `/api/chores` | List chores (filter by cadence/assigned user) | Any |
| `POST` | `/api/chores` | Create a new chore | Parent |
| `PUT` | `/api/chores/{id}` | Update chore details/points/cadence | Parent |
| `DELETE` | `/api/chores/{id}` | Soft delete / archive a chore | Parent |
| `POST` | `/api/chores/{id}/submit` | Mark a chore as completed (moves to Pending) | Child / Any |
| `GET` | `/api/submissions/pending` | List submissions awaiting parent review | Parent |
| `POST` | `/api/submissions/{id}/approve` | Approve task and credit points to child balance | Parent |
| `POST` | `/api/submissions/{id}/reject` | Reject task with optional feedback | Parent |
| `GET` | `/api/scoreboard` | Get leaderboard & transaction history | Any |

---

## 5. Implementation Milestones

```text
   ┌──────────────────────┐
   │ Phase 1: Setup & DB  │ ➔ SQLite Schema + SQLAlchemy Models + Seed Data
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │ Phase 2: Core API    │ ➔ CRUD Chores + Submission + Approval Engine
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │ Phase 3: Web UI      │ ➔ Parent Dashboard + Child Portal + Scoreboard
   └──────────┬───────────┘
              ▼
   ┌──────────────────────┐
   │ Phase 4: QA & Polish │ ➔ Pytest Suite + Edge Case Validation + Readme
   └──────────────────────┘
```

### Milestone 1: Project Setup & Data Persistence (Days 1–2)

- Initialize repo, dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `pytest`).
- Implement database models and automatic migration/init script.
- Create basic seed script with default Parent and Child profiles.

### Milestone 2: API & Business Logic Implementation (Days 3–4)

- Implement CRUD endpoints for users and chores.
- Implement chore completion submission logic (`PENDING_APPROVAL`).
- Implement parent approval/rejection transaction (atomic balance update + ledger entry).
- Write integration tests covering the approval and point crediting lifecycle.

### Milestone 3: Responsive Frontend (Days 5–6)

- **Profile Selector / Switcher**: Fast switching between Parent and Child views.
- **Child View**: Simple list of daily/weekly chores with single-tap "Mark Complete" buttons and live balance display.
- **Parent View**: Pending approvals queue with "Approve" / "Reject" actions and chore editor modal.
- **Scoreboard**: Clean card layout showing points ranking and recent activity feed.

### Milestone 4: Testing & Documentation (Day 7)

- Verify automated test coverage (`pytest`).
- Write `README.md` with startup instructions, Docker run command, and workflow walkthrough.

---

## 6. Verification & Acceptance Criteria

- **Chore Creation**: Parent can create a daily chore with title "Make Bed" worth 10 points.
- **Submission**: Child can view "Make Bed" and click "Submit for Review".
- **State Isolation**: Submitting a chore does **not** increase the child's balance immediately.
- **Parent Review**: Chore appears in the Parent's pending queue.
- **Approval & Ledger**: When Parent clicks "Approve", the child's point balance increases by 10 points and an entry is logged in `PointLedger`.
- **Rejection Flow**: If rejected, no points are awarded, and the chore status reverts so it can be retried.
- **Test Coverage**: Automated integration tests verify that double approvals cannot credit duplicate points.

---

## 7. Out of Scope (Future Enhancements)

- Multi-tenant authentication (OAuth / JWT auth).
- In-app gift card / reward redemption store.
- Push notifications (email or SMS).
- Photo upload proof verification.
