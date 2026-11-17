# Incident Response and Security Monitoring Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-008 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Chief Information Security Officer (CISO) |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy defines how Evolish monitors for security events, scores the risk of requests made to the SecureAI Assistant, investigates suspected misuse and responds to incidents.

## 2. Scope

This policy applies to all Evolish systems and to all employees, interns and contractors in the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments. It covers security incidents of every kind and every request made to the SecureAI Assistant.

## 3. Definitions

- **Security event**: an observed occurrence that may indicate a breach of policy or a threat.
- **Security incident**: a security event that has harmed, or is likely to harm, the confidentiality, integrity or availability of Evolish information or systems.
- **Risk score**: a value from 0.00 to 1.00 that the governance engine gives to each request to the SecureAI Assistant.
- **Threat score**: a value from 0 to 100 that measures the malicious intent of a request.
- **Governance case**: a record opened for Admin review when a user's cumulative risk reaches the configured threshold.
- **Honeypot monitoring**: a controlled investigation, called Ghost Mode in the SecureAI Assistant, in which a suspected user's requests are answered from a decoy environment while their activity is recorded.
- **Audit log**: the tamper-evident record of requests, decisions and administrative actions.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Incident severity levels

4.1.1 Every security incident must be given one of the severity levels below by the Security team.

| Severity | Description | Examples | Response |
|---|---|---|---|
| SEV-1 Critical | Confirmed compromise of Restricted information or outage of payment or lending services | Breach of customer KYC or card data, ransomware in production | Immediate response; CISO and Board Risk Committee informed at once |
| SEV-2 High | Likely compromise of Confidential or Restricted information, or a targeted attack in progress | Stolen credentials in use, confirmed insider data extraction | Response within one hour; CISO informed |
| SEV-3 Medium | Policy breach or attack attempt that was contained by controls | Repeated blocked requests for restricted data, blocked phishing | Response within one working day |
| SEV-4 Low | Minor event with no impact on information or services | Single blocked request, lost and encrypted device recovered | Logged and reviewed in the weekly review |

4.1.2 The severity level must be reviewed when new facts emerge and must be recorded with the reason for any change.

## 4.2 Incident reporting

4.2.1 All staff must report a suspected security incident to the Security team immediately through the security incident channel.

4.2.2 Staff must not investigate an incident themselves, delete evidence or contact the suspected person.

4.2.3 A concern that this policy does not clearly cover must be escalated to the CISO and must not be left unresolved.

## 4.3 Risk levels for AI requests

4.3.1 Every request to the SecureAI Assistant must be given a risk score and a risk level.

4.3.2 A risk score of 0.30 or below is LOW. A risk score above 0.30 and up to 0.70 is MEDIUM. A risk score above 0.70 is HIGH.

4.3.3 Every request must receive one governance decision: allowed, filtered or blocked. A filtered response is answered with masked fields or a caution. A blocked request is restricted and is not answered.

4.3.4 A request that is blocked because the role lacks a permission, or because it asks for information that no role may obtain, must be classified as HIGH risk with a risk score of at least 0.75.

4.3.5 Every HIGH-risk request must raise an alert to Admin role holders.

## 4.4 Risk signal categories

4.4.1 The governance engine must examine every request for the five risk signal categories below. Each category has a weight that sets its contribution to the risk score.

| Category | Examples of signals | Default weight |
|---|---|---|
| Cybersecurity threat language | Hack, exploit, bypass, injection, privilege escalation | 0.6 |
| Malware and attack tooling | Malware, ransomware, keylogger, phishing, brute force | 0.8 |
| Data exfiltration signals | Dump database, export all, extract records, all passwords | 1.0 |
| Sensitive personal data disclosure | Date of birth, home address, passport number, medical record | 0.7 |
| Insider threat indicators | Cover tracks, delete logs, disable monitoring, evade detection | 1.0 |

4.4.2 A request that contains a signal from any category must have its risk score raised.

4.4.3 The rules that prohibit each activity are in the Information Security Policy (EV-SEC-001), clauses 4.6, 4.7 and 4.9, the Data Warehouse and Analytics Access Policy (EV-SEC-004), clause 4.8, and the Data Privacy Policy (EV-SEC-006), clause 4.4.

