# Evolish Technologies Pvt. Ltd. policy set

Evolish Technologies Pvt. Ltd. is a fictional company. These policies were written for this academic project and modelled on RBI, DPDP Act 2023 and ISO/IEC 27001 practices.

| Document ID | File | Category |
|---|---|---|
| EV-SEC-001 | `Information_Security_Policy.md` | Security |
| EV-SEC-002 | `Data_Classification_and_Handling_Policy.md` | Privacy |
| EV-SEC-003 | `Access_Control_Policy.md` | Access Control |
| EV-SEC-004 | `Data_Warehouse_and_Analytics_Access_Policy.md` | Access Control |
| EV-SEC-005 | `Acceptable_Use_of_AI_Tools_Policy.md` | Acceptable Use |
| EV-SEC-006 | `Data_Privacy_Policy.md` | Privacy |
| EV-SEC-007 | `HR_and_Employee_Records_Policy.md` | Privacy |
| EV-SEC-008 | `Incident_Response_and_Security_Monitoring_Policy.md` | Security |

Notes for maintainers:

- `scripts/ingest_policies.py` splits each policy on `## ` headings, so every numbered rule is its own heading (for example `## 4.2 Intern access`). A citation such as "Access Control Policy §4.2" refers to that heading.
- The rule-to-citation table is in `app/services/governance.py`. If a clause is renumbered, update the table in the same change.
- This README and the `_old/` folder are not ingested. `_old/` holds the four policies that this set replaced.
- PDF copies for review are in `backend/policies_pdf/`.
