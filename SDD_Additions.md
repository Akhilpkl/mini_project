# System Design Document (SDD) — Project Extensions

This document provides formal technical specifications for the newly implemented modules of the **Alumni Management System**. These sections are designed to be appended to the existing project report for academic submission.

---

## 4.0 Module Specifications

### 4.1 Real-Time Messaging System
The messaging module implements an asynchronous communication protocol between users of different roles (Student, Alumni, Faculty).
- **Communication Flow**: 1-to-1 duplex messaging using AJAX polling at 2.5s intervals.
- **Data Persistence**: Messages are stored with UTC timestamps and linked via Foreign Key relationships to the `User` table.
- **Sorting Logic**: Conversations are dynamically sorted in descending order based on the `timestamp` of the most recent message exchanged.

### 4.2 Unread Message Notification System
A tracking mechanism for message status to improve user engagement and responsiveness.
- **Logic**: A boolean `is_read` flag is toggled upon fetching messages via the `api_get_chat` endpoint.
- **UI Indicators**: Modern badges with glowing effects (box-shading) signify unread counts in the sidebar and message list.

### 4.3 Profile Access Interdependency
To enhance networking, user profiles are directly accessible from the messaging interface.
- **Event Handling**: Clicking a profile photo or name triggers navigation to the `view_profile` route.
- **Bubbling Prevention**: `event.stopPropagation()` is utilized to distinguish between profile viewing and chat activation.

### 4.4 Alumni Event Photo Sharing and Verification System
A moderated community hub for sharing visual records of alumni gatherings and reunions.
- **Workflow Architecture**: Implements a three-stage lifecycle: **Upload** (Alumni) -> **Verification** (Faculty) -> **Gallery Display** (Global).
- **Moderation Logic**: Photos are assigned a `pending` status upon upload and are only rendered in the public gallery after explicit `approved` status transition by authorized faculty.
- **Verification Panel**: A specialized administrative interface for faculty to review, approve, or reject submissions based on content quality and relevance.

---

## 5.0 Enhanced Administration Architecture

### 5.1 Admin Panel Design
The administrative suite is transitioned from a simple dashboard to a multi-route functional architecture.
- **Base Layout**: `admin_base.html` provides a dedicated sidebar with role-specific navigation.
- **Functional Components**:
    - **Dashboard**: Overview of system health and metrics.
    - **User Management**: full CRUD operations on user accounts.
    - **Approvals**: Verification workflows for Faculty and Alumni profiles.
    - **Job Moderation**: Review and deletion of job postings.
    - **Points Control**: Administrative points adjustment and historical tracking.

---

## 6.0 Gamification & Point System

### 6.1 Role-Based Restrictions
The gamification engine is architected with strict role-based rules:
- **Alumni**: Only users with the `alumni` role can earn points for profile updates and job postings.
- **Students/Faculty**: These roles are restricted from point accumulation but have read-access to the global leaderboard.
- **Admin**: Admins possess the authority to manage (reset/update) points but do not participate in the earning cycle.

### 6.2 Point Validation & Prevention
- **Unique Actions**: A `PointTransaction` record ensures that one-time actions (like profile completion) do not award duplicate points.
- **Daily Frequency**: The `daily_login` action is throttled to once per 24-hour cycle using server-side timestamp validation.

---

## 7.0 Database Schema Extensions

### 7.1 New Entity Definitions
| Table Name | Attributes | Description |
|------------|------------|-------------|
| `message` | `sender_id`, `recipient_id`, `content`, `timestamp`, `is_read` | Stores 1-to-1 communication history. |
| `point_transaction` | `user_id`, `action`, `amount`, `timestamp` | Audit log for all gamification events. |
| `event_photo` | `id`, `user_id`, `image_path`, `caption`, `event_name`, `status`, `verified_by`, `uploaded_at` | Stores moderated community event photos. |

### 7.2 Updated Relationships
- **User ↔ Message**: One-to-Many relationship (one user can send/receive many messages).
- **User ↔ PointTransaction**: One-to-Many relationship (each point earned is logged as a transaction).
- **User ↔ EventPhoto**: One-to-Many relationship (alumni can upload multiple photos).
- **Faculty ↔ EventPhoto**: One-to-Many relationship (faculty verifies and approves submissions).

---

## 8.0 Updated Use Cases

1.  **UC04: Real-Time Messaging**: Allows users to exchange text messages and receive instant notifications.
2.  **UC05: Profile Navigation**: Users can transition directly from a chat card to the full profile of the contact.
3.  **UC06: Administrative Moderation**: Administrator approves or rejects pending alumni/faculty applications.
4.  **UC07: Points Management**: Administrator manually updates or resets user points to maintain system integrity.
5.  **UC08: Upload Event Photo**: Alumni submits a photo with a caption for moderation.
6.  **UC09: Moderate Photos**: Faculty reviews pending photos and approves them for public display.
7.  **UC10: View Event Gallery**: Users browse approved alumni event photos on the dashboard.

---

## 9.0 Security & Validation
- **Role-Based Access Control (RBAC)**: Strict separation of privileges ensures only Alumni can upload and only Faculty/Admin can moderate content.
- **File Validation**: MIME-type restriction (JPG/PNG) and file size limitation (2MB) prevent malicious uploads and storage overhead.
- **Access Control**: Unapproved photos are isolated from the public GET requests using server-side filters.

---

## 9.0 Non-Functional Improvements
- **Performance**: Asynchronous fetching reduces server load compared to full-page reloads.
- **Responsiveness**: Modern UI components ensure consistent behavior across different screen resolutions.
- **Data Integrity**: Transaction-based point updates prevent synchronization issues in the database.