## 4.5 High-risk intent

4.5.1 Every request to the SecureAI Assistant must be given a threat score from 0 to 100 that reflects the intent of the request and not only the words used.

4.5.2 The threat categories assessed are credential theft, access to private conversations, database exploitation, authentication bypass, unauthorised access, sensitive data extraction, privilege escalation and prompt injection.

4.5.3 A request with a threat score of 40 or more must be restricted for every role, including Admin. It must be classified as HIGH risk and recorded as a security event, and no answer may be generated for it.

4.5.4 A request with a threat score from 30 to 39 may be answered, but the response must carry a caution, and the request must be logged and counted towards the user's cumulative risk.

4.5.5 Covert intent, acting without authorisation, evasion of monitoring, targeting of other users' data and targeting of administrator assets must raise the threat score.

4.5.6 A targeted request that is not a bulk request, made by a role that holds the permission for the data requested, must have its threat score reduced, so that authorised work is not treated as an attack.

4.5.7 Legitimate security work that is restricted by this clause must be referred to the Security team.

## 4.6 Threat alerts

4.6.1 Threat scores are grouped into four levels: low (below 30), medium (30 to 54), high (55 to 79) and critical (80 and above).

4.6.2 A request with a threat score at or above the alert threshold must raise a threat alert and notify Admin role holders. The default alert threshold is 50.

4.6.3 An Admin must review each threat alert and decide whether to dismiss it, open an investigation or escalate it as a security incident.

## 4.7 Cumulative risk and governance cases

4.7.1 The risk scores of a user's MEDIUM-risk and HIGH-risk requests must be added to that user's cumulative risk score. LOW-risk requests must not be counted.

4.7.2 When a user's cumulative risk score reaches the cumulative threshold, a governance case must be opened automatically for Admin review. The default cumulative threshold is 1.50.

4.7.3 A governance case must open with the status "open". The system must not restrict a user by itself when a case is opened.

4.7.4 Only one unresolved governance case may exist for a user at a time.

## 4.8 Governance case handling

4.8.1 A governance case must have one of these statuses: open, under review, warned, restricted, escalated or resolved.

4.8.2 The Admin actions available on a case are review, warn, restrict, restore, escalate, resolve and note. Every action must be recorded with the Admin who took it and the time.

4.8.3 A restriction must be decided by an Admin. A restricted user must not be able to use the SecureAI Assistant until an Admin restores access.

4.8.4 A restriction is temporary and may be reversed by the restore action. The system must not disable an account permanently or end a person's employment. Those decisions belong to HR and management.

4.8.5 The risk events, cited policy clauses and Admin notes of a case must remain visible in the case record.

## 4.9 Investigations and honeypot monitoring

4.9.1 An investigation into suspected misuse may be opened only by an Admin, following a threat alert or a governance case.

4.9.2 An Admin may place a suspected user under honeypot monitoring. While it is active, the user's requests to the SecureAI Assistant must be answered from a controlled decoy environment and must not reach production data or policy sources.

4.9.3 Decoy responses must contain only fictitious information. Real credentials, customer data or employee data must not be used as bait.

4.9.4 Every message exchanged during honeypot monitoring, and every Admin action taken, must be recorded as evidence in the investigation record and in the audit log.

4.9.5 An Admin may pause, resume or end honeypot monitoring and may suspend the user's account. Each of these actions must be recorded.

4.9.6 Honeypot monitoring must be used only for the investigation of a specific suspected user and must end when the investigation is closed. It must not be used for general surveillance of staff.

4.9.7 Evidence from an investigation must be shared only with the CISO, HR and Legal, and must be handled as Restricted information.

## 4.10 Attack simulation

4.10.1 Admin role holders may run simulated attack scenarios to test controls and train reviewers.

4.10.2 Security events created by a simulation must be labelled as simulated and must not be reported as real incidents.

## 4.11 Audit log integrity

4.11.1 Every request to the SecureAI Assistant, every sign-in and sign-out, every failed sign-in and every administrative action, including changes to policies, roles, users and risk configuration, must be recorded in the audit log.

