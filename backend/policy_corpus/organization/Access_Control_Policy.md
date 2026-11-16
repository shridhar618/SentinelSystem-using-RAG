# Access Control Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-003 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Chief Information Security Officer (CISO) |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy defines the roles used at Evolish, the permissions attached to each role and the data each role may access, including through the SecureAI Assistant.

## 2. Scope

This policy applies to every account provisioned in Evolish systems for employees, interns, contractors and guests in the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments, and to every request made to the SecureAI Assistant.

## 3. Definitions

- **Role**: a named set of permissions assigned to a user account.
- **Permission**: a specific right to view a category of information or perform an administrative action.
- **Least privilege**: giving a role only the permissions it needs for its function.
- **Governed roles**: the nine roles defined in clauses 4.2 to 4.10: Guest, Intern, Software Engineer, HR, Manager, Supervisor, Data Engineer, Data Analyst and Admin.
- **SecureAI Assistant**: the internal AI governance assistant of Evolish.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Least privilege and unauthorised access

4.1.1 Access to Evolish information must be granted on the principles of least privilege and need to know, consistent with ISO/IEC 27001 and the RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023.

4.1.2 A role must not be given a permission that its function does not need.

4.1.3 Any attempt to access information, an account, a system or an administrative area outside the permissions of the user's role is unauthorised access.

4.1.4 Users must not access, or attempt to access, the accounts, data, files, records or dashboards of other users.

4.1.5 The SecureAI Assistant must restrict a request that shows intent to gain unauthorised access, for every role, under the Incident Response and Security Monitoring Policy (EV-SEC-008), clause 4.5.

## 4.2 Intern access

4.2.1 The Intern role is granted `view_public_information`, `view_project_information_limited` and `use_ai_assistant`.

4.2.2 Interns must not be granted `view_employee_pii` or `view_employee_salary`, whatever project they are assigned to.

4.2.3 Interns may view the limited view of project information. Interns must not receive the full technical view of a project.

4.2.4 Interns must not request content that is secret, confidential, proprietary, internal-only or classified through the SecureAI Assistant.

4.2.5 The SecureAI Assistant must block a request from an Intern account that asks for secret, confidential, proprietary, internal-only or classified content, and must classify the request as HIGH risk.

4.2.6 Interns must not have access to the data warehouse.

## 4.3 Guest access

4.3.1 The Guest role is granted `view_public_information` only.

4.3.2 Guests must not use the SecureAI Assistant. A Guest request to the assistant must be denied and recorded as a permission denial.

4.3.3 Guests must not have access to project, employee, salary, customer or warehouse data.

## 4.4 Software Engineer access

4.4.1 The Software Engineer role is granted `view_public_information`, `view_project_information_full` and `use_ai_assistant`.

4.4.2 Software Engineers may view the full technical view of project information.

4.4.3 Software Engineers must not have access to employee personal records, salary records or the data warehouse.

## 4.5 HR access

4.5.1 The HR role is granted `view_public_information`, `view_project_information_limited`, `view_employee_pii`, `view_employee_salary` and `use_ai_assistant`.

4.5.2 HR may view employee personal records and salary records for HR purposes, subject to the HR and Employee Records Policy (EV-SEC-007).

4.5.3 HR must not receive the full technical view of a project and must not have access to the data warehouse.

4.5.4 Responses to the HR role are masked under the Data Classification and Handling Policy (EV-SEC-002), clause 4.12.

## 4.6 Manager access

4.6.1 The Manager role is granted `view_public_information`, `view_project_information_full`, `view_employee_pii` and `use_ai_assistant`.

4.6.2 Managers may view employee personal records. Managers must use this access only for employees who report to them, as required by the HR and Employee Records Policy (EV-SEC-007), clause 4.4.

4.6.3 Managers must not be granted `view_employee_salary`. Salary review is an HR function.

4.6.4 Managers must not have access to the data warehouse.

## 4.7 Supervisor access

