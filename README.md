<img src="https://github.com/a-vishniavetski/azure-pdf-wav-pipeline/assets/132013288/f919ade1-95b2-4fc8-95ce-52e5389b8529" align="right" height="75">

# Cloud Speech Synthesis from scanned documents on Azure platform
> A Cloud-deployed python application, that can process PDF documents and create .WAV files with information extracted.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Navigation

- [Overview](#Overview)
- [Technologies used](#technologies-used)
- [Configuration and Deployment](#Configuration-and-Deployment)
- [Code Navigation](#code-navigation)
- [Usage](#usage)
- [License](#license)

## Overview
Access to the application is available either through the simple front-end, or directly through the HTTP requests with corresponding query parameters.
- **Document Processing**: Scan PDF documents, contained in Azure Storage Account, with Azure Document Intelligence

- **Cognitive Search**: Create, Access, and Update a Cognitive Search Index containing scanned information.

- **Speech Synthesis**: Query the search index to generate .WAV files with AI voicing the selected information.

<img src="https://github.com/a-vishniavetski/azure-pdf-wav-pipeline/assets/132013288/8797b982-3a07-4005-91f0-467db2c5a3b2" align="center">

## Technologies Used

The following Azure technologies and services were used:

- **Python SDK**: To build and automate the whole application.

- **App Functions**: To create a cloud-based environment, configured to run the application.

- **App Service Plan**: To contain the App Function

- **Cognitive Search**: For efficient keyword-based document retrieval.

- **Speech Services**: For creating .WAV files voicing the retrieved information.

- **Document Intelligence (DI)**: To scan and extract text from PDFs.
  
- **Storage Accounts**: For storing PDF files.

- **Application Insights**: For analyzing logs, stack traces, statistics of user access, and overall performance of the application.

An example of a deployed resource group:

<img src="https://github.com/a-vishniavetski/azure-pdf-wav-pipeline/assets/132013288/ceb76d76-abab-4116-8a45-cdd41b6072eb">

## Configuration and Deployment
> The repository is intended as a showcase, rather than as an installation source since the app uses Access Keys and Endpoints and does not yet implement Azure Active Directory or Azure Key Vault. The general guidelines, however, would be:
1. Prepare all of the necessary Azure resources, such as *Storage Account(for PDFs), Search Service, Speech Service, Document Intelligence Service, App Service Plan, Function app* and optionally *Application Insights*.
2. Download the contents of the `function_app` folder. It contains an Azure Function App ready for deployment, ***except for the environment variables necessary!***
3. Configure a Function App project in the downloaded folder, using [*VS Code Azure Tools Extension Pack*](https://marketplace.visualstudio.com/items?itemName=ms-vscode.vscode-node-azure-pack), or other preferred methods of interaction with Azure.
4. Either through `local.settings.json` before the deployment, or Azure Portal after the deployment, set the necessary environment variables(everything than requires `os.environ.get()` in the Python code).
5. *Optionally*: Debug the application using the debugger available in VS Code that interacts with the Azure Extension Pack.
6. Deploy the application
7. Check if the `FUNC_CODE` environment variable corresponds to the function code found in the *"Code + Test"* section in the Azure Portal -> Your App Service Plan -> Your App Function.

## Code Navigation
- `function_app`
  - `function_app.py`: The application code
  - `html_initial/final/fail/update`: HTML pages to provide front-end for the app
  - `requirements.txt`: List of packages for the Python environment
  - `host.json`: Azure configuration file
- `miscellaneous`
  - `pdfs`
    - Examples of the PDF with information, that can be uploaded to blob storage
  - `architecture_wikipedia_scraper.py`: Script to web-scrape Wikipedia and create PDF files, that can be uploaded to the Storage Account. **Azure unrelated.**

## Usage

**Deployed application** is available at [this URL](https://tts-script-func.azurewebsites.net/api/pdf_to_speech?code=r4Kzu1kVYD5IngJ_XcdGcYI3uCpXowGwOF8WRry7gJuaAzFuW-Bffw==), as long as my Azure Student Subscription won't run out.

***Workflow:***
1. PDF documents get uploaded to the Azure Storage Account (so far manually)

2. Enter the name of the index entry about which you would like to get the information in the search box, and click "Submit"

3. Download the resulting .WAV file using the link on the page.

***Optionally:***

4. Update the search index using the corresponding button. The process takes some time, depending on the amount of documents in the storage.

## License
The application is licensed under the terms of the MIT Open Source license and is available for free for any purposes.
