# Policy Framework References and Alignment

| Field | Detail |
|---|---|
| Document ID | EV-SEC-009 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Chief Information Security Officer (CISO) |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

This document records the external standards, frameworks and laws that Evolish Technologies Pvt. Ltd. ("Evolish") used as references when writing its security, privacy and AI governance policies (EV-SEC-001 to EV-SEC-008). It shows, clause by clause, which part of each Evolish policy is based on which external source, so that reviewers and auditors can trace every requirement back to a recognised reference.

## 2. Scope

This document covers the eight Evolish policies listed in section 4.1 and the governance controls of the SecureAI Assistant. It does not add new obligations of its own. Where this document and another Evolish policy differ, the other policy prevails.

## 3. Definitions

- **Reference framework**: a published standard, guideline or law that Evolish used as a source when writing a policy.
- **Alignment**: a statement that an Evolish policy clause implements, or is consistent with, a named part of a reference framework. Alignment does not mean that Evolish is certified against that framework.
- **AI RMF**: the NIST Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST AI 100-1.

## 4. Policy statements

The sections below list each reference framework and map its parts to Evolish policy clauses.

## 4.1 Evolish policies covered

| Document ID | Policy |
|---|---|
| EV-SEC-001 | Information Security Policy |
| EV-SEC-002 | Data Classification and Handling Policy |
| EV-SEC-003 | Access Control Policy |
| EV-SEC-004 | Data Warehouse and Analytics Access Policy |
| EV-SEC-005 | Acceptable Use of AI Tools Policy |
| EV-SEC-006 | Data Privacy Policy |
| EV-SEC-007 | HR and Employee Records Policy |
| EV-SEC-008 | Incident Response and Security Monitoring Policy |

## 4.2 Reference frameworks used

| Ref | Framework | Publisher | Used for |
|---|---|---|---|
| R1 | Artificial Intelligence Risk Management Framework (AI RMF 1.0), NIST AI 100-1, January 2023 | National Institute of Standards and Technology (NIST), USA | AI governance, roles, monitoring and incident handling |
| R2 | AI RMF Playbook | NIST | Suggested actions for applying R1 |
| R3 | AI RMF: Generative Artificial Intelligence Profile, NIST AI 600-1, July 2024 | NIST | Risks specific to generative AI assistants |
| R4 | NIST Privacy Framework, Version 1.0, January 2020 | NIST | Privacy risk management and data processing controls |
| R5 | OWASP Top 10 for LLM Applications 2025 | OWASP GenAI Security Project | Security risks of large language model applications |
| R6 | The Digital Personal Data Protection Act, 2023 (No. 22 of 2023) | Government of India | Legal obligations for processing personal data in India |
| R7 | ISO/IEC 27001, Information security management systems | ISO / IEC | Information security management system |
| R8 | RBI Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices, 2023 | Reserve Bank of India | IT governance obligations of a regulated entity |

Copies of R1 to R6 are held in the SecureAI policy corpus (`policy_corpus/external_frameworks/`) and can be searched by the SecureAI Assistant once the policy index is built. R7 and R8 are referenced but not held, because they are not freely redistributable.

## 4.3 NIST AI Risk Management Framework (R1, R2)

