# Jira for Application Security Engineers
**Real walkthroughs — every step matches actual Jira Cloud UI**

> Role context: You are an AppSec Engineer. Your Jira life revolves around security findings, vulnerability tickets, CI/CD gates, audit trails, compliance sprints, and risk acceptance workflows. This guide covers 30+ topics from first login to advanced automation — all steps match what you actually click in Jira Cloud.

---

## Table of Contents

1. [First Login & Profile Setup](#1-first-login--profile-setup)
2. [Exploring Your Workspace](#2-exploring-your-workspace)
3. [Understanding Project Types](#3-understanding-project-types)
4. [Creating a Security Project](#4-creating-a-security-project)
5. [Issue Types for Security Work](#5-issue-types-for-security-work)
6. [Creating a Vulnerability Ticket](#6-creating-a-vulnerability-ticket)
7. [Setting Priority & Severity Fields](#7-setting-priority--severity-fields)
8. [Custom Fields for Security Findings](#8-custom-fields-for-security-findings)
9. [Linking Issues (Finding → Fix → Test)](#9-linking-issues-finding--fix--test)
10. [Assigning Tickets to Developers](#10-assigning-tickets-to-developers)
11. [Labels & Components](#11-labels--components)
12. [Boards — Kanban for Security Triage](#12-boards--kanban-for-security-triage)
13. [Sprints for Security Reviews](#13-sprints-for-security-reviews)
14. [Filters & Saved Searches (JQL)](#14-filters--saved-searches-jql)
15. [Dashboards for Security Posture](#15-dashboards-for-security-posture)
16. [User Management — Adding Team Members](#16-user-management--adding-team-members)
17. [Creating Groups (Security Team Group)](#17-creating-groups-security-team-group)
18. [Project Roles & Permissions](#18-project-roles--permissions)
19. [Global Permissions](#19-global-permissions)
20. [Managing Security Incidents as Issues](#20-managing-security-incidents-as-issues)
21. [Epics for Compliance Programs](#21-epics-for-compliance-programs)
22. [Workflows — Moving Tickets Through Triage](#22-workflows--moving-tickets-through-triage)
23. [Custom Workflow for Vulnerability Lifecycle](#23-custom-workflow-for-vulnerability-lifecycle)
24. [Automation Rules — Auto-assign Critical Findings](#24-automation-rules--auto-assign-critical-findings)
25. [Automation — Escalate Overdue Security Tickets](#25-automation--escalate-overdue-security-tickets)
26. [Notifications & Watching Issues](#26-notifications--watching-issues)
27. [Bulk Editing — Triaging Multiple Findings](#27-bulk-editing--triaging-multiple-findings)
28. [Versions / Releases for Security Milestones](#28-versions--releases-for-security-milestones)
29. [Roadmaps for Security Programs](#29-roadmaps-for-security-programs)
30. [Reporting — Security Metrics for Management](#30-reporting--security-metrics-for-management)
31. [Integrating Jira with GitHub](#31-integrating-jira-with-github)
32. [Integrating Jira with Slack](#32-integrating-jira-with-slack)
33. [Service Management — Vulnerability Disclosure Intake](#33-service-management--vulnerability-disclosure-intake)
34. [Risk Acceptance Workflow](#34-risk-acceptance-workflow)
35. [Audit Log — Who Changed What](#35-audit-log--who-changed-what)
36. [Exporting for Compliance Reports](#36-exporting-for-compliance-reports)
37. [Personal Settings & Shortcuts](#37-personal-settings--shortcuts)

---

## 1. First Login & Profile Setup

**Agenda:** Get your account configured before anyone assigns you anything.

```
Go to → https://your-org.atlassian.net
→ Click "Log in with Google" (or email/password)
→ Top-right corner → click your Avatar (circle with initials)
→ Click "Profile"
→ Click "Edit profile"
→ Set Full Name → "Your Name (AppSec)"
→ Set Department → "Security Engineering"
→ Set Job title → "Application Security Engineer"
→ Save changes
→ Avatar → "Account settings"
→ "Security" tab
→ "Two-step verification" → Enable → Follow authenticator app setup
→ "API tokens" → "Create API token" → Label: "CLI access" → Copy token (save it — shown once)
```

> **Why:** Your API token is used for Jira CLI, automation scripts, and CI/CD webhook integrations. The profile fields appear on every ticket you create or comment on.

---

## 2. Exploring Your Workspace

**Agenda:** Understand what exists before you create anything.

```
Top navigation bar → "Projects" → "View all projects"
→ Scan the list: note which projects are "Scrum", which are "Kanban", which are "Service Management"
→ Click any project → look at left sidebar:
   - "Board" (the Kanban/Scrum view)
   - "Backlog" (all tickets not yet in sprint)
   - "Roadmap" (timeline view)
   - "Reports" (velocity, burndown, etc.)
   - "Project settings" (bottom of sidebar)
→ Top nav → "Your work"
→ See: "Assigned to me", "Watched", "Recent", "Boards"
→ Top nav → "People" → see your org and teams
→ Top nav → "Plans" (if Jira Advanced Roadmaps is enabled)
```

---

## 3. Understanding Project Types

**Agenda:** Know which project type to use for which security activity.

```
Top nav → "Projects" → "Create project"
→ You will see three options:
```

| Type | Use for | Board style |
|---|---|---|
| **Scrum** | Sprint-based security review cycles, quarterly audits | Sprint board + backlog |
| **Kanban** | Ongoing vulnerability triage (no fixed sprint) | Continuous flow board |
| **Service Management** | Vulnerability disclosure intake, pentest request queue | Request portal + SLA |

```
→ Press Escape (don't create yet — this was for learning the options)
```

> **AppSec day-to-day:** Vulnerability triage → Kanban. Compliance program → Scrum. Bug bounty / disclosure portal → Service Management.

---

## 4. Creating a Security Project

**Agenda:** Create a dedicated Kanban project for ongoing vulnerability management.

```
Top nav → "Projects" → "Create project"
→ Select "Scrum" or "Kanban" → Click "Select"
   (choose Kanban for always-on triage)
→ Project name: "Application Security — Vulnerability Triage"
→ Key: "SECVT" (auto-generated, edit if needed — this prefixes all ticket IDs: SECVT-1, SECVT-2)
→ Project lead: select yourself
→ Access: "Private" (security findings should not be public to all employees)
→ Click "Create project"
→ You land on the Kanban board with default columns: To Do | In Progress | Done
```

---

## 5. Issue Types for Security Work

**Agenda:** Configure the right issue types so a vulnerability ticket looks different from a general task.

```
Left sidebar → "Project settings"
→ "Issue types"
→ You see default types: Story, Task, Bug, Epic, Subtask
→ Click "Add issue type" (or use existing "Bug" for findings)

For a security project, recommended mapping:
```

| Jira Issue Type | Security Use |
|---|---|
| **Bug** | Individual vulnerability finding (SAST/DAST/SCA output) |
| **Task** | Security review task, code review, pentest activity |
| **Story** | Security feature (MFA enforcement, RBAC implementation) |
| **Epic** | Compliance program (OWASP Top 10 remediation, HIPAA audit) |
| **Sub-task** | Individual fix step under a larger vulnerability |

```
→ Drag to reorder as needed
→ "Save changes"
```

---

## 6. Creating a Vulnerability Ticket

**Agenda:** Log a real security finding the way a team expects it.

```
Top nav → "Create" (or press "C" keyboard shortcut)
→ Project: "Application Security — Vulnerability Triage"
→ Issue type: "Bug"
→ Summary: "[SAST][HIGH] SQL Injection in /api/patients/search — CWE-89"
→ Description field → Switch to "Rich text" mode → Enter:

   **Finding:** Unsanitized user input passed directly to SQL query
   **Scanner:** Semgrep rule python.lang.security.audit.sqli.avoid-sqli
   **File:** pursh/backend/api/patients.py line 42
   **Evidence:** `query = f"SELECT * FROM patients WHERE name = '{name}'"`
   **Remediation:** Use parameterized queries via SQLAlchemy ORM
   **OWASP:** A03:2021 — Injection
   **CVSS Score:** 8.1 (High)
   **Affected environment:** Production

→ Priority: "High"
→ Assignee: [developer who owns that file]
→ Reporter: [yourself — auto-filled]
→ Labels: "sast", "sql-injection", "cwe-89", "pursh-backend"
→ Due date: [today + 14 days for High findings per SLA]
→ Click "Create"
```

---

## 7. Setting Priority & Severity Fields

**Agenda:** Understand Jira's built-in Priority vs. your custom Severity field (they are different things).

```
→ Note: Jira's "Priority" = operational urgency (how fast to fix)
→ "Severity" = technical impact (how bad is the vulnerability)
→ These can differ: a Low severity finding in a critical auth service = High priority

To add a custom Severity field:
→ Top nav → Settings (gear icon, top right) → "Issues"
→ Left sidebar → "Custom fields"
→ "Create custom field"
→ Field type: "Select List (single choice)"
→ Name: "Security Severity"
→ Options: Add → "Critical" → Add → "High" → Add → "Medium" → Add → "Low" → Add → "Informational"
→ "Create"
→ "Associate to screens" → Select your security project's screens → "Update"

Now when creating a ticket:
→ "Create" → scroll down → "Security Severity" field appears
→ Set separately from "Priority"
```

---

## 8. Custom Fields for Security Findings

**Agenda:** Add fields that make security tickets auditable and traceable.

```
Settings (gear) → "Issues" → "Custom fields" → "Create custom field"

Create each of these:
```

| Field Name | Type | Values / Purpose |
|---|---|---|
| **CWE ID** | Text field (single line) | CWE-89, CWE-79, etc. |
| **OWASP Category** | Select list | A01–A10 (2021 list) |
| **CVE ID** | Text field | CVE-2024-XXXXX for SCA findings |
| **Scanner Name** | Select list | Semgrep, ZAP, Trivy, Grype, Gitleaks, Checkov |
| **Risk Acceptance** | Select list | None / Accepted / Mitigated / False Positive |
| **Risk Acceptance Reason** | Text area | Free text justification |
| **Fix Commit** | URL field | Link to the fixing PR/commit |
| **Verified Fixed** | Checkbox | Security engineer marks after re-scan |

```
For each field:
→ "Create custom field" → choose type → name it → "Create"
→ "Associate to screens" → your project's "Default Screen" → "Update"
```

---

## 9. Linking Issues (Finding → Fix → Test)

**Agenda:** Connect a vulnerability finding to the developer's fix ticket and the verification test ticket.

```
Open any vulnerability ticket (e.g., SECVT-42)
→ Click "Link" button (or "..." menu → "Link")
→ "Link type" dropdown:
   - "blocks" → SECVT-42 blocks DEV-891 (dev cannot close without fixing this)
   - "is blocked by" → reverse
   - "is cloned by" → for tracking across projects
   - "relates to" → loose association
   - "duplicates" → for deduplication
→ Issue to link: type DEV-891 (the developer's fix ticket) → Select it
→ Click "Save"

Now on SECVT-42 you see:
   "Blocks: DEV-891 — Fix SQL injection in patient search"

For verification ticket:
→ "Link" again
→ Type: "is verified by"
→ Link to: SECVT-45 (your re-scan/verification task)
```

> **Why this matters:** Auditors can trace the chain: finding → fix → verification. This is evidence for HIPAA §164.312 and OWASP ASVS reviews.

---

## 10. Assigning Tickets to Developers

**Agenda:** Get findings into the right developer's queue with context.

```
Option A — Direct assignment on ticket:
→ Open ticket → "Assignee" field → Click "Unassigned"
→ Type developer name → Select from dropdown
→ Change is saved automatically

Option B — Bulk assign from board:
→ Board view → find unassigned card → right-click → "Assign to..."
→ OR: use Bulk Edit (see topic 27)

Option C — Assignment with notification:
→ Open ticket → "Comment" section at bottom
→ Type: "@developer-name — this SAST finding is in your service (pursh/backend/api/patients.py:42). 
  Parameterized queries fix this. Due: [date]. Ask me if you need the remediation card."
→ Click "Save"
→ Developer gets email + in-app notification because they were @mentioned
```

---

## 11. Labels & Components

**Agenda:** Organize findings so you can filter and report by scanner, category, and service.

**Labels (free-form tags):**
```
On any ticket → "Labels" field → Type and press Enter:
   sast | dast | sca | container | secrets | iac | cloudsec
   critical | high | medium | low
   cwe-89 | cwe-79 | cwe-798
   pursh-backend | pursh-frontend | aisec-runner | infra
   owasp-a03 | owasp-a07
   false-positive | accepted-risk | needs-triage

To view all labels used in project:
→ Project settings → "Labels" (if available)
→ OR: Filters → JQL: label = "sast" ORDER BY created DESC
```

**Components (structured service areas):**
```
Project settings → "Components"
→ "Add component"
→ Name: "Pursh Backend" → Component lead: [backend owner]
→ Add: "Pursh Frontend", "AISec Runner", "CI/CD Pipeline", "Infrastructure/IaC", "Authentication"
→ Save

On ticket creation → "Component/s" field → Select "Pursh Backend"
Now you can filter: component = "Pursh Backend" AND labels = "critical"
```

---

## 12. Boards — Kanban for Security Triage

**Agenda:** Use the board as your daily triage desk.

```
Left sidebar → "Board"
→ Default columns: To Do | In Progress | Done

Customize columns for security workflow:
→ Board → top-right "..." → "Board settings"
→ "Columns" tab
→ "Add column" → Name: "Triage" → drag before "To Do"
→ "Add column" → Name: "Awaiting Developer" → after "In Progress"
→ "Add column" → Name: "Awaiting Verification" → after "Awaiting Developer"
→ "Add column" → Name: "Accepted Risk" → after "Awaiting Verification"
→ Save

Final column order:
  Triage → To Do → In Progress → Awaiting Developer → Awaiting Verification → Accepted Risk → Done

Swimlanes (group by):
→ Board settings → "Swimlanes"
→ "Base Swimlanes on": "Assignee" or "Labels" or "Priority"
→ Choose "Priority" → board shows Critical / High / Medium / Low rows
```

---

## 13. Sprints for Security Reviews

**Agenda:** If using Scrum, run two-week security review cycles.

```
Left sidebar → "Backlog"
→ Top right of Backlog → "Create sprint"
→ Sprint name: "Security Review Sprint 1 — SAST + SCA"
→ Goal: "Triage all Semgrep + Trivy findings from May release"
→ Start date: today
→ End date: today + 14 days
→ Click "Create sprint"

Add tickets to sprint:
→ In Backlog, right-click any ticket → "Move to sprint" → Select "Sprint 1"
→ OR drag tickets from backlog into the sprint section

Start the sprint:
→ "Start sprint" button → Confirm dates → "Start"
→ Board now shows only sprint tickets

End of sprint:
→ "Complete sprint" → choose what to do with incomplete tickets:
   - "Move to Backlog" (most common)
   - "Move to next sprint"
→ Sprint report auto-generates (velocity, completed vs incomplete)
```

---

## 14. Filters & Saved Searches (JQL)

**Agenda:** JQL is your SQL for finding security tickets. Learn it well.

```
Top nav → "Filters" → "Advanced issue search"
→ Switch to "Advanced" mode (top right of search bar)
```

**Essential JQL queries for AppSec:**

```jql
-- All open critical/high findings assigned to me
project = SECVT AND priority in (Critical, High) AND assignee = currentUser() AND status != Done

-- All unassigned findings needing triage
project = SECVT AND assignee is EMPTY AND status = "Triage" ORDER BY created ASC

-- All SAST findings from last 7 days
project = SECVT AND labels = "sast" AND created >= -7d ORDER BY priority DESC

-- Overdue High+ findings (past due date)
project = SECVT AND priority in (Critical, High) AND due < now() AND status != Done

-- All false positives this quarter
project = SECVT AND "Risk Acceptance" = "False Positive" AND created >= startOfQuarter()

-- Findings awaiting developer fix for > 30 days
project = SECVT AND status = "Awaiting Developer" AND updated <= -30d

-- All Trivy (SCA) container findings
project = SECVT AND "Scanner Name" = "Trivy" AND labels = "container"

-- Accepted risk tickets — for audit export
project = SECVT AND "Risk Acceptance" = "Accepted" ORDER BY created ASC
```

```
To save a filter:
→ After typing JQL → "Save as" → Name: "Overdue High+ Security Findings"
→ "Save"
→ Now accessible under Filters → "View all filters" → "My filters"

To share a filter with team:
→ Open saved filter → "Details" → "Edit permissions"
→ "Share with" → Select your security group → "Save"
```

---

## 15. Dashboards for Security Posture

**Agenda:** Build a management-visible dashboard showing security posture at a glance.

```
Top nav → "Dashboards" → "Create dashboard"
→ Name: "Security Posture — AppSec Overview"
→ "Private" → "Create"

Add gadgets (widgets):
→ "Add gadget" (top right of dashboard)

Add each gadget:
→ "Filter Results" gadget → Saved filter: "All Open Critical/High" → Columns: Summary, Priority, Assignee, Due Date → "Save"

→ "Pie Chart" gadget → Filter: all open SECVT tickets → Stat type: "Priority" → "Save"
  (shows Critical/High/Medium/Low breakdown)

→ "Two Dimensional Filter Statistics" gadget
  → Filter: all SECVT tickets
  → X axis: Priority
  → Y axis: Scanner Name
  → "Save" (shows findings matrix: how many Critical findings per scanner)

→ "Created vs Resolved Chart" gadget
  → Filter: SECVT project
  → "Save" (shows if you're resolving faster than new findings arrive — your burn rate)

→ "Assigned to Me" gadget → straightforward queue view

Share dashboard:
→ "..." → "Edit" → "Add viewers"
→ Add CISO, engineering manager → "Save"
```

---

## 16. User Management — Adding Team Members

**Agenda:** Onboard a new developer to the security project.

```
Top nav → Settings (gear icon) → "User management"
→ Left sidebar → "Users"
→ "Invite users" button (top right)
→ Enter email: developer@company.com
→ Product access: "Jira Software" → Role: "Basic" (not admin)
→ "Send invite"

Once they accept:
→ Settings → User management → Users → Search their name
→ Click their name → "Product access" tab
→ Verify they have "Jira Software — Member" access

Add to project:
→ Navigate to your security project
→ Project settings → "People"
→ "Add members" → Search name → Role: "Developer" or "Viewer"
→ "Add"
```

---

## 17. Creating Groups (Security Team Group)

**Agenda:** Groups let you assign permissions, filters, and dashboards to the whole security team at once.

```
Settings (gear) → "User management"
→ Left sidebar → "Groups"
→ "Create group"
→ Group name: "security-engineers"
→ Description: "Application Security Engineering team"
→ "Create group"

Add members:
→ Click "security-engineers" group
→ "Add members" → Search and add each AppSec team member → "Add"

Now use the group instead of individuals:
→ Project permissions → Assign "Security Engineers" group to roles
→ Filter sharing → Share with "security-engineers" group
→ Dashboard sharing → Share with "security-engineers" group
→ Notifications → Notify "security-engineers" group on Critical findings
```

---

## 18. Project Roles & Permissions

**Agenda:** Control who can create/edit/delete security tickets — findings are sensitive.

```
Project settings → "People" → "Manage roles"

Default roles:
→ "Administrators" — full project control
→ "Developers" — create/edit issues
→ "Viewers" — read only (good for developers not on the security team)

Add members to roles:
→ Click "Administrators" → "Add members"
→ Add security team members as Administrators
→ Click "Developers" → Add dev team members (they can update their assigned tickets)
→ "Viewers" → Add CISO, compliance auditors (read-only audit trail access)

Project settings → "Permissions"
→ Review each permission:
   - "Create Issues" → Roles: Administrators, Developers (not Viewers)
   - "Delete Issues" → Roles: Administrators only
   - "Resolve Issues" → Roles: Administrators, Developers
   - "Move Issues" → Roles: Administrators only
   - "Edit Issues" → Roles: Administrators, Developers (own issues)
→ "Save"
```

---

## 19. Global Permissions

**Agenda:** Understand what global admins can do vs. project-level control.

```
Settings (gear) → "System" → "Global permissions"
(Note: this requires Jira Administrator access — your org's Jira admin controls this)

Key global permissions to know:
```

| Permission | Who should have it | Why it matters for AppSec |
|---|---|---|
| **Jira Administrators** | Jira admin only | Can delete projects, modify all workflows |
| **Browse Users** | All users | Needed to @mention teammates in tickets |
| **Manage Group Filter Subscriptions** | Power users | Can share saved filters |
| **Bulk Change** | Security engineers | Needed for bulk-triaging scan results |
| **Create Shared Objects** | Security engineers | Needed to share dashboards/filters org-wide |

```
→ If you need "Bulk Change" and don't have it → ask your Jira admin to grant it to your user or group
→ Settings → System → Global permissions → "Bulk Change" → "Add" → Select your group → "Grant"
```

---

## 20. Managing Security Incidents as Issues

**Agenda:** When an incident happens (e.g., exposed S3 bucket, leaked secret), track it in Jira.

```
"Create" → Issue type: "Bug" (or if you have it: "Incident")
→ Summary: "[INCIDENT][P1] AWS S3 bucket pursh-lab-assets publicly accessible — 2024-05-22"
→ Priority: "Critical"
→ Labels: "incident", "p1", "cloudsec", "s3", "data-exposure"
→ Description:
   **Detected:** 2024-05-22 14:32 UTC via Prowler check S3.2
   **Impact:** Public read access on bucket containing synthetic lab result PDFs
   **Data at risk:** Synthetic PHI only — no real patient data
   **Immediate action taken:** Bucket policy removed at 14:40 UTC
   **Owner:** @infrateam
   **Status:** Containment complete, eradication in progress
   **NIST phase:** Eradication

→ Create linked sub-tasks:
   → "Link" → "is parent of" → Create sub-tasks:
     - SECVT-50: Block public access on all S3 buckets (Checkov IaC fix)
     - SECVT-51: Audit all bucket policies (Prowler re-scan)
     - SECVT-52: Update incident runbook with detection timeline
     - SECVT-53: Management notification — prepare posture summary

→ Due date: today + 4 hours for P1 containment SLA
```

---

## 21. Epics for Compliance Programs

**Agenda:** Organize a multi-month compliance program (OWASP Top 10 remediation) as an Epic.

```
"Create" → Issue type: "Epic"
→ Epic name: "OWASP Top 10 Remediation — Pursh Backend"
→ Summary: "OWASP Top 10 (2021) full remediation for Pursh backend service"
→ Description:
   Sprint-by-sprint plan to remediate all OWASP findings detected by Semgrep + ZAP
   Target: Zero High+ OWASP findings by Q3 2024
   Scope: pursh/backend/ — all Python FastAPI routes

→ Start date: today
→ Due date: today + 90 days
→ Labels: "owasp-top10", "compliance", "q3-goal"
→ Create

Link findings to this Epic:
→ Open any vulnerability ticket (e.g., SECVT-42 — SQL Injection)
→ "Epic Link" field → Select "OWASP Top 10 Remediation — Pursh Backend"
→ Now this finding is tracked under the Epic

View Epic progress:
→ Left sidebar → "Roadmap" → see Epic as a bar on the timeline
→ Click Epic → see all linked child issues + completion %
```

---

## 22. Workflows — Moving Tickets Through Triage

**Agenda:** Understand the lifecycle states of a vulnerability ticket.

```
Open any ticket → top right area shows current status button (e.g., "Triage")
→ Click the status button → see available transitions:
   "Triage" → "Assign to Developer"
   "Triage" → "Mark False Positive"
   "Triage" → "Accept Risk"
   "In Progress" → "Awaiting Verification"
   "Awaiting Verification" → "Done" (after re-scan confirms fix)
   "Awaiting Verification" → "Reopen" (if re-scan shows still vulnerable)

To see the full workflow diagram:
→ Project settings → "Workflows"
→ Click the workflow name → "View" (shows diagram of all states + transitions)
```

**Standard AppSec vulnerability lifecycle:**

```
New Finding Created
      ↓
  [Triage]  ← AppSec reviews: real? scope? severity correct?
      ↓               ↓                    ↓
[Assign Dev]    [False Positive]     [Accept Risk]
      ↓               ↓                    ↓
[In Progress]     [Closed]           [Accepted Risk]
      ↓                                    ↓
[Awaiting Verification]             [Quarterly Review]
      ↓               ↓
   [Done]          [Reopen]
```

---

## 23. Custom Workflow for Vulnerability Lifecycle

**Agenda:** Create a workflow that exactly matches the security triage process.

```
Project settings → "Workflows"
→ "Add workflow" → "Create new workflow"
→ Name: "AppSec Vulnerability Lifecycle"

Add statuses:
→ "Add status" → Name: "Triage" → Category: "To Do"
→ "Add status" → Name: "Assigned to Developer" → Category: "In Progress"
→ "Add status" → Name: "Fix In Progress" → Category: "In Progress"
→ "Add status" → Name: "Awaiting Verification" → Category: "In Progress"
→ "Add status" → Name: "Accepted Risk" → Category: "To Do" (special holding state)
→ "Add status" → Name: "False Positive" → Category: "Done"
→ "Add status" → Name: "Remediated" → Category: "Done"

Add transitions (arrows between statuses):
→ Click "Add transition"
→ Name: "Begin Triage" → From: [any] → To: "Triage"
→ "Assign to Dev" → From: "Triage" → To: "Assigned to Developer"
→ "Start Fix" → From: "Assigned to Developer" → To: "Fix In Progress"
→ "Submit for Verification" → From: "Fix In Progress" → To: "Awaiting Verification"
→ "Verify Fixed" → From: "Awaiting Verification" → To: "Remediated"
→ "Reopen" → From: "Awaiting Verification" → To: "Fix In Progress"
→ "Mark False Positive" → From: "Triage" → To: "False Positive"
→ "Accept Risk" → From: "Triage" → To: "Accepted Risk"

Publish workflow:
→ "Publish" → "Associate with project" → Select SECVT → "Associate"
```

---

## 24. Automation Rules — Auto-assign Critical Findings

**Agenda:** When a Critical ticket is created, automatically assign it to the lead AppSec engineer and set a due date.

```
Project settings → "Automation"
→ "Create rule"

Trigger:
→ "Issue created"
→ Next

Condition:
→ "Add condition" → "Issue fields condition"
→ Field: "Priority" → Condition: "equals" → Value: "Critical"
→ Next

Actions (add multiple):
→ "Add action" → "Assign issue"
   → Assignee: [AppSec lead username]

→ "Add action" → "Edit issue fields"
   → Field: "Due date"
   → Value: "{{now.plusDays(1)}}" (Critical = 24-hour SLA)

→ "Add action" → "Add comment"
   → Comment: "🚨 CRITICAL finding auto-triaged. Due: {{issue.duedate}}. 
     AppSec lead notified. Review and assign to owning developer within 2 hours."

Rule name: "Auto-triage Critical Security Findings"
→ "Turn it on" toggle → "Save"
```

---

## 25. Automation — Escalate Overdue Security Tickets

**Agenda:** Automatically flag tickets that developers haven't touched in 14 days.

```
Project settings → "Automation" → "Create rule"

Trigger:
→ "Scheduled"
→ Run: "Every day at 09:00"

Condition:
→ "JQL condition"
→ JQL: project = SECVT AND priority in (Critical, High) AND status = "Assigned to Developer" AND updated <= -14d AND status != Done

Actions:
→ "Add comment":
   "⚠️ This {{issue.priority}} security finding has been assigned for 14+ days without update. 
   SLA breach imminent. @{{issue.assignee.displayName}} — please update status or request extension.
   AppSec lead: @[your-name] has been notified."

→ "Edit issue fields" → "Priority" → escalate one level up if not already Critical

→ "Send email"
   → To: [AppSec lead email], [Engineering Manager email]
   → Subject: "Overdue security finding: {{issue.key}} — {{issue.summary}}"

Rule name: "Escalate Overdue High+ Security Findings"
→ Save → Enable
```

---

## 26. Notifications & Watching Issues

**Agenda:** Get the right alerts without notification spam.

```
Watch a ticket (get all updates):
→ Open any ticket → top right → bell icon → "Watch"
→ Now you get emailed on every comment, status change, field change

Stop watching:
→ Same bell icon → "Stop watching"

Manage notification scheme (project-wide):
→ Project settings → "Notifications"
→ "Notification scheme": default Jira scheme
→ "Actions" → "Edit notifications"
→ Per event (Issue Created, Issue Updated, etc.), add/remove notification recipients:
   - "Current Assignee" → always on (developer assigned to fix)
   - "Reporter" → always on (you as the AppSec who filed it)
   - "Group" → "security-engineers" for Critical findings

Personal notification preferences:
→ Avatar → "Profile" → "Notifications"
→ Choose: email | in-app | both
→ Toggle off categories you don't need (e.g., "My Changes" — don't notify yourself on your own edits)

@mentions:
→ In any comment: @username → they get an email notification regardless of watch status
→ Use this for: "@developer — this blocks your release. Critical. Fix by Thursday."
```

---

## 27. Bulk Editing — Triaging Multiple Findings

**Agenda:** After a scan run produces 200 findings, triage them in bulk without opening each one.

```
Top nav → "Filters" → "Advanced issue search"
→ Run JQL: project = SECVT AND status = "Triage" AND labels = "sast" AND created >= -1d
→ This shows today's new SAST findings

Switch to List view (not board):
→ Top right → grid icon → "List"
→ Check the checkbox in column header → "Select all X issues"

Bulk operations:
→ "Bulk Change" button appears at top
→ Choose: "Edit Issues"
→ Available bulk edits:
   - "Change Assignee" → assign all to relevant developer
   - "Change Priority" → downgrade all "Medium" SAST findings to verify severity
   - "Add Label" → add "needs-manual-review" to a batch
   - "Change Component" → bulk-categorize by service
   - "Transition Issues" → move all from "Triage" to "Assigned to Developer"
→ Make your changes → "Confirm"

Note: bulk change is logged in each ticket's history — full audit trail preserved.
```

---

## 28. Versions / Releases for Security Milestones

**Agenda:** Track which software version introduced or fixed a finding.

```
Project settings → "Versions"
→ "Create version"
→ Name: "v2.3.0-security-patch"
→ Start date: today
→ Release date: today + 7 days
→ Description: "OWASP A03 SQL injection fixes — Pursh backend"
→ "Add"

On any ticket:
→ "Fix Version/s" field → Select "v2.3.0-security-patch"
→ "Affects Version/s" field → Select the version where vulnerability was introduced

Reports:
→ Left sidebar → "Reports" → "Version Report"
→ Select "v2.3.0-security-patch"
→ See: all tickets in this version, completion %, estimated release date
→ Use for: "We're releasing v2.3 — are all Critical security fixes confirmed remediated?"

Release notes for security:
→ "Versions" → click version name → "Release Notes"
→ Auto-generates list of all fixed issues in this version
→ Share with CISO as evidence of remediation for the release
```

---

## 29. Roadmaps for Security Programs

**Agenda:** Show the CISO a 6-month security program timeline without a spreadsheet.

```
Left sidebar → "Roadmap"
→ You see Epics on a horizontal timeline

Create program Epics visible on roadmap:
→ "Create Epic" (inline in roadmap or via Create button)

Suggested AppSec roadmap Epics:
```

| Epic | Quarter | Goal |
|---|---|---|
| SAST Baseline — All Critical Fixed | Q1 | Zero Critical Semgrep findings |
| DAST Integration — ZAP on Every PR | Q1 | ZAP baseline scan in CI/CD |
| SCA Dependency Hygiene | Q2 | No Critical CVEs in production deps |
| Container Hardening | Q2 | Trivy image gate passing |
| OWASP Top 10 Full Coverage | Q3 | All 10 categories tested + mapped |
| HIPAA Compliance Mapping | Q3 | Finding→HIPAA mapping complete |
| Annual Security Review | Q4 | External pentest + full audit |

```
Set Epic dates:
→ Click Epic on roadmap → set start + end dates → drag to adjust
→ Child issues (linked bugs/tasks) appear as dots under each Epic bar

Share roadmap:
→ Top right → "Share" → copy link → send to CISO
→ Or: "Export" → PNG / CSV
```

---

## 30. Reporting — Security Metrics for Management

**Agenda:** Pull the numbers management actually asks about in weekly reviews.

```
Left sidebar → "Reports"

Key reports for AppSec:

1. "Created vs Resolved Chart"
→ Time range: Last 30 days
→ Shows: new findings per day vs. findings closed per day
→ If "created" line is above "resolved" line → backlog is growing → escalate

2. "Pie Chart" (via dashboard gadget)
→ Grouped by "Priority" → shows Critical/High/Medium/Low split
→ Grouped by "Assignee" → shows who owns the most open findings

3. Custom report via filter + export:
→ JQL: project = SECVT AND status = Done AND resolutiondate >= startOfMonth()
→ Columns: Key, Summary, Priority, Scanner, Fix Commit, Resolved
→ "Export" → "CSV" → open in Excel → calculate MTTR:
   MTTR = average(resolutiondate - created) for all resolved this month

4. Velocity Report (Scrum only):
→ Shows sprint-over-sprint completion rate
→ Use to show: "Security team is resolving 15 findings/sprint — at this rate, backlog clears in 8 weeks"

5. Time in Status (requires add-on or export):
→ Export all tickets → calculate average days in "Awaiting Developer" status
→ Benchmark: High should not sit in "Awaiting Developer" > 14 days
```

**Monthly management email format:**
```
Security Posture — May 2024

New findings this month:    42
Closed this month:          38  (MTTR: 9.2 days avg)
Still open Critical/High:    7  (down from 12 last month)
False positives:             6  (14% FP rate — Semgrep Python rules)
Accepted risks:              2  (documented + approved)
SLA breach:                  1  (SECVT-88 — escalated to eng manager)
```

---

## 31. Integrating Jira with GitHub

**Agenda:** Link PRs and commits directly to Jira tickets so the fix is traceable.

```
Settings (gear) → "Products" → "DVCS accounts" (or "GitHub" under "Integrations")
→ "Add GitHub account" → Authorize with GitHub OAuth
→ Select your organization → "Save"

Once connected, in GitHub:
→ In any commit message or PR title/body, reference the Jira ticket key:
   git commit -m "SECVT-42: fix SQL injection with parameterized query"
   PR title: "SECVT-42 — fix SQL injection in patient search endpoint"

In Jira, open SECVT-42:
→ Right side panel → "Development" section → see:
   - Commits: 1 commit linked
   - Pull requests: PR #145 "Open" or "Merged"
   - Branches: "fix/secvt-42-sql-injection"

This means:
→ CISO can open SECVT-42 and click through to the exact line of code that was fixed
→ Auditors see: finding → ticket → commit → PR → merged → verified
→ No manual linking needed — the ticket key in the commit does it automatically
```

---

## 32. Integrating Jira with Slack

**Agenda:** Get Jira ticket updates in your security Slack channel without leaving Slack.

```
Settings (gear) → "Products" → "Slack integration"
→ OR: in Slack → Apps → "Jira Cloud" → Install

In Slack:
→ /jira connect → Follow OAuth flow → Authorize

Subscribe a Slack channel to Jira events:
→ In #security-alerts Slack channel → type: /jira subscribe
→ JQL filter: project = SECVT AND priority in (Critical, High) AND status changed
→ Notify on: "Issue Created", "Status Changed", "Comment Added"
→ Save subscription

Now when a Critical finding is created in Jira:
→ #security-alerts gets: 
   🚨 New Critical: [SECVT-99] SQL Injection in /api/admin — assigned to @dev-name — due tomorrow

From Slack, team members can:
→ Type: /jira view SECVT-99 → see full ticket in Slack
→ Type: /jira comment SECVT-99 "Working on fix — will have PR by EOD"
→ Type: /jira transition SECVT-99 → move status without opening Jira
```

---

## 33. Service Management — Vulnerability Disclosure Intake

**Agenda:** Create a public-facing portal where external researchers can report vulnerabilities.

```
Top nav → "Projects" → "Create project"
→ Select "Service Management" → "Use template" → "IT Service Management" or "General service project"
→ Name: "Vulnerability Disclosure — AISec"
→ Key: "VDP"
→ "Create project"

Configure request types:
→ Project settings → "Request types"
→ "Add request type"
→ Name: "Report a Security Vulnerability"
→ Icon: shield icon
→ Description: "Found a security issue? Report it here. We respond within 5 business days."
→ Fields to collect:
   - "Summary" (required): Brief description
   - "Description" (required): Steps to reproduce
   - "Environment" (optional): Affected product/version
   - "Impact" (optional): What data or systems are at risk
→ "Create"

Set SLA:
→ Project settings → "SLAs"
→ "Create SLA"
→ Name: "Initial Response — Security Reports"
→ Goal: Complete within "5 business days"
→ Start: when issue created → Stop: when status = "Acknowledged"

Share portal:
→ Project settings → "Customer portal"
→ Copy portal URL → paste in your SECURITY.md file and GitHub repo
→ External researchers submit here → you triage in Jira behind the portal
```

---

## 34. Risk Acceptance Workflow

**Agenda:** Formally document when a finding won't be fixed — required for audits.

```
Open the vulnerability ticket (e.g., SECVT-55)
→ Click status → "Accept Risk" transition (from custom workflow)

Fill in required fields:
→ "Risk Acceptance" custom field → "Accepted"
→ "Risk Acceptance Reason" field → type:
   "This finding is in a development-only endpoint not exposed in production.
   The endpoint requires admin authentication. CVSS Environmental score drops to 3.1 (Low).
   Accepted risk per AppSec policy: Low environmental severity in non-production = acceptable.
   Owner approval: Engineering Manager @[name] — verbal approval 2024-05-22.
   Review date: 2024-08-22 (90 days)."
→ Labels: add "accepted-risk"
→ Due date: set to 90-day review date

Add approver comment:
→ Comment: "@manager — please confirm acceptance of this risk in a reply to this ticket for audit trail."
→ Manager replies → you now have written approval in Jira

Save JQL for audit:
→ JQL: project = SECVT AND "Risk Acceptance" = "Accepted" ORDER BY "Risk Acceptance Reason" ASC
→ Save as: "Accepted Risks — Audit Export"
→ Export to CSV quarterly for compliance reports
```

---

## 35. Audit Log — Who Changed What

**Agenda:** See every action taken on a ticket — essential for audit defense.

**Per-ticket history:**
```
Open any ticket → scroll to bottom → "History" tab (next to "Activity")
→ See every change:
   - 2024-05-22 14:00: [your-name] changed Priority from Medium → High
   - 2024-05-22 14:05: [your-name] assigned to developer@company.com
   - 2024-05-22 16:30: developer@company.com changed status from "Assigned" → "Fix In Progress"
   - 2024-05-23 09:00: [your-name] changed status → "Awaiting Verification"
→ Each change shows: who, what, when, old value, new value
```

**Global audit log (Jira Admin required):**
```
Settings (gear) → "System" → "Audit log"
→ Shows org-wide: project created, user invited, permission changed, workflow modified
→ Filter by: date range, user, category
→ Export: "Export" → CSV

For a security incident investigation:
→ Filter: user = "suspicious-user@company.com" → date range: last 7 days
→ See every action they took in Jira (ticket edits, exports, permission changes)
```

---

## 36. Exporting for Compliance Reports

**Agenda:** Generate the evidence package auditors need without manual work.

```
Method 1 — CSV Export (quick):
→ Filters → run JQL: project = SECVT AND created >= startOfQuarter()
→ "Export" → "Export Excel CSV (current fields)"
→ Opens in Excel: all findings with every field value
→ Format: add columns for MTTR calculation, filter by quarter, summarize by priority

Method 2 — Printable view (for specific tickets):
→ Open ticket → "..." → "Print" or "Export to PDF"
→ Shows full ticket with all fields, comments, history
→ Use for: individual accepted-risk documentation for auditors

Method 3 — Automation export (scheduled):
→ Automation rule → Trigger: "Scheduled" (first of each month)
→ Action: "Send email" to CISO with link to saved filter
→ Filter link auto-opens the current month's resolved findings

Method 4 — Jira API (for custom reports):
→ Endpoint: GET /rest/api/3/search?jql=project=SECVT&fields=summary,priority,status,customfield_10001
→ Use your API token from topic 1
→ Pipe into Python script to generate posture report PDF

Compliance audit pack checklist:
```

| Evidence | Source | Export method |
|---|---|---|
| All findings this period | JQL + CSV | Export Excel |
| Accepted risks with justification | JQL filter "Risk Acceptance" = Accepted | CSV + PDF per ticket |
| MTTR by severity | Resolved tickets + created date | CSV → Excel calculation |
| False positive rate | FP tickets / total tickets | CSV count |
| Overdue SLA breaches | Overdue JQL | CSV |
| Who approved risk acceptances | Ticket comments/history | Per-ticket print |

---

## 37. Personal Settings & Shortcuts

**Agenda:** Move 30% faster in Jira with keyboard shortcuts and personal config.

```
Personal settings:
→ Avatar → "Personal settings"
→ "Language": English (obvious but check)
→ "Time zone": Your local zone (affects due date displays)
→ "Notifications": reduce to what you actually need
→ "My profile": keep updated (name shows on every ticket)

Keyboard shortcuts (press ? anywhere in Jira to see full list):
```

| Key | Action |
|---|---|
| `C` | Create new issue |
| `E` | Edit current issue |
| `G` then `G` | Go to Agile board |
| `G` then `D` | Go to Dashboard |
| `G` then `P` | Go to Projects |
| `/` | Focus search bar |
| `?` | Show all shortcuts |
| `J` / `K` | Next / Previous issue in list |
| `A` | Assign to me |
| `I` | Assign issue (open picker) |
| `M` | Comment on issue |
| `L` | Edit labels |
| `S` | Watch / unwatch issue |
| `T` | View all transitions |

**Quick tips:**
```
→ Pin your most-used project in left sidebar:
   Top nav → "Projects" → hover over your project → star icon → now it's pinned

→ Starred filters (quick access):
   Filters → "View all filters" → star any filter → appears in Filters dropdown

→ Board quick filters (per-board shortcuts):
   Board view → top right → "Quick Filters"
   → "Add quick filter" → Name: "My Critical" → JQL: assignee = currentUser() AND priority = Critical
   → Now one click on board shows only your critical tickets

→ Backlog refinement shortcut:
   Backlog → right-click any ticket → common fields appear inline — no need to open the ticket
```

---

## Quick Reference — AppSec Engineer Daily Jira Checklist

```
Morning (15 minutes):
→ Filters → "Assigned to me" → check overnight assignments
→ Dashboard → "Security Posture" → note any new Criticals
→ Backlog → triage any new auto-created tickets from overnight scans

During the day:
→ Move tickets through workflow as work happens
→ Comment on tickets where developers need guidance
→ @mention relevant people when blockers arise

End of day:
→ Update "Awaiting Verification" tickets after re-scans
→ Check automation rule results (any escalations triggered?)
→ Ensure all Critical tickets have a due date and assignee

Weekly:
→ Pull "Overdue High+ Security Findings" filter → escalate stragglers
→ Update Risk Acceptance tickets approaching 90-day review dates
→ Export CSV for management weekly update

Monthly:
→ Export compliance audit pack
→ Update CISO dashboard with posture summary
→ Close out completed sprints / verify no stale "Remediated" tickets
→ Review FP rate — tune scanner rules if > 20%
```

---

*File: `internal/Learning/Jira.md` | Role: Application Security Engineer | Coverage: 37 topics — account setup through compliance export*
