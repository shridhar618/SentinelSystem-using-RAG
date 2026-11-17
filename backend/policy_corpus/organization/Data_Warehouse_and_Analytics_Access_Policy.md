# Data Warehouse and Analytics Access Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-004 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Head of Data |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy states who may access the Evolish data warehouse, which holds payment and lending transaction data, and the conditions that apply to that access.

## 2. Scope

This policy applies to the Evolish data warehouse, its raw and analytics zones, the pipelines that load it and every tool that queries it, including the SecureAI Assistant. It applies to all employees, interns and contractors in the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments.

## 3. Definitions

- **Data warehouse**: the central analytical data store of Evolish.
- **Raw transaction data**: unmasked transaction, payment, UPI, loan and customer records as received from production systems.
- **Masked analytics tables**: tables derived from raw data in which direct identifiers have been masked or tokenised.
- **Data owner**: the department head accountable for a dataset. The Head of Data is the data owner of the warehouse unless another owner is recorded.
- **Temporary access**: time-limited access given to a person whose role does not normally hold it.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Warehouse zones

4.1.1 The data warehouse must be divided into a raw zone and an analytics zone.

4.1.2 The raw zone holds raw transaction data and is classified Restricted under the Data Classification and Handling Policy (EV-SEC-002).

4.1.3 The analytics zone holds masked analytics tables and is classified Confidential.

4.1.4 Raw data must not be copied into the analytics zone until it has been masked under clause 4.6.

## 4.2 Raw transaction data

4.2.1 Only the Data Engineer role may access raw transaction data. This access is given by the permission `view_warehouse_raw_data`.

4.2.2 Data Engineers may access raw transaction data only to build, operate and repair data pipelines and masking jobs.

4.2.3 A request to the SecureAI Assistant for raw or unmasked transaction, payment, UPI, loan, customer or warehouse data from a role that does not hold `view_warehouse_raw_data` must be blocked and classified as HIGH risk.

4.2.4 Data Analysts must not access raw transaction data.

## 4.3 Masked analytics tables

4.3.1 Only the Data Engineer and Data Analyst roles may access masked analytics tables. This access is given by the permission `view_warehouse_masked_data`.

4.3.2 Data Analysts must use masked analytics tables only. All analysis, reporting and dashboards must be built on the analytics zone.

4.3.3 A request to the SecureAI Assistant for masked or tokenised tables, or for warehouse tables, datasets or data, from a role that does not hold `view_warehouse_masked_data` must be blocked and classified as HIGH risk.

## 4.4 All other roles

4.4.1 Guest, Intern, Software Engineer, HR, Manager and Supervisor roles, and all roles that receive the default permission set, must not have access to the data warehouse.

4.4.2 Staff in other roles who need figures from the warehouse must request a report from the Data team. They must not be given direct access for this purpose.

## 4.5 Admin accounts

4.5.1 Admin accounts hold `view_warehouse_raw_data` and `view_warehouse_masked_data` because the Admin role holds every permission, as stated in the Access Control Policy (EV-SEC-003), clause 4.10.

4.5.2 Admin role holders must use warehouse permissions only to administer access and investigate incidents. They must not use them for business analysis.

4.5.3 Every use of warehouse permissions by an Admin account must be logged and reviewed by the Head of Data each month.

## 4.6 Masking and tokenisation standard

4.6.1 Aadhaar numbers, PAN numbers, bank account numbers, card numbers, mobile numbers, email addresses and UPI identifiers must be masked or tokenised before data enters the analytics zone.

4.6.2 Masking must be irreversible for analysts. Token mapping tables must be stored in the raw zone only.

4.6.3 Data Engineers must test masking jobs before each release and must report a masking failure as a security incident.

## 4.7 Temporary access

4.7.1 A person whose role does not hold a warehouse permission may be given temporary access only when there is a documented business need.

4.7.2 Temporary access must be approved by both the person's manager and the data owner before it is granted.

4.7.3 Temporary access must expire automatically 30 days after it is granted. Access needed beyond 30 days requires a new request and fresh approval from both approvers.

4.7.4 Temporary access must be limited to the specific tables needed and must be given as masked access unless the data owner records why raw access is necessary.

4.7.5 Temporary access must be given through the access request process as a time-limited change to the user's access. The SecureAI Assistant must not grant temporary access and must evaluate each request against the role assigned to the account at the time of the request.

4.7.6 The Data team must keep a register of all temporary access with the approvers, the tables covered and the expiry date.

## 4.8 Bulk export and extraction

4.8.1 Staff must not export, dump, download or extract bulk records from the data warehouse or any production database, except through an approved and logged data pipeline.

4.8.2 Staff must not ask the SecureAI Assistant to dump a database, export all records, extract records, list a user table or return a full database.

4.8.3 The SecureAI Assistant must treat bulk export and extraction language as a data exfiltration signal that raises the risk score of the request.

4.8.4 A request that shows intent to exploit a database or to extract sensitive data in bulk must be restricted for every role, including Data Engineer and Admin, under the Incident Response and Security Monitoring Policy (EV-SEC-008), clause 4.5.

4.8.5 Warehouse data must not be copied to personal devices, removable media or external services.

## 4.9 Query logging and monitoring

4.9.1 Every query against the data warehouse must be logged with the user, the time and the tables accessed.

4.9.2 Query logs must be retained in line with the Incident Response and Security Monitoring Policy (EV-SEC-008), clause 4.12.

4.9.3 The Data team must review access to the raw zone every month and report unusual access to the Security team.

## 4.10 Re-identification

4.10.1 Staff must not attempt to re-identify individuals from masked analytics tables, whether by joining datasets or by any other method.

4.10.2 Analysis outputs that are shared outside the Data team must be aggregated so that no individual customer can be identified.

## 4.11 Non-production environments

4.11.1 Raw transaction data must not be loaded into development or test environments.

4.11.2 Only masked or synthetic data may be used for development, testing and training of models.

## 4.12 Data residency

4.12.1 Payment system data must be stored in systems located in India, in line with RBI requirements on the storage of payment system data.

4.12.2 Warehouse data must not be transferred outside India without the approval of the Data Protection Officer and the Head of Risk & Compliance.

## 5. Roles and responsibilities

- **Head of Data**: owns this policy, acts as data owner of the warehouse and approves temporary access.
- **Data Engineers**: operate pipelines and masking jobs and protect the raw zone.
- **Data Analysts**: work only on masked analytics tables and report any unmasked data they find in the analytics zone.
- **Managers**: approve temporary access requests for their staff and confirm the business need.
- **Admin role holders**: apply approved access changes and remove expired access.
- **Security team**: monitors warehouse access and investigates unusual activity.

## 6. Exceptions

An exception to this policy must be approved in writing by the Head of Data and the CISO for a fixed period of not more than 30 days. No exception may be granted to clause 4.8.5 or clause 4.11.1.

## 7. Enforcement

Warehouse permissions are enforced by warehouse access controls and by the governance engine of the SecureAI Assistant. Blocked requests are logged and contribute to the user's cumulative risk. A breach of this policy may result in removal of access and disciplinary action under the HR disciplinary procedure.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Data Classification and Handling Policy (EV-SEC-002)
- Access Control Policy (EV-SEC-003)
- Data Privacy Policy (EV-SEC-006)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023
- Digital Personal Data Protection Act, 2023

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
