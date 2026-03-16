# RAGFlow Assistant Prompt Library

Common English prompts for using this RAGFlow skill.

This library focuses on:
- file upload
- parsing control
- stopping parsing for specific documents
- progress tracking
- dataset and document inspection
- retrieval and knowledge lookup
- listing configured LLM providers and models
- dataset and document deletion
- troubleshooting

For model listing:
- default behavior should show only available models
- default grouping should be by model `type`
- extra details should be shown only when explicitly requested
- provider / vendor grouping should be supported when requested

## File Input

When asking the assistant to upload files:
- prefer explicit local file paths such as `/data/reports/q1.pdf`
- if your client supports it, you can also drag files into the chat
- direct file paths are more reliable
- large drag-and-drop uploads may fail

## Scope Rules For Progress Requests

The skill resolves progress scope by specificity:
- if no dataset is specified, check all datasets and all documents
- if a dataset is specified, check all documents in that dataset
- if document IDs are specified, check only those documents

For broad progress requests, the assistant should list currently `RUNNING` documents first.
If parse status returns an error, return that error directly instead of guessing the cause.
If a parse status document contains `progress_msg`, surface it directly. For `FAIL` documents, use that field as the error detail.

## Common Prompts

### 1. File Upload

#### Upload a file to a dataset

```text
Upload this file to the "{dataset_name}" dataset in RAGFlow.
```

#### Upload a file from a local path

```text
Upload the file at "{file_path}" to the "{dataset_name}" dataset.
```

#### Upload multiple files from local paths

```text
Upload these files to the "{dataset_name}" dataset:
{file_path_1}
{file_path_2}
{file_path_3}
```

### 2. Upload And Start Parsing

#### Upload and parse

```text
Upload this file to "{dataset_name}" and start parsing.
```

#### Upload from a local path and parse

```text
Upload the file at "{file_path}" to "{dataset_name}" and start parsing.
```

### 3. Parsing Task Control

#### Parse specific files

```text
Start parsing these document IDs in "{dataset_name}":
{document_id_1}, {document_id_2}
```

#### Re-parse a document

```text
Re-parse the document with ID "{document_id}" in dataset "{dataset_name}".
```

#### Stop parsing specific files

```text
Stop parsing document IDs "{document_id_1}" and "{document_id_2}" in "{dataset_name}".
```

#### Resolve IDs first, then stop parsing

```text
List all files in "{dataset_name}", find the currently running documents named "{document_name}", and stop parsing those document IDs.
```

### 4. Parsing Progress Queries

#### Check overall parsing progress

```text
Check the parsing progress.
```

#### Check progress for one dataset

```text
Show the parsing progress of all files in "{dataset_name}".
```

#### Check progress for specific documents

```text
Show the parsing progress of document IDs "{document_id_1}" and "{document_id_2}" in "{dataset_name}".
```

#### Show only files still being parsed

```text
Show me all files that are still running.
```

### 5. Dataset Information

#### List all files in a dataset

```text
List all files in "{dataset_name}".
```

#### Show dataset parsing summary

```text
Show the parsing status summary of "{dataset_name}".
Include total files, RUNNING, DONE, FAIL, and CANCEL counts.
```

### 6. Retrieval

#### Search all configured datasets

```text
Search my RAGFlow knowledge base for: "{query}".
```

#### Search one dataset only

```text
Search the "{dataset_name}" dataset for: "{query}".
```

#### Search specific files only

```text
Search document IDs "{document_id_1}" and "{document_id_2}" in "{dataset_name}" for: "{query}".
```

#### High precision retrieval

```text
Search "{dataset_name}" for "{query}" with a higher similarity threshold and show the best chunks.
```

### 7. Models

#### List available models

```text
List available models.
```

#### Group models by provider

```text
Show models grouped by {provider}.
```

### 8. Troubleshooting

#### Check why parsing failed

```text
Check why this document failed to parse: "{document_id}" in "{dataset_name}".
```

#### Show document details

```text
Show the parsing details for document ID "{document_id}" in "{dataset_name}".
```

### 9. Deletion And Cleanup

#### Delete specific documents from a dataset

```text
Delete document IDs "{document_id_1}" and "{document_id_2}" from "{dataset_name}".
```

#### Delete documents by first listing the dataset contents

```text
List all files in "{dataset_name}", find the matching document IDs, and delete the documents named "{document_name}".
```

For both delete and stop-parsing actions:
- execute only on explicit document IDs
- if the user only knows filenames or partial names, list documents first and resolve exact IDs
- do not perform fuzzy batch delete or fuzzy batch stop actions

#### Delete a dataset

```text
Delete the "{dataset_name}" dataset.
```

#### Delete multiple datasets

```text
Delete these datasets in RAGFlow:
"{dataset_name_1}"
"{dataset_name_2}"
```

### 10. Recommended Automation Prompt

```text
Upload the file at "{file_path}" to "{dataset_name}" and start parsing.
```

## Minimal Prompt Set

If you only need the most useful prompts, start with these:

1. `Upload the file at "{file_path}" to "{dataset_name}".`
2. `Upload the file at "{file_path}" to "{dataset_name}" and start parsing.`
3. `Check the parsing progress.`
4. `Show the parsing progress of all files in "{dataset_name}".`
5. `Check why document "{document_id}" failed to parse in "{dataset_name}".`
6. `Stop parsing document "{document_id}" in "{dataset_name}".`
7. `Delete document "{document_id}" from "{dataset_name}".`
8. `Search the "{dataset_name}" dataset for: "{query}".`
9. `List available models.`

## Typical Workflow

A standard ingestion flow looks like this:

1. Upload file
2. Start parsing
3. Monitor parsing progress
4. Stop parsing specific documents if needed
5. Review dataset status
6. Search the dataset for relevant answers
7. Troubleshoot failed documents if needed
8. Delete documents or datasets when cleanup is needed

## What To Provide

For best results, include as much of the following as possible:

- dataset name or dataset ID
- local file path
- document ID, if you are targeting a specific document
- explicit document IDs if you want to stop parsing
- query text, if you want retrieval

For deletion tasks, provide:

- dataset name or dataset ID
- explicit document IDs when deleting or stopping specific documents
- document name only if you want the assistant to list files first and resolve exact IDs before acting
