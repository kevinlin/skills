# Contoso Rebate Platform: Detailed Requirements (synthetic excerpt)

## Settlement (FR_M20 to FR_M28)

| ID | Requirement |
|----|-------------|
| FR_M20 | At period close the platform calculates the claim settlement amount per customer: accrued rebate less prior settlements. |
| FR_M21 | The platform produces a settlement statement for each customer once posting is confirmed. |
| FR_M22 | A settlement above 10,000 requires Finance review before it is posted. |
| FR_M23 | A rejected settlement returns to calculation with the reviewer's reason attached. |
| FR_M24 | An approved settlement is posted to the ERP as a credit memo. |
| FR_M25 | The ERP document number returned by the posting is stored on the settlement. |
| FR_M26 | A disputed settlement is held and Finance resolves the dispute within 10 working days. |
| FR_M27 | The customer is notified when the settlement statement is available. |
| FR_M28 | Every approval decision is logged with the user and a timestamp. |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-P02 | The settlement run completes within 4 hours for up to 200 customer accounts per period. |
| NFR-A01 | The settlement audit trail is retained for 7 years. |