4.7.1 The Supervisor role is granted `view_public_information`, `view_project_information_full` and `use_ai_assistant`.

4.7.2 Supervisors must not have access to employee personal records, salary records or the data warehouse.

## 4.8 Data Engineer access

4.8.1 The Data Engineer role is granted `view_public_information`, `view_project_information_full`, `use_ai_assistant`, `view_warehouse_masked_data` and `view_warehouse_raw_data`.

4.8.2 Data Engineers may access raw transaction data and masked analytics tables in the data warehouse, subject to the Data Warehouse and Analytics Access Policy (EV-SEC-004).

4.8.3 Data Engineers must not have access to employee personal records or salary records.

## 4.9 Data Analyst access

4.9.1 The Data Analyst role is granted `view_public_information`, `view_project_information_limited`, `use_ai_assistant` and `view_warehouse_masked_data`.

4.9.2 Data Analysts may access masked analytics tables only. Data Analysts must not be granted `view_warehouse_raw_data` and must not access raw transaction data.

4.9.3 Data Analysts must not have access to employee personal records or salary records, and must not receive the full technical view of a project.

## 4.10 Admin access

4.10.1 The Admin role is granted every permission in the permission catalogue in clause 4.12.

4.10.2 Admin access must be limited to named staff responsible for governance and system administration, and every Admin action must be recorded in the audit log.

4.10.3 Admin permissions do not override the absolute prohibitions on credentials, government-issued identifiers and payment data. Those requests must be blocked for Admin as for every other role.

4.10.4 Admin accounts hold the warehouse permissions for administration only. Their use is limited by the Data Warehouse and Analytics Access Policy (EV-SEC-004), clause 4.5.

## 4.11 Other roles

4.11.1 A role that is not one of the governed roles, such as Developer, Finance, Sales, Operations or Support Engineer, must receive the default permission set: `view_public_information`, `view_project_information_limited` and `use_ai_assistant`.

4.11.2 A role must not be treated as trusted because it has no explicit mapping. Additional permissions must be added to the role mapping by an Admin before they take effect.

## 4.12 Permission catalogue

4.12.1 The permissions below are the only permissions recognised by the SecureAI Assistant.

| Permission | What it allows |
|---|---|
| `view_public_information` | View public and non-sensitive company information |
| `view_project_information_limited` | View the limited view of project information |
| `view_project_information_full` | View the full technical view of project information |
| `view_employee_pii` | View authorised employee personal information |
| `view_employee_salary` | View employee salary and compensation information |
| `view_warehouse_masked_data` | View masked analytics tables in the data warehouse |
| `view_warehouse_raw_data` | View raw transaction data in the data warehouse |
| `use_ai_assistant` | Use the SecureAI Assistant |
| `ai_governance_admin` | View audit logs, risk events and governance cases |
| `manage_policies` | Upload, re-index, enable and disable policy documents |
| `manage_risk_configuration` | Edit risk engine weights and thresholds |
| `manage_users` | Create users and assign roles |
| `system_configuration_admin` | Change system-wide configuration |

## 4.13 Role-to-data access matrix

4.13.1 The matrix below states what each governed role may access. "Yes" means the role holds the permission. "No" means a request must be refused.

| Data category | Guest | Intern | Software Engineer | HR | Manager | Supervisor | Data Engineer | Data Analyst | Admin |
|---|---|---|---|---|---|---|---|---|---|
| Public information | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Use of the SecureAI Assistant | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Project information, limited view | No | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Project information, full technical view | No | No | Yes | No | Yes | Yes | Yes | No | Yes |
| Employee personal records | No | No | No | Yes | Yes | No | No | No | Yes |
| Salary and compensation records | No | No | No | Yes | No | No | No | No | Yes |
| Masked analytics tables | No | No | No | No | No | No | Yes | Yes | Yes |
| Raw transaction data | No | No | No | No | No | No | Yes | No | Yes |
| Audit logs, risk events and governance cases | No | No | No | No | No | No | No | No | Yes |
| Policy, risk and user administration | No | No | No | No | No | No | No | No | Yes |
| Credentials, API keys and private keys | No | No | No | No | No | No | No | No | No |
| Aadhaar, PAN, card and bank account data through the assistant | No | No | No | No | No | No | No | No | No |

4.13.2 A role that holds the full technical view of project information also holds the limited view.

4.13.3 Roles not listed in the matrix follow clause 4.11.

## 4.14 Salary and compensation access

4.14.1 Only the HR and Admin roles hold `view_employee_salary`.

4.14.2 A request to the SecureAI Assistant for salary, compensation, pay scale or payroll data from a role that does not hold `view_employee_salary` must be blocked and classified as HIGH risk.

4.14.3 Detailed rules for salary records are in the HR and Employee Records Policy (EV-SEC-007), clause 4.2.

## 4.15 Employee personal data access

4.15.1 Only the HR, Manager and Admin roles hold `view_employee_pii`.

4.15.2 A request to the SecureAI Assistant for personal data, contact details, home addresses, dates of birth or employee records from a role that does not hold `view_employee_pii` must be blocked and classified as HIGH risk.

4.15.3 Detailed rules for employee personal records are in the HR and Employee Records Policy (EV-SEC-007), clause 4.3.

## 4.16 Privilege changes

4.16.1 A role or permission may be changed only by an Admin through the user management function, on an approved access request.

4.16.2 Users must not ask the SecureAI Assistant to change their role, grant them administrator, root or elevated access, or escalate their privileges.

4.16.3 The SecureAI Assistant must not change any role or permission. A request to do so must be restricted for every role as a privilege escalation attempt and recorded as a security event.

4.16.4 Every change to a role or a role-to-permission mapping must be recorded in the audit log.

## 4.17 Authentication controls

4.17.1 Users must not bypass, disable or evade sign-in, multi-factor authentication, verification or session controls.

4.17.2 Users must not forge, steal, replay or tamper with tokens, sessions or cookies, and must not impersonate another user.

4.17.3 The SecureAI Assistant must restrict a request that seeks to bypass authentication, for every role, and record it as a security event.

## 4.18 Provisioning, review and removal of access

4.18.1 Access must be requested through the access request process and approved by the user's manager before it is granted.

4.18.2 Role assignments must be reviewed by department heads every quarter, and unneeded access must be removed.

4.18.3 Access must be removed on the last working day of a leaver, and reviewed within five working days when a person changes role.

4.18.4 A user whose governance case has the status "restricted" must not be able to use the SecureAI Assistant until an Admin restores access.

## 4.19 Effective permissions

4.19.1 The permissions of a user are those of the role assigned to the account at the time of the request. A role previously held, a job title or a stated justification must not be treated as granting a permission.

4.19.2 Temporary access must be given by a time-limited change to the user's access through the access request process, and not by the SecureAI Assistant.

## 5. Roles and responsibilities

- **Chief Information Security Officer**: owns this policy and the role catalogue.
- **Admin role holders**: create users, assign roles and maintain role-to-permission mappings.
- **Department heads and managers**: approve access requests and carry out quarterly access reviews.
- **Data owners**: approve access to the data they own.
- **All users**: use only the access they have been given and report access they should not have.

## 6. Exceptions

An exception must be requested through the access request process, approved by the user's manager, the relevant data owner and the CISO, and must be time-limited. No exception may be granted to clause 4.10.3.

## 7. Enforcement

Access rules are enforced by the governance engine of the SecureAI Assistant and by system access controls. Blocked and restricted requests are logged and contribute to the user's cumulative risk under the Incident Response and Security Monitoring Policy (EV-SEC-008). A breach of this policy may result in removal of access and disciplinary action.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Data Classification and Handling Policy (EV-SEC-002)
- Data Warehouse and Analytics Access Policy (EV-SEC-004)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- HR and Employee Records Policy (EV-SEC-007)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023
- ISO/IEC 27001

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
