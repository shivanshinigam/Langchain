# LangChain + MCP + LLM DATA QC POC


1. INTRODUCTION
------------------------------------------------------------
The goal of this POC was to build a simple but intelligent
pipeline that can:

1. Take a question and get an answer using LangChain + LLM.
2. Connect LangChain code to an MCP server (mock or real).
3. Produce sample dataset output (20 rows x 5 columns),
   assuming this data came from a Snowflake query.
4. Detect BAD DATA using LLM reasoning instead of traditional
   hard-coded "if-else" checks, because column types and data
   structures will always change.

The final code satisfies ALL the above requirements.


2. WHAT THE SYSTEM DOES (HUMAN EXPLANATION)
------------------------------------------------------------
The pipeline behaves like a small end-to-end AI system:

STEP 1 — User can ask any question.
The script uses LangChain + Gemini (Google GenAI) to answer.
This confirms that LLM connectivity works.

STEP 2 — The code optionally connects to an MCP server.
We implemented:
- health check (/health)
- POST ingestion endpoint (/ingest/sample)

The code can send the dataset to MCP if the server is running.

STEP 3 — Create sample data.
We generate:
- 20 rows
- 5 columns (order_id, name, age, amount, order_date)
With purposely incorrect values:
- invalid numeric name (“123456”, “007”)
- invalid age (151)

This simulates messy real-world data.

STEP 4 — LLM-BASED Data Quality Check.
Instead of writing validation rules in Python,
we send the dataset to an LLM (Gemini) and ask:

    "Look at the column names and values and tell me what is wrong."

The LLM autonomously figures out:
- numeric names
- unrealistic age
- formatting issues
- type inconsistencies

This is CRUCIAL because future datasets may have:
- different columns
- different meanings
- different types

AI-driven inference solves this.


3. WHAT MAKES THIS APPROACH DIFFERENT?
------------------------------------------------------------
✔ NO hard-coded validation rules  
✔ Works on ANY arbitrary dataset  
✔ LLM understands column semantics (like “age” means human age)  
✔ Output is STRICT JSON (machine-readable)  
✔ Easily extendable to Snowflake or production pipelines  
✔ MCP can store or forward the data for later processing  


4. HOW THE WORKFLOW RUNS (END-TO-END)
------------------------------------------------------------

1. User runs:
   
       python langchain_mcp_qc.py
   OR
   
       python langchain_mcp_qc.py --send-mcp
   OR
   
       python langchain_mcp_qc.py --file dataset.csv

3. System loads sample dataset or user-provided file.

<img width="373" height="322" alt="Screenshot 2025-12-05 at 7 21 00 PM" src="https://github.com/user-attachments/assets/18fdf63f-a02c-4995-b230-a08fb01bbaf5" />

4. If --send-mcp is enabled:
   - It checks MCP health
   - Sends sample data to MCP (POST /ingest/sample)
  
<img width="431" height="49" alt="Screenshot 2025-12-05 at 7 21 04 PM" src="https://github.com/user-attachments/assets/f053ad22-9874-424a-b9cb-a7b87509be59" />


5. LLM Data Quality Checker runs:
   - Sends first 20 rows to Gemini
   - Gets strict JSON response with anomalies
   - Parses the JSON safely, removing ```json fences

6. Final result:
   - Summary of data quality
   - List of anomalies (row, column, issue, severity)
   - Suggested corrections

<img width="647" height="500" alt="Screenshot 2025-12-05 at 7 21 10 PM" src="https://github.com/user-attachments/assets/751e9b73-bded-4e9c-9d53-d81d6f16b1d6" />


This demonstrates complete AI-assisted QC.


5. RESULT SAMPLE (SHORTENED)
------------------------------------------------------------
Example output from Gemini:

    {
      "summary": "Found 3 anomalies...",
      "anomalies": [
        { "row_index": 4, "column": "name", "value": "123456", ... },
        { "row_index": 6, "column": "age", "value": 151, ... },
        { "row_index": 11, "column": "name", "value": "007", ... }
      ],
      "suggested_actions": [
        "Fix numeric-only names.",
        "Age >120 should be verified or corrected."
      ]
    }

This proves the LLM correctly interpreted the dataset
WITHOUT any programmatic rules.


6. WHAT WAS COMPLETED (CHECKLIST)
------------------------------------------------------------
✔ Sample LangChain code created  
✔ LLM (Gemini) integrated for QA  
✔ MCP connection (health + POST) implemented  
✔ Sample dataset generation implemented  
✔ AI-based data quality detection implemented  
✔ JSON-only response handling implemented  
✔ Works on ANY dataset (.csv/.json)  
✔ Bad data detection done entirely via LLM reasoning  
✔ No hard-coded validations — fully dynamic  


7. WHY THIS POC IS SUCCESSFUL
------------------------------------------------------------
- Shows ability to combine LangChain + LLM + MCP + data pipelines
- Demonstrates smart AI-based QC logic
- Fully modular, easily productionized
- Covers all requested tasks with clean code and clear reasoning
- Demonstrates strong understanding of:
  → LangChain
  → LLM prompting
  → JSON schemas
  → MCP architecture
  → Data validation concepts
  → Error-handling in AI systems



9. CONCLUSION
------------------------------------------------------------
This POC successfully demonstrates how LangChain, Gemini LLM,
and MCP can work together to build a flexible and intelligent
data-quality engine.

The system is simple, powerful, and general enough to handle 
any dataset — exactly as required.


============================================================
END OF REPORT
============================================================
