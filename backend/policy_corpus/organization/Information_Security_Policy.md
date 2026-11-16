# Information Security Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-001 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Chief Information Security Officer (CISO) |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy is the top-level statement of how Evolish protects the confidentiality, integrity and availability of its information and systems. All other security policies of Evolish derive their authority from this document.

## 2. Scope

This policy applies to all employees, interns, contractors and third-party personnel of Evolish across the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments. It covers all information assets owned or processed by Evolish, all systems that store or process them, and every interaction with the SecureAI Assistant, which is the internal AI governance assistant of Evolish.

## 3. Definitions

- **Information asset**: any data, system, application, device or service that has value to Evolish.
- **Credential**: any secret used to prove identity or obtain access, including passwords, login codes, API keys, access tokens, session tokens and private cryptographic keys.
- **SecureAI Assistant**: the internal AI assistant through which staff ask questions about company policy and role-appropriate company information. Every request is evaluated by a governance engine before a response is shown.
- **Security event**: an observed occurrence that may indicate a breach of this policy or a threat to an information asset.
- **ISMS**: the information security management system of Evolish.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Information security management system

4.1.1 Evolish must operate an information security management system aligned with ISO/IEC 27001.

4.1.2 The ISMS must meet the expectations of the RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023, and the personal data safeguards required by the Digital Personal Data Protection Act, 2023 (DPDP Act 2023).

4.1.3 Security risks must be identified, assessed and treated at least once a year, and whenever a material change is made to systems that process payment or lending data.

## 4.2 Governance and oversight

4.2.1 The Board Risk Committee must approve this policy and must review the security posture of Evolish at least twice a year.

4.2.2 The Chief Information Security Officer must own the ISMS and must report material security risks to the Board Risk Committee.

4.2.3 Each department head must ensure that staff in the department follow this policy and complete the required training.

## 4.3 Credentials and secrets

4.3.1 Passwords, login codes, credentials, API keys, access tokens and private keys are Restricted information under the Data Classification and Handling Policy (EV-SEC-002).

4.3.2 Credentials must never be disclosed to another person, written in tickets, chat messages, source code or documents, or entered into any AI tool.

4.3.3 The SecureAI Assistant must not disclose passwords, credentials, API keys or private keys to any role. This prohibition applies to every role, including Admin, and no permission overrides it.

4.3.4 A request to the SecureAI Assistant for a password, credential, API key or private key must be blocked, classified as HIGH risk and recorded in the audit log, whatever justification is given.

4.3.5 Staff who have forgotten a credential must use the approved reset procedure of the IT service desk. They must not ask a colleague or the SecureAI Assistant for it.

4.3.6 Secrets used by applications must be stored only in the approved secrets management system and must be rotated when a person with access leaves the team.

## 4.4 Authentication and passwords

4.4.1 Every user must have a unique account. Shared accounts must not be used.

4.4.2 Multi-factor authentication must be enabled on all systems that hold Confidential or Restricted information.

4.4.3 Passwords must be at least 12 characters long and must not be reused across systems.

4.4.4 Repeated failed sign-in attempts must be rate-limited and logged.

4.4.5 Authentication controls must not be bypassed. The related access rule is in the Access Control Policy (EV-SEC-003), clause 4.17.

## 4.5 Encryption and key management

4.5.1 Confidential and Restricted information must be encrypted in transit and at rest using algorithms approved by the CISO.

4.5.2 Cryptographic keys must be generated, stored and rotated in the approved key management service. Private keys must not leave that service in readable form.

## 4.6 Prohibited security activities

4.6.1 Staff must not attempt to hack, exploit, attack, break into or take over any Evolish system, account, database, server, application or network.

4.6.2 Staff must not attempt to bypass, disable or evade authentication, access controls or security controls.

4.6.3 Staff must not run injection attacks, including SQL injection, against Evolish systems, and must not attempt to dump, drop or export database tables without authorisation.

4.6.4 Staff must not ask the SecureAI Assistant for instructions, code or steps that would help carry out any activity in clauses 4.6.1 to 4.6.3 against Evolish systems.

4.6.5 The SecureAI Assistant must treat exploitation, bypass and attack language as a risk signal. Such requests raise the risk score of the request and, where the request shows high-risk intent, must be restricted for every role under the Incident Response and Security Monitoring Policy (EV-SEC-008), clause 4.5.

