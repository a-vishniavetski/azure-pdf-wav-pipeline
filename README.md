<img src="https://github.com/a-vishniavetski/azure-pdf-wav-pipeline/assets/132013288/f919ade1-95b2-4fc8-95ce-52e5389b8529" align="right" height="75">

# Cloud Speech Synthesis from scanned documents on Azure platform
> A Cloud-deployed python application, that can process PDF documents and create .WAV files with information extracted.
## Key Features

- **Document Processing**: Scan PDF documents, contained in Azure Storage Account, with Azure Document Intelligence

- **Cognitive Search**: Create, Access, and Update a Cognitive Search Index containing scanned information.

- **Speech Synthesis**: Query the search index to generate .WAV files with AI voicing the selected information.

***A simple front-end is also provided:***

<img src="https://github.com/a-vishniavetski/azure-pdf-wav-pipeline/assets/132013288/8797b982-3a07-4005-91f0-467db2c5a3b2" align="center">

## Technologies Used

The following Azure technologies and services were used:

- **Python SDK**: To build and automate the whole application.

- **App Functions**: To create a cloud-based environment, configured to run the application.

- **Cognitive Search**: For efficient keyword-based document retrieval.

- **Speech Services**: For creating .WAV files voicing the retrieved information.

- **Document Intelligence (DI)**: To scan and extract text from PDFs.
  
- **Storage Accounts**: For storing PDF files.

- **Application Insights**: For analyzing logs, stack traces, statistics of user access, and overall performance of the application.

## Code navigation
`function_app` folder:
* `function_app.py` is the application itself
* `html_...` HTML pages to provide front-end for the app

`miscellaneous` folder: Contains Azure-unrelated scripts, that can be used to web-scrape Wikipedia and prepare the PDF documents for the upload to the Storage Account.

## Usage

**Deployed application** is available at [this URL](https://tts-script-func.azurewebsites.net/api/pdf_to_speech?code=r4Kzu1kVYD5IngJ_XcdGcYI3uCpXowGwOF8WRry7gJuaAzFuW-Bffw==), as long as my Azure Student Subscription won't run out.

***Workflow:***
1. PDF documents get uploaded to the Azure Storage Account (so far manually)

2. Enter the name of the index entry about which you would like to get the information in the search box, and click "Submit"

3. Download the resulting .WAV file using the link on the page.

***Optionally:***

4. Update the search index using the corresponding button. The process takes some time, depending on the amount of documents in the storage.

*Note: The whole process is also possible through manual https requests with corresponding query parameters*
