# HR and Employee Records Policy

| Field | Detail |
|---|---|
| Document ID | EV-SEC-007 |
| Version | 1.0 |
| Effective date | 1 November 2026 |
| Next review date | 1 November 2027 |
| Owner | Head of Human Resources |
| Approved by | Board Risk Committee |
| Classification | Internal |

## 1. Purpose

Evolish Technologies Pvt. Ltd. ("Evolish") is a Bengaluru-based financial technology company that provides digital payments on the Unified Payments Interface (UPI) and small personal loans. Evolish has about 300 employees and is regulated by the Reserve Bank of India (RBI).

This policy states who may see salary records and employee personal records at Evolish, and how those records must be handled, including when they are requested through the SecureAI Assistant.

## 2. Scope

This policy applies to the records of all current and former employees, interns, contractors and job applicants of Evolish, and to everyone in the Engineering, Data, HR, Finance, Risk & Compliance and Customer Support departments who can access them.

## 3. Definitions

- **Employee personal records**: personal information about an employee, including contact details, home address, date of birth, joining date, job title, reporting line and role history.
- **Salary records**: salary, compensation, pay scale, payroll, stipend and bonus information about an employee.
- **HRMS**: the human resources management system, which is the system of record for employee data.
- **Direct report**: an employee who reports to a manager in the HRMS reporting line.
- **SecureAI Assistant**: the internal AI governance assistant of Evolish.

## 4. Policy statements

The numbered clauses below are the binding requirements of this policy.

## 4.1 Employee record categories

4.1.1 Employee personal records are classified Confidential under the Data Classification and Handling Policy (EV-SEC-002).

4.1.2 Salary records are classified Restricted.

4.1.3 Employee records are personal data and must be processed in line with the Data Privacy Policy (EV-SEC-006) and the Digital Personal Data Protection Act, 2023 (DPDP Act 2023).

## 4.2 Salary and compensation records

4.2.1 Only the HR and Admin roles may view salary records. This access is given by the permission `view_employee_salary`.

4.2.2 Guest, Intern, Software Engineer, Manager, Supervisor, Data Engineer and Data Analyst roles, and all roles that receive the default permission set, must not view the salary of any other employee.

4.2.3 Managers must not view the salary of their direct reports through the SecureAI Assistant. Managers who need compensation information for a review must obtain it from HR.

4.2.4 A request to the SecureAI Assistant for salary, compensation, pay scale or payroll data from a role that does not hold `view_employee_salary` must be blocked and classified as HIGH risk.

4.2.5 HR must use salary records only for an authorised HR or payroll purpose. Curiosity is not an authorised purpose.

4.2.6 Finance staff who process payroll must do so in the payroll system under its own access controls, and must not obtain salary records through the SecureAI Assistant.

## 4.3 Employee personal records

4.3.1 Only the HR, Manager and Admin roles may view employee personal records. This access is given by the permission `view_employee_pii`.

4.3.2 Guest, Intern, Software Engineer, Supervisor, Data Engineer and Data Analyst roles, and all roles that receive the default permission set, must not view employee personal records.

4.3.3 A request to the SecureAI Assistant for the phone number, mobile number or contact details of an employee, a home address, a date of birth, employee records, an employee directory or personal details, from a role that does not hold `view_employee_pii`, must be blocked and classified as HIGH risk.

4.3.4 When an authorised role asks for employee personal records, the SecureAI Assistant must return only the fields asked for, as required by the Data Classification and Handling Policy (EV-SEC-002), clause 4.13.

## 4.4 Manager access

4.4.1 Managers hold `view_employee_pii` so that they can contact and manage their teams.

4.4.2 Managers must use this access only for their direct reports and only for a management purpose.

4.4.3 The SecureAI Assistant checks the Manager role and not the reporting line. Use of the access for employees who are not direct reports is a breach of this policy and is detected through review of the audit log.

## 4.5 Access to one's own records

