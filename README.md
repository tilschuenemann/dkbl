## Functional Requirements - Documents

1. The program reads the DKB csv export and creates a report with the following columns:

* date*
* amount*
* balance
* type
* occurence
* recipient_clean*
* label1*
* label2*
* label3*

Columns marked with * feature a copy with the suffix "_custom", where the user can safely correct
data without losing the original.

2. To help the user with entering a redundant information like labels for reoccurring transactions, a mapping table is provided. Here, the recipient can also be given a clean name. The mapping table features the following columns:

* recipient
* recipien_clean
* label1
* label2
* label3
* occurence

## Functional Requirements - Workflows

1. The user specifies the original report and creates the ledger and the mapping table. The ledger is sorted ascending by date, the mapping table is sorted alphabetically by recipient. All columns are formatted appropriately.

[x] import content

[x] import header

[x] create ledger

[x] create mapping table

[ ] tests

2. The user should be able to make changes to the ledger or mapping table and then update the ledger. Balances, mappings and mapping table get updated.

[x] update balance

[x] update mappings

[x] update mappings table

[ ] update tests

3. New exports get appended to the original ledger.

[x] append ledger

## Non-functional Requirements

1. The program should provide a log entry for each operation and their changes (amount of records added or deleted).