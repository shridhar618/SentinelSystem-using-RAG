# Data Classification and Handling Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-002 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Chief Information Security Officer (CISO) |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy defines the four classification levels that Evolish applies to its information and the handling rules for each level, including how classified information is treated by the SecureAI Assistant.

## 2. Scope

This policy applies to all information created, received, stored or processed by Evolish in any form, and to all employees, interns, contractors and third parties in the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments who handle it.

## 3. Definitions

- **Information owner**: the department head accountable for a set of information and for its classification.
- **Personal data**: any data about an individual who is identifiable by or in relation to that data, as defined in the Digital Personal Data Protection Act, 2023 (DPDP Act 2023).
- **KYC documents**: identity and address documents collected from customers to meet know-your-customer obligations.
- **Masking**: replacing all or part of a value so that the original value cannot be read.
- **SecureAI Assistant**: the internal AI governance assistant of Evolish.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Classification levels

4.1.1 All Evolish information must be classified as one of four levels: Public, Internal, Confidential or Restricted.

4.1.2 Information that has not been classified must be handled as Internal until its owner classifies it.

4.1.3 Where information of different levels is combined, the combined information must take the highest level present.

## 4.2 Public information

4.2.1 Public information is information that Evolish has published or approved for release, such as product descriptions, published fees, office hours and press releases.

4.2.2 Public information may be shared with anyone and may be returned by the SecureAI Assistant to every role that holds `view_public_information`.

## 4.3 Internal information

4.3.1 Internal information is intended for Evolish staff and not for the public. Examples are internal procedures, project descriptions, project status and organisation charts.

4.3.2 Internal information must not be shared outside Evolish without the approval of the information owner.

4.3.3 Project information is Internal. A limited view (purpose, status, milestones and team size) may be given to roles that hold `view_project_information_limited`. The full technical view (architecture, data stores, environments and technical risks) may be given only to roles that hold `view_project_information_full`.

4.3.4 Content marked internal-only must not be requested through the SecureAI Assistant by Intern accounts. The access rule is in the Access Control Policy (EV-SEC-003), clause 4.2.

## 4.4 Confidential information

4.4.1 Confidential information is information whose unauthorised disclosure could harm Evolish, its staff or its customers. Examples are employee personal records, proprietary source code, proprietary business information, contracts and masked analytics tables.

4.4.2 Confidential information must be shared only with people who need it for their role.

4.4.3 Employee personal records may be returned by the SecureAI Assistant only to roles that hold `view_employee_pii`.

4.4.4 Content marked confidential or proprietary must not be requested through the SecureAI Assistant by Intern accounts. The access rule is in the Access Control Policy (EV-SEC-003), clause 4.2.

## 4.5 Restricted information

4.5.1 Restricted is the highest classification level. Unauthorised disclosure of Restricted information could cause severe financial, legal or regulatory harm to Evolish or its customers.

4.5.2 Restricted information includes Aadhaar and PAN numbers, KYC documents, payment card data, bank account details, raw transaction logs, salary and payroll records, credentials, cryptographic keys, and any content marked secret or classified.

4.5.3 Restricted information must be accessed only by the roles named in the policy that governs it, and every access must be logged.

4.5.4 Credentials are Restricted information that no role may obtain through the SecureAI Assistant. The rule is in the Information Security Policy (EV-SEC-001), clause 4.3.

4.5.5 Content marked secret or classified must not be requested through the SecureAI Assistant by Intern accounts. The access rule is in the Access Control Policy (EV-SEC-003), clause 4.2.

## 4.6 Classification examples

4.6.1 The table below classifies common Evolish data types. Information owners must apply it when classifying their information.

| Data type | Classification | Governing rule |
|---|---|---|
| Product descriptions, published fees, office hours | Public | Clause 4.2 |
| Internal procedures, project status and milestones | Internal | Clause 4.3 |
| Technical architecture of internal projects | Internal (full technical view) | Clause 4.3.3 |
| Employee contact details, home address, date of birth | Confidential | HR and Employee Records Policy, clause 4.3 |
| Source code | Confidential | Clause 4.11 |
| Masked analytics tables | Confidential | Data Warehouse and Analytics Access Policy, clause 4.3 |
| Salary and payroll records | Restricted | HR and Employee Records Policy, clause 4.2 |
| Aadhaar and PAN numbers | Restricted | Clause 4.9 |
| KYC documents | Restricted | Clause 4.9 |
| Payment card data and bank account details | Restricted | Clause 4.10 |
| Raw transaction logs | Restricted | Data Warehouse and Analytics Access Policy, clause 4.2 |
| Passwords, API keys, private keys and other credentials | Restricted | Information Security Policy, clause 4.3 |

## 4.7 Labelling and ownership

4.7.1 Every information asset must have a named information owner.

4.7.2 Documents classified Confidential or Restricted must carry the classification label on the first page or in the file properties.

4.7.3 Information owners must review the classification of their information at least once a year.

## 4.8 Handling requirements by level

4.8.1 Information must be handled according to the table below.