| AI RMF subcategory | What it requires | Evolish policy clauses |
|---|---|---|
| GOVERN 1.1 | Legal and regulatory requirements involving AI are understood, managed and documented | EV-SEC-001 §4.1, §4.2; this document |
| GOVERN 1.4 | The risk management process and its outcomes are established through transparent policies, procedures and controls | EV-SEC-005 §4.4, §4.12; EV-SEC-008 §4.3, §4.13 |
| GOVERN 1.5 | Ongoing monitoring and periodic review of the risk management process are planned, with roles defined | EV-SEC-008 §4.6, §4.7; annual review of every policy |
| GOVERN 2.1 | Roles, responsibilities and lines of communication for managing AI risk are documented and clear | Section 5 of every Evolish policy; EV-SEC-003 §4.2 to §4.11 |
| GOVERN 6.1 | Policies address AI risks from third-party entities | EV-SEC-001 §4.12; EV-SEC-005 §4.7 |
| MAP 1.1 | Intended purposes, context-specific laws and deployment settings of the AI system are understood and documented | EV-SEC-005 §4.1 to §4.3 |
| MEASURE 2.7 | AI system security and resilience are evaluated and documented | EV-SEC-008 §4.10; EV-SEC-001 §4.8 |
| MEASURE 2.8 | Risks associated with transparency and accountability are examined and documented | EV-SEC-005 §4.10, §4.11; EV-SEC-008 §4.11, §4.14 |
| MEASURE 2.10 | Privacy risk of the AI system is examined and documented | EV-SEC-006 §4.4, §4.15 |
| MANAGE 2.4 | Mechanisms exist to supersede, disengage or deactivate AI use that performs outside intended use | EV-SEC-008 §4.7, §4.8 (restriction of a user's AI access through a governance case) |
| MANAGE 4.1 | Post-deployment monitoring plans are implemented, including capture of user input and incident response | EV-SEC-005 §4.11; EV-SEC-008 §4.6, §4.9 |
| MANAGE 4.3 | Incidents and errors are communicated, tracked, responded to and recovered from | EV-SEC-008 §4.2, §4.15 |

## 4.4 NIST Generative AI Profile (R3)

| GAI risk (NIST AI 600-1, section 2) | Evolish control |
|---|---|
| 2. Confabulation | EV-SEC-005 §4.10 (human accountability for AI output); EV-SEC-008 §4.14 (no decision without policy evidence) |
| 4. Data Privacy | EV-SEC-002 §4.12 (masking in AI responses); EV-SEC-006 §4.4; EV-SEC-007 §4.8 |
| 7. Human-AI Configuration | EV-SEC-005 §4.10; EV-SEC-008 §4.8 (humans decide consequences) |
| 9. Information Security | EV-SEC-005 §4.5 (prompt injection); EV-SEC-001 §4.6, §4.7 |
| 12. Value Chain and Component Integration | EV-SEC-001 §4.12; EV-SEC-005 §4.7 |

## 4.5 NIST Privacy Framework (R4)

| Privacy Framework category | Evolish policy clauses |
|---|---|
| ID.IM-P Inventory and Mapping | EV-SEC-002 §4.1, §4.6; EV-SEC-007 §4.1 |
| ID.RA-P Risk Assessment | EV-SEC-006 §4.15 (privacy impact assessment) |
| GV.PO-P Governance Policies, Processes, and Procedures | EV-SEC-006 sections 4 and 5 |
| GV.AT-P Awareness and Training | EV-SEC-001 §4.13 |
| GV.MT-P Monitoring and Review | EV-SEC-004 §4.9; EV-SEC-008 §4.11 |
| CT.PO-P Data Processing Policies, Processes, and Procedures | EV-SEC-006 §4.1, §4.3 |
| CT.DM-P Data Processing Management | EV-SEC-006 §4.6, §4.9; EV-SEC-002 §4.14 |
| CT.DP-P Disassociated Processing | EV-SEC-004 §4.3, §4.6, §4.10 (masking, tokenisation, no re-identification) |
| CM.AW-P Data Processing Awareness | EV-SEC-006 §4.2 (notice) |
| PR.AC-P Identity Management, Authentication, and Access Control | EV-SEC-003 §4.1, §4.17, §4.18 |
| PR.DS-P Data Security | EV-SEC-001 §4.5; EV-SEC-002 §4.8 |

## 4.6 OWASP Top 10 for LLM Applications 2025 (R5)

| OWASP risk | Evolish control |
|---|---|
| LLM01:2025 Prompt Injection | EV-SEC-005 §4.5; EV-SEC-008 §4.5 |
| LLM02:2025 Sensitive Information Disclosure | EV-SEC-002 §4.12, §4.13; EV-SEC-003 §4.13; EV-SEC-007 §4.8 |
| LLM03:2025 Supply Chain | EV-SEC-001 §4.12 |
| LLM04:2025 Data and Model Poisoning | EV-SEC-001 §4.11 (production changes are peer reviewed and tested before release) |
| LLM05:2025 Improper Output Handling | EV-SEC-002 §4.12 (responses are masked before display) |
| LLM06:2025 Excessive Agency | EV-SEC-003 §4.1, §4.19 (the assistant cannot grant access; only the role's effective permissions apply) |
| LLM07:2025 System Prompt Leakage | EV-SEC-005 §4.5; EV-SEC-001 §4.3 (credentials must never be entered into any AI tool) |
| LLM08:2025 Vector and Embedding Weaknesses | EV-SEC-003 §4.13 (role-to-data access matrix applies to every answer) |
| LLM09:2025 Misinformation | EV-SEC-005 §4.10; EV-SEC-008 §4.14 |

## 4.7 Digital Personal Data Protection Act, 2023 (R6)

| DPDP Act provision | Evolish policy clauses |
|---|---|
| Section 4 (grounds for processing personal data) and section 6 (consent) | EV-SEC-006 §4.1 |
| Section 5 (notice) | EV-SEC-006 §4.2 |
| Section 7(i) (legitimate use for purposes of employment) | EV-SEC-007 §4.1 to §4.3 |
| Section 8(2) (Data Processors only under a valid contract) | EV-SEC-006 §4.13 |
| Section 8(5) (reasonable security safeguards) | EV-SEC-006 §4.10; EV-SEC-001 §4.5 |
| Section 8(6) (intimation of personal data breach to the Board and each affected Data Principal) | EV-SEC-006 §4.11; EV-SEC-008 §4.16 |
| Section 8(7) (erasure when the purpose is no longer served) | EV-SEC-006 §4.9; EV-SEC-007 §4.11 |
| Section 8(10) (grievance redressal mechanism) and section 13 | EV-SEC-006 §4.7 |
| Section 9 (personal data of children) | EV-SEC-006 §4.12 |
| Section 11 (right to access information) and section 12 (correction and erasure) | EV-SEC-006 §4.6; EV-SEC-007 §4.5 |
| Section 16 (transfer of personal data outside India) | EV-SEC-006 §4.14; EV-SEC-004 §4.12 |

## 4.8 Known gaps

The following parts of the reference frameworks are not yet covered by a dedicated Evolish policy clause. They are recorded here so they are addressed at the next policy review.

| Reference | Gap |
|---|---|
| NIST AI 600-1, risk 11 (Obscene, Degrading, and/or Abusive Content) | No clause addresses abusive or offensive language sent to the SecureAI Assistant. |
| OWASP LLM10:2025 Unbounded Consumption | No clause sets limits on the volume or rate of requests a user may send to the SecureAI Assistant. |

## 4.9 ISO/IEC 27001 and RBI Master Direction (R7, R8)

EV-SEC-001 §4.1 requires Evolish to operate an information security management system aligned with ISO/IEC 27001 and meeting the RBI Master Direction on IT Governance, Risk, Controls and Assurance Practices, 2023. EV-SEC-003, EV-SEC-004, EV-SEC-005 and EV-SEC-008 also list these as related documents.

## 5. Roles and responsibilities

- **CISO**: owns this document and keeps the mappings current when a reference framework or an Evolish policy changes.
- **Data Protection Officer**: confirms the DPDP Act mappings in section 4.7.
- **Policy owners**: tell the CISO when a clause cited here is renumbered or removed.

## 6. Exceptions

This document grants no exceptions. Exceptions to a policy are handled under section 6 of that policy.

## 7. Enforcement

This document is informative. Obligations are enforced through the policies it references.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Data Classification and Handling Policy (EV-SEC-002)
- Access Control Policy (EV-SEC-003)
- Data Warehouse and Analytics Access Policy (EV-SEC-004)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- HR and Employee Records Policy (EV-SEC-007)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- NIST AI 100-1, NIST AI RMF Playbook, NIST AI 600-1, NIST Privacy Framework 1.0
- OWASP Top 10 for LLM Applications 2025
- Digital Personal Data Protection Act, 2023

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 18 November 2026 | First issue | Board Risk Committee |
