# TODO - EAC Incident Audit Report redesign

- [x] Implement improved compliance-ready **Ticket-based** Audit Report generation (PDF + Excel)

  - [x] Add chart generation for PDF (department/priority/status distributions) and embed in report
  - [x] Compute Executive Summary + statistics (counts + average resolution time + most common category)
  - [x] Render Detailed Incident Table with required columns
  - [x] Add Resolution Details (resolution notes, resolved by, resolution date) using existing models (Ticket/resolved_at + comments/audit logs as best-available notes)
  - [x] Add Audit Trail section using `AuditLog` for tickets included in the report (user/action/time/prev/new status best-effort)
  - [x] Auto-generate Recommendations section from computed stats
  - [x] Add Approval section (placeholders)
  - [x] Improve PDF formatting: branding logo, table styling, page numbering, generation timestamp
  - [x] Improve Excel formatting: multiple sheets, header styling, and column auto-sizing
- [ ] Update Django views/endpoints to serve the redesigned PDF/Excel at existing routes
- [x] Add any needed helper utilities (preferably in `core/utils.py` or a new `core/reporting.py`)
- [ ] Add/verify dependencies for charts (matplotlib) and run quick manual tests