| Requirement | Public | Internal | Confidential | Restricted |
|---|---|---|---|---|
| Storage | Any approved system | Evolish systems only | Access-controlled Evolish systems | Encrypted, access-controlled systems with logging |
| Transmission | No restriction | Evolish channels | Encrypted channels | Encrypted channels, named recipients only |
| Sharing outside Evolish | Permitted | Owner approval | Owner approval and a confidentiality agreement | Not permitted except where required by law or regulator |
| Printing | Permitted | Permitted | Only when necessary | Not permitted without CISO approval |
| Disposal | No restriction | Delete | Secure deletion | Secure deletion with a disposal record |

## 4.9 Government-issued identifiers

4.9.1 Aadhaar numbers, PAN numbers, passport numbers and KYC documents are Restricted information. Foreign national identifiers, such as Social Security Numbers, are treated in the same way.

4.9.2 Government-issued identifiers must be stored only in the approved KYC and customer systems, and must be masked wherever they are displayed, in line with the DPDP Act 2023 and applicable RBI and UIDAI requirements.

4.9.3 The SecureAI Assistant must not disclose Aadhaar numbers, PAN details or Social Security Numbers to any role. A request for them must be blocked for every role, including Admin, and classified as HIGH risk.

4.9.4 Staff must not enter government-issued identifiers or KYC documents into the SecureAI Assistant or any other AI tool.

## 4.10 Payment card and bank account data

4.10.1 Payment card numbers, card security codes (CVV), UPI PINs and bank account details are Restricted information.

4.10.2 Card security codes and UPI PINs must never be stored by Evolish after authorisation and must never be requested from a customer by staff.

4.10.3 The SecureAI Assistant must not disclose credit card data, card security codes, UPI PINs or bank account information to any role. A request for them must be blocked for every role, including Admin, and classified as HIGH risk.

## 4.11 Source code

4.11.1 Evolish source code is Confidential and proprietary information.

4.11.2 Source code must be stored only in the approved source code repositories and must not be uploaded to personal accounts or to external AI tools.

4.11.3 Source code must not contain credentials. The rule is in the Information Security Policy (EV-SEC-001), clause 4.3.

## 4.12 Masking in AI assistant responses

4.12.1 Responses returned by the SecureAI Assistant to the HR role must be masked before display, because HR is the role that holds both employee personal data and salary permissions.

4.12.2 The following fields must be masked in an HR response unless the request asked for that field: email addresses, phone numbers and salary or financial figures.

4.12.3 The following fields must always be masked in an HR response: identifier-format numbers such as Social Security Numbers, payment card numbers and passwords written in the text.

4.12.4 A masked value must be replaced by a marker that names the field type, for example `[EMAIL REDACTED]` or `[AMOUNT REDACTED]`.

4.12.5 A response in which a field has been masked must be recorded with the decision "filtered", and the user must be told which field types were masked.

4.12.6 A user who needs the unmasked value for an authorised purpose must obtain it from the system of record and must not ask the SecureAI Assistant again.

## 4.13 Minimum necessary disclosure

4.13.1 A response must contain only the fields that the request needs. A full record must not be returned when one field was asked for.

4.13.2 When an authorised role asks for an employee's contact details, the SecureAI Assistant must return only the contact fields requested and must not include salary.

4.13.3 Eligibility by role does not remove the duty in clause 4.13.1. A role that may see a field must still receive it only when it is relevant to the request.

## 4.14 Retention and disposal

4.14.1 Information must be kept only for as long as it is needed for its purpose or required by law or regulation, and must then be disposed of under clause 4.8.

4.14.2 Retention of personal data is governed by the Data Privacy Policy (EV-SEC-006), clause 4.9. Retention of audit logs is governed by the Incident Response and Security Monitoring Policy (EV-SEC-008), clause 4.12.

## 4.15 Transfer outside Evolish

4.15.1 Confidential and Restricted information must not be sent to personal email accounts, personal cloud storage or unapproved messaging applications.

4.15.2 Confidential and Restricted information must not be submitted to external AI tools. The rule is in the Acceptable Use of AI Tools Policy (EV-SEC-005), clause 4.7.

## 5. Roles and responsibilities

- **Chief Information Security Officer**: owns this policy and approves handling standards.
- **Information owners**: classify their information, approve sharing and review classification every year.
- **Data Protection Officer**: advises on the classification and handling of personal data.
- **Admin role holders**: maintain the masking and blocking rules of the SecureAI Assistant in line with this policy.
- **All staff**: handle information according to its classification and report mishandling.

## 6. Exceptions

An exception must be requested in writing by the information owner and approved by the CISO for a fixed period. No exception may be granted to clauses 4.9.3, 4.10.2 or 4.10.3.

## 7. Enforcement

Compliance is monitored through data loss prevention controls, access logs, the audit log of the SecureAI Assistant and internal audit. A breach of this policy may result in removal of access and disciplinary action under the HR disciplinary procedure.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Access Control Policy (EV-SEC-003)
- Data Warehouse and Analytics Access Policy (EV-SEC-004)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- HR and Employee Records Policy (EV-SEC-007)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- Digital Personal Data Protection Act, 2023
- ISO/IEC 27001

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