4.11.2 Each audit record must be linked to the record before it by a cryptographic hash, so that any change, deletion or reordering of records can be detected.

4.11.3 No person, including an Admin, may alter or delete an audit record, clear the audit log or disable audit logging.

4.11.4 A request to delete logs, clear audit records, disable monitoring or hide activity must be treated as an insider threat indicator under the Information Security Policy (EV-SEC-001), clause 4.9.

4.11.5 The integrity of the audit log chain must be verified at least once a month, and a verification failure must be handled as a SEV-2 incident.

## 4.12 Audit log retention

4.12.1 Audit log records must be retained for at least five years from the date they are created.

4.12.2 Audit log records must not be deleted when a policy document is updated, disabled or re-indexed. Past decisions must remain recorded with the policy clauses cited at the time.

4.12.3 Audit log records that relate to an open investigation, a regulatory inquiry or legal proceedings must be retained until the matter is closed, even if the five-year period has passed.

4.12.4 Access to the audit log is limited to roles that hold `ai_governance_admin`.

## 4.13 Risk configuration

4.13.1 Risk category weights, the LOW and MEDIUM risk thresholds, the cumulative threshold and the threat alert threshold may be changed only by a role that holds `manage_risk_configuration`.

4.13.2 Every change to the risk configuration must be recorded in the audit log.

4.13.3 A change to the risk configuration must not alter the recorded risk level of past requests.

## 4.14 Decisions without policy evidence

4.14.1 Every blocked request must cite the policy clauses that support the decision.

4.14.2 Where a request is blocked on risk signals alone and no policy clause can be cited, the user must be told that there is insufficient policy evidence for a reliable governance decision, and the case must be referred to an Admin for review.

## 4.15 Incident response lifecycle

4.15.1 Incidents must be handled in these phases: identification, containment, eradication, recovery and post-incident review.

4.15.2 Evidence must be preserved from the moment an incident is identified.

4.15.3 A post-incident review must be completed within ten working days of the closure of a SEV-1 or SEV-2 incident, and its actions must be tracked to completion.

4.15.4 The incident response plan must be tested at least once a year.

## 4.16 Regulatory notification

4.16.1 The CISO and the Head of Risk & Compliance must report cyber security incidents to the RBI and to CERT-In within the timelines those authorities prescribe.

4.16.2 A personal data breach must be notified to the Data Protection Board of India and to affected Data Principals, as required by the Digital Personal Data Protection Act, 2023 and the Data Privacy Policy (EV-SEC-006), clause 4.11.

4.16.3 Only the CISO, the Data Protection Officer and the Head of Risk & Compliance may communicate with regulators about an incident.

## 5. Roles and responsibilities

- **Board Risk Committee**: is informed of SEV-1 incidents and reviews incident trends.
- **Chief Information Security Officer**: owns this policy, leads the response to SEV-1 and SEV-2 incidents and approves investigations.
- **Security team**: monitors alerts, classifies incidents and runs the response.
- **Admin role holders**: review alerts and governance cases, run honeypot monitoring and maintain the risk configuration.
- **Data Protection Officer**: leads the response to personal data breaches.
- **Head of Risk & Compliance**: manages regulatory notification.
- **HR and Legal**: advise on investigations that involve staff.
- **All staff**: report suspected incidents immediately.

## 6. Exceptions

No exception may be granted to clauses 4.5.3, 4.11.3 or 4.12. Any other exception must be approved in writing by the CISO for a fixed period.

## 7. Enforcement

Monitoring under this policy is continuous. Staff who cause an incident through a deliberate breach of policy, who fail to report an incident or who obstruct an investigation may face disciplinary action under the HR disciplinary procedure, up to and including termination of employment or contract.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Data Classification and Handling Policy (EV-SEC-002)
- Access Control Policy (EV-SEC-003)
- Data Warehouse and Analytics Access Policy (EV-SEC-004)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- HR and Employee Records Policy (EV-SEC-007)
- RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023
- Digital Personal Data Protection Act, 2023
- ISO/IEC 27001

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