## 4.7 Malware and attack tooling

4.7.1 Staff must not create, obtain, store or run malware, ransomware, trojans, rootkits, keyloggers, spyware, botnet software, phishing kits, credential-dumping tools or brute-force tools on Evolish systems.

4.7.2 Staff must not ask the SecureAI Assistant to produce or explain how to deploy such tooling against Evolish or any third party.

4.7.3 The SecureAI Assistant must treat references to malware and attack tooling as a risk signal that raises the risk score of the request.

## 4.8 Authorised security testing

4.8.1 Penetration testing and red-team exercises may be performed only by the Security team or an approved external assessor, under a written scope approved by the CISO.

4.8.2 Authorised testers must not use the SecureAI Assistant to obtain attack instructions against production systems. Legitimate security work that is restricted by the assistant must be raised with the Security team.

4.8.3 Questions asked to learn about or defend against a security threat are permitted. The rule is in the Acceptable Use of AI Tools Policy (EV-SEC-005), clause 4.9.

## 4.9 Logging and monitoring controls

4.9.1 Security logging and monitoring must be enabled on all production systems and on the SecureAI Assistant.

4.9.2 Staff must not delete logs, clear audit records, disable monitoring, turn off logging, hide their activity or attempt to evade detection.

4.9.3 A request to the SecureAI Assistant that refers to covering tracks, deleting logs, clearing audit records or disabling monitoring must be treated as an insider threat indicator and must raise the risk score of the request.

4.9.4 Audit log integrity and retention rules are set out in the Incident Response and Security Monitoring Policy (EV-SEC-008), clauses 4.11 and 4.12.

## 4.10 Endpoint and network security

4.10.1 Company laptops and mobile devices must be encrypted, patched and protected by approved endpoint security software.

4.10.2 Production networks must be segmented from corporate networks. Access to production must pass through approved, logged access paths.

4.10.3 Staff must not connect unapproved devices or removable media to systems that process Restricted information.

## 4.11 Secure development and change management

4.11.1 Changes to production systems must be peer reviewed, tested and approved before release.

4.11.2 Source code must be scanned for vulnerabilities and embedded secrets before it is merged.

4.11.3 Production data must not be copied to development or test environments unless it has been masked under the Data Warehouse and Analytics Access Policy (EV-SEC-004).

## 4.12 Third-party and cloud security

4.12.1 A security assessment must be completed before a third party is given access to Evolish information or systems.

4.12.2 Contracts with service providers must include security, confidentiality, audit and breach notification obligations consistent with RBI outsourcing expectations and the DPDP Act 2023.

## 4.13 Security awareness and training

4.13.1 All staff must complete security awareness training when they join and once every year after that.

4.13.2 Staff in Engineering, Data and Customer Support must complete additional role-based training on handling payment and customer data.

## 4.14 Business continuity and resilience

4.14.1 Critical payment and lending systems must have documented recovery objectives, tested backups and a disaster recovery plan that is tested at least once a year.

## 5. Roles and responsibilities

- **Board Risk Committee**: approves this policy and oversees security risk.
- **Chief Information Security Officer**: owns the ISMS, maintains this policy and reports on compliance.
- **Security team**: operates security controls, monitors alerts and investigates security events.
- **Department heads**: enforce this policy within their departments.
- **Admin role holders**: administer the SecureAI Assistant, its policy sources and its risk configuration.
- **All staff**: follow this policy and report suspected security events without delay.

## 6. Exceptions

An exception to this policy must be requested in writing, risk assessed by the Security team and approved by the CISO for a fixed period of not more than 12 months. No exception may be granted to clause 4.3.3 or clause 4.9.2.

## 7. Enforcement

Compliance is monitored through technical controls, audit logs and internal audit. A breach of this policy may result in removal of access and disciplinary action under the HR disciplinary procedure, up to and including termination of employment or contract. A breach that may be a criminal offence may be reported to the appropriate authorities.

## 8. Related documents

- Data Classification and Handling Policy (EV-SEC-002)
- Access Control Policy (EV-SEC-003)
- Data Warehouse and Analytics Access Policy (EV-SEC-004)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- HR and Employee Records Policy (EV-SEC-007)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023
- Digital Personal Data Protection Act, 2023
- ISO/IEC 27001

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