4.5.1 Every employee may view their own personal and salary records through the self-service function of the HRMS.

4.5.2 The SecureAI Assistant does not verify whose record is requested. Employees must use the HRMS, and not the SecureAI Assistant, to view their own salary.

## 4.6 Home address and date of birth

4.6.1 Home addresses and dates of birth must not be provided through the SecureAI Assistant to any role, including roles that hold `view_employee_pii`.

4.6.2 An authorised role that needs a home address or a date of birth must obtain it from the HRMS and must record the purpose.

## 4.7 Targeted and bulk requests

4.7.1 A targeted request by an authorised role for the record of a specific employee is a normal use of that role's permission. The SecureAI Assistant must not treat it as an attack.

4.7.2 A request for the records of all or many employees, or a request to export, dump or download records, must be restricted for every role, including HR and Admin, under the Data Privacy Policy (EV-SEC-006), clause 4.16.

4.7.3 Bulk reports of employee data must be produced from the HRMS under the approval of the Head of Human Resources.

## 4.8 Masking of HR responses

4.8.1 Responses returned to the HR role by the SecureAI Assistant must be masked under the Data Classification and Handling Policy (EV-SEC-002), clause 4.12.

4.8.2 Salary figures, email addresses and phone numbers must be masked in a response to HR unless the request asked for that field.

## 4.9 Recruitment records

4.9.1 The records of job applicants must be accessed only by HR and by the interviewers assigned to the applicant.

4.9.2 The records of unsuccessful applicants must be erased 12 months after the recruitment decision, unless the applicant has consented to a longer period.

## 4.10 Performance and disciplinary records

4.10.1 Performance reviews and disciplinary records must be accessed only by HR, the employee's manager and the employee.

4.10.2 Performance and disciplinary records must not be made available through the SecureAI Assistant.

## 4.11 Retention of employee records

4.11.1 Employee records must be retained for the period of employment and for eight years after the employee leaves, or for a longer period where a law requires it, and must then be securely erased.

4.11.2 Payroll and statutory records must be retained for the period required by the applicable labour and tax laws.

## 4.12 Disclosure to third parties

4.12.1 Employee records must not be disclosed outside Evolish except where the employee has consented or where disclosure is required by law, a court or a regulator.

4.12.2 Requests for employment verification must be handled by HR and must be limited to the dates of employment and the last job title, unless the employee has consented to more.

## 5. Roles and responsibilities

- **Head of Human Resources**: owns this policy and is the information owner of employee records.
- **HR staff**: maintain employee records and use salary and personal data only for HR purposes.
- **Managers**: use employee personal records only for their direct reports.
- **Finance**: processes payroll in the payroll system.
- **Data Protection Officer**: advises on the processing of employee personal data.
- **Admin role holders**: maintain the employee data rules of the SecureAI Assistant and review related audit records.
- **All employees**: keep their own records accurate and respect the confidentiality of colleagues' records.

## 6. Exceptions

An exception to this policy must be approved in writing by the Head of Human Resources and the Data Protection Officer for a stated purpose and a fixed period. No exception may be granted to clause 4.2.1 or clause 4.7.2.

## 7. Enforcement

Access to employee records is enforced by HRMS access controls and by the governance engine of the SecureAI Assistant. Blocked requests are logged and contribute to the user's cumulative risk. A breach of this policy may result in removal of access and disciplinary action under the HR disciplinary procedure.

## 8. Related documents

- Information Security Policy (EV-SEC-001)
- Data Classification and Handling Policy (EV-SEC-002)
- Access Control Policy (EV-SEC-003)
- Acceptable Use of AI Tools Policy (EV-SEC-005)
- Data Privacy Policy (EV-SEC-006)
- Incident Response and Security Monitoring Policy (EV-SEC-008)
- Digital Personal Data Protection Act, 2023

## 9. Revision history

| Version | Date | Description | Approved by |
|---|---|---|---|
| 1.0 | 1 November 2026 | First issue | Board Risk Committee |
