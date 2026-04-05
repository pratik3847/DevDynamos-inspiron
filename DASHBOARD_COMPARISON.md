# Dashboard Comparison: 834 vs 835

## Quick Reference

| Feature | 834 Dashboard | 835 Dashboard |
|---------|---------------|---------------|
| **Purpose** | Member Enrollment | Payment Remittance |
| **Route** | /dashboard/835 | /dashboard/834 |
| **File Type** | 834 EDI | 835 EDI |
| **Main Focus** | Family groups & members | Claims & payments |
| **Data Source** | `session.memberEnrollmentSummary` | `session.parsed_835` |

---

## 834 Dashboard (Member Enrollment)

### What It Shows:
- **Member enrollment information**
- Family groupings (subscriber + dependents)
- Maintenance types (Addition, Cancellation, Change, Audit)
- Coordination of Benefits (COB) indicators
- Relationship codes

### Key Metrics:
- Total Members
- Family Groups
- Members with COB

### Visual Elements:
- ✅ **Green Badge**: 021 Addition
- 🔴 **Red Badge**: 024 Cancellation
- 🟠 **Orange Badge**: 001 Change
- ⚪ **Gray Badge**: 030 Audit

### Test Data (test_834_comprehensive.txt):
- 7 members total
- 6 family groups
- 2 members with COB
- Mix of additions, cancellations, and changes

---

## 835 Dashboard (Remittance)

### What It Shows:
- **Payment remittance details**
- Claims processing status
- Payment amounts and adjustments
- Patient responsibility
- CARC/RARC adjustment codes

### Key Metrics:
- Total Payment Amount
- Payment Method
- Claims Count
- Total Billed vs Paid

### Visual Elements:
- ✅ **Green**: Processed as Billed (Status 1)
- 🟠 **Orange**: Processed with Adjustments (Status 2)
- 🔴 **Red**: Denied (Status 3)
- ⚪ **Gray**: Secondary Payer (Status 4)

### Test Data (test_835_comprehensive.txt):
- $2,850.00 total payment
- 5 claims
- 2 paid in full, 2 adjusted, 1 denied
- Multiple CARC codes (1, 2, 27, 45)

---

## Integration Architecture

```
User Uploads File
      ↓
Pipeline Detects Type (834 or 835)
      ↓
┌─────────────────┬─────────────────┐
│   834 Files     │   835 Files     │
├─────────────────┼─────────────────┤
│ pyx12 parser    │ parser_835.py   │
│ enrollment      │ remittance      │
│ summary builder │ parser          │
├─────────────────┼─────────────────┤
│ Saves to:       │ Saves to:       │
│ .memberEnroll   │ .parsed_835     │
│ mentSummary     │                 │
└─────────────────┴─────────────────┘
      ↓
Session Context (MongoDB)
      ↓
┌─────────────────┬─────────────────┐
│ Dashboard834    │ Dashboard835    │
│ /dashboard/835  │ /dashboard/834  │
│                 │                 │
│ Shows families  │ Shows claims    │
│ & dependents    │ & adjustments   │
└─────────────────┴─────────────────┘
```

---

## Common Features (Both Dashboards)

✓ Session-based (reads from active session context)
✓ Expandable rows (dependents/adjustments)
✓ Filtering capabilities
✓ Color-coded status indicators
✓ Responsive design
✓ Real-time data display

---

## Unique Features

### 834 Only:
- Family grouping logic
- COB filtering
- Dependent rollup
- Maintenance type badges

### 835 Only:
- Payment information
- Adjustment details
- AI-powered CARC explanations (RAG)
- Patient responsibility tracking
- Claim status breakdown

---

## Testing Commands

### Parse 834 File:
```bash
python test_834_parsing_simple.py
```

### Parse 835 File:
```bash
python test_835_parsing_simple.py
```

### Upload via UI:
1. Start backend: `cd backend && uvicorn app.main:main --reload`
2. Start frontend: `npm run dev`
3. Login and upload test file
4. Navigate to appropriate dashboard

---

## Status

✅ **834 Dashboard**: Fully functional - member enrollment working
✅ **835 Dashboard**: Fully functional - remittance processing working
✅ **Backend Integration**: Pipeline auto-detects and routes correctly
✅ **Frontend Routes**: Both dashboards accessible and displaying data
✅ **RAG Integration**: 240K+ embeddings ready for 835 explanations

**BOTH DASHBOARDS PRODUCTION READY** 🎉
