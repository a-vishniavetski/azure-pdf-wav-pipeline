"""
This file contains the Azure Functions code for a serverless application that uses Azure Cognitive Services to perform search indexing and text-to-speech conversion.

This file is intended to be deployed as an Azure Function, and requires the appropriate Azure services to be set up and configured with the necessary keys and endpoints.

Author: Aliaksei Vishniavetski
Date: October 2023
"""
import os

import azure.functions as func
from azure.core.credentials import AzureKeyCredential

# STORAGE
from azure.storage.blob import BlobServiceClient

# DOCUMENT INTELLIGENCE
from azure.ai.formrecognizer import DocumentAnalysisClient

# SPEECH
import azure.cognitiveservices.speech as speechsdk

# COGNITIVE SEARCH
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    ComplexField,
    CorsOptions,
    SearchIndex,
    ScoringProfile,
    SearchFieldDataType,
    SimpleField,
    SearchableField
)


# COGNITIVE SEARCH 
SEARCH_ACCESS_KEY = os.environ.get("COGSEARCH_KEY")
SEARCH_ENDPOINT = os.environ.get("COGSEARCH_ENDPOINT")
SEARCH_INDEX_NAME = "architecture"

# AZURE BLOB STORAGE 
SPEECH_STORAGE_STRING = os.environ.get("TTS_STORAGE_STRING")  # This one is for the Speech services
STORAGE_STRING = os.environ.get("STORAGE_STRING1")  # This one has the PDFs
CONTAINER_NAME = "pdfs"  # Azure pdfs Blob Container  Name

# AZURE SPEECH 
SPEECH_ACCESS_KEY = os.environ.get("SPEECH_KEY")
SPEECH_LOCATION = os.environ.get("SPEECH_LOCATION")

# DOCUMENT INTELLIGENCE 
DI_KEY = os.environ.get("DI_KEY1") 
DI_ENDPOINT = os.environ.get("DI_ENDPOINT")

# AZURE FUNCTION 
FUNCTION_ACCESS_CODE = os.environ.get("FUNC_CODE")

# CHECK IF ENVIRONMENT VARIABLES ARE SET
if any([SEARCH_ACCESS_KEY is None, 
        SEARCH_ENDPOINT is None,
        SEARCH_INDEX_NAME is None,
        SPEECH_STORAGE_STRING is None,
        SPEECH_ACCESS_KEY is None,
        SPEECH_LOCATION is None,
        FUNCTION_ACCESS_CODE is None]):
    raise ValueError("Missing environment variables. Cannot proceed.")

# CREATE FUNCTION APP
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route=f"http_tts_trigger")
def http_tts_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function that generates speech from text and stores it in Azure Blob Storage.
    The function expects a keyword as a query parameter or in the request body.
    If the keyword is found in the index, the function generates speech from the corresponding information
    and stores it in Azure Blob Storage. The function returns the filename, information, and URL of the generated audio file as HTTP Response.
    If the keyword is not found in the index, the function returns an error message.
    """
    keyword_for_search = req.params.get('keyword')  # the keyword to search for in the search index
    index_update_flag = req.params.get('update')  # if set to "true", the search index will be updated

    # PREPARE THE HTML FORMS
    HTML_INITIAL_FORM = ""
    HTML_FINAL_FORM = ""
    HTML_FAIL_FORM = ""
    HTML_UPDATE_FORM = ""
    existing_index_entries = get_all_entry_names()

    with open("html_initial.html", "r") as file:
        HTML_INITIAL_FORM = file.read()
        HTML_INITIAL_FORM = HTML_INITIAL_FORM.replace("{entries}", existing_index_entries)
        HTML_INITIAL_FORM = HTML_INITIAL_FORM.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    with open("html_final.html", "r") as file:
        HTML_FINAL_FORM = file.read()
        HTML_FINAL_FORM = HTML_FINAL_FORM.replace("{entries}", existing_index_entries)
        HTML_FINAL_FORM = HTML_FINAL_FORM.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    with open("html_fail.html", "r") as file:
        HTML_FAIL_FORM = file.read()
        HTML_FAIL_FORM = HTML_FAIL_FORM.replace("{entries}", existing_index_entries)
        HTML_FAIL_FORM = HTML_FAIL_FORM.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    with open("html_update.html", "r") as file:
        HTML_UPDATE_FORM = file.read()
        HTML_UPDATE_FORM = HTML_UPDATE_FORM.replace("{entries}", existing_index_entries)
        HTML_UPDATE_FORM = HTML_UPDATE_FORM.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    
    if index_update_flag:
        try:
            update_index()
            return func.HttpResponse(HTML_UPDATE_FORM, status_code=200, mimetype="text/html")
        except:
            return func.HttpResponse("Index update failed.", status_code=500)
            
    if not keyword_for_search:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            keyword_for_search = req_body.get('keyword')
    
    if not keyword_for_search:
        return func.HttpResponse(HTML_INITIAL_FORM, status_code=200, mimetype="text/html")

    if keyword_for_search:
        # SEARCH FOR THE KEYWORD IN THE INDEX
        filename_and_text = find_index_entry(keyword_for_search)

        if filename_and_text is None:
            return func.HttpResponse(HTML_FAIL_FORM, status_code=200, mimetype="text/html")
        else:
            filename = filename_and_text["name"] + ".wav"
            text_to_speech = filename_and_text["information"]

            # GENERATE THE LOCAL WAV FILE
            audio_data_bytes = synthesize_speech_stream(text_to_speech=text_to_speech)

            # UPLOAD THE WAV FILE TO AZURE BLOB STORAGE
            blob_url = send_speech_to_storage(filename, audio_data_bytes)
            
            # PREPARE THE HTML PAGE
            HTML_FINAL_FORM = HTML_FINAL_FORM.replace("{filename}", filename)
            HTML_FINAL_FORM = HTML_FINAL_FORM.replace("{information}", text_to_speech)
            HTML_FINAL_FORM = HTML_FINAL_FORM.replace("{blob_url}", blob_url)

            return func.HttpResponse(HTML_FINAL_FORM, status_code=200, mimetype="text/html")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a keyword in the query string or in the request body to use the Text-to-Speech services.",
             status_code=200
        )
     

def find_index_entry(keyword: str) -> dict[str, str] or None:
    """
    Searches for information related to the given keyword using Azure Cognitive Search.
    
    Args:
        keyword (str): The keyword to search for.
    
    Returns:
        dict[str, str] or None: A dictionary containing the search result, or None if no result is found.
    """
    search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX_NAME, AzureKeyCredential(SEARCH_ACCESS_KEY))
    result = search_client.search(search_text=keyword)
    result = list(result)
    if len(result) == 0:
        return None
    else:
        return result[0]


def get_all_entry_names() -> str:
    """
    Returns a list of all names in the search index.
    
    Returns:
        str: A list of all names in the search index, IN HTML.
    """
    search_client = SearchClient(SEARCH_ENDPOINT, SEARCH_INDEX_NAME, AzureKeyCredential(SEARCH_ACCESS_KEY))
    result = search_client.search(search_text="*", search_fields="name")
    retval = [_dict["name"].replace("_", " ") for _dict in list(result)]
    retval = "".join([f"<li>{_}</li>" for _ in retval])

    return retval


def send_speech_to_storage(filename: str, audio_data: bytes) -> str:
    """
    Uploads an audio file to Azure Blob Storage and returns the URL of the uploaded file.

    Args:
        filename (str): The name of the audio file to upload.
        audio_data (bytes): The audio data of the audio file to upload.

    Returns:
        str: The URL of the uploaded file.
    """
    
    # CONNECT TO THE BLOB CONTAINER
    blob_service_client = BlobServiceClient.from_connection_string(SPEECH_STORAGE_STRING)
    blob_container_client = blob_service_client.get_container_client("output-wav")

    # SAVE THE AUDIO FILE TO THE BLOB CONTAINER
    blob_container_client.upload_blob(data=audio_data, name=filename, overwrite=True)
    
    # GET THE BLOB URL
    blob_client = blob_container_client.get_blob_client(filename)
    blob_url = blob_client.url

    return blob_url


def synthesize_speech_stream(text_to_speech: str) -> bytes:
    """
    Generates speech locally using Azure Cognitive Services Text-to-Speech API.
    Saves the result as a WAV file in the current directory.
    
    Args:
    text_to_speech (str): The text to be converted to speech.
    filename (str): The name of the file to save the generated speech.
    
    Returns:
    audio_data (bytes): The audio data of the generated speech.
    """
    
    # SET SPEECH AND AUDIO CONFIGURATION
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_ACCESS_KEY, region=SPEECH_LOCATION)
    
    VOICE_NAME = "en-AU-WilliamNeural"
    speech_config.speech_synthesis_voice_name=VOICE_NAME
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)  # None for audio_config stops the audio from playing automatically

    # GENERATE SPEECH
    text = text_to_speech
    speech_synthesis_result: speechsdk.SpeechSynthesisResult = speech_synthesizer.speak_text_async(text).get()
    audio_data = speech_synthesis_result.audio_data

    return audio_data


# ---------------------------------- DOCUMENT INTELLIGENCE ----------------------------------


def analyze_general_documents(doc_infos: dict[str, str],
                              di_endpoint: str,
                              di_key: str) -> list[dict[str, str]]:
    """
    Analyzes the content of general documents using Azure Form Recognizer.

    Args:
        doc_infos (dict): A dictionary of document names and their corresponding URLs.

    Returns:
        dict: A dictionary of document names and the extracted text from each document.
    """

    retval = []

    # create your `DocumentAnalysisClient` instance and `AzureKeyCredential` variable
    document_analysis_client = DocumentAnalysisClient(endpoint=di_endpoint, credential=AzureKeyCredential(di_key))

    for name, url in doc_infos.items():
        doc_text = analyze_general_document(document_analysis_client=document_analysis_client,
                                            url=url)
        _dict = {}
        _dict["name"] = name
        _dict["information"] = doc_text
        retval.append(_dict)

    return retval


def analyze_general_document(document_analysis_client: DocumentAnalysisClient, url: str) -> str:
    """
    Analyzes the content of a specific document using Azure Form Recognizer.

    Args:
        document_analysis_client (DocumentAnalysisClient): An instance of DocumentAnalysisClient.
        url (str): The URL of the document to be analyzed.

    Returns:
        str: The extracted text from the document.
    """

    retval = ""

    poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-document", url)
    
    result = poller.result()

    for page in result.pages:
        retval = "".join(line.content for line in page.lines)
    
    print(f"Document analyzed successfully. URL: {url}")
    return retval


def get_blob_infos(storage_account_string: str, 
                   container_name: str,
                   ) -> dict[str, str]:
    """
    Retrieves a dictionary of blob names and their corresponding URLs from an Azure Blob Storage account.

    Args:
        storage_account_string (str): The connection string for the Azure Storage Account.
        container_name (str): The name of the container in the Azure Blob Storage.

    Returns:
        dict: A dictionary containing blob names as keys and their URLs as values.
    """
    
    # ACCESS THE STORAGE ACCOUNT
    blob_service_client = BlobServiceClient.from_connection_string(storage_account_string)
    
    # ACCES THE CONTAINER
    container_client = blob_service_client.get_container_client(container=container_name)

    # ACCESS THE BLOBS, GET THEIR URLS
    blob_info = {}
    blobs_properties = container_client.list_blobs()
    for blob_property in blobs_properties:
        blob_client = container_client.get_blob_client(blob=blob_property.name)
        blob_url = blob_client.url
        blob_name = blob_client.blob_name[:blob_client.blob_name.find(".pdf")].replace("-", " ")
        blob_info[blob_name] = blob_url

    return blob_info


# ---------------------------------- COGNITIVE SEARCH ----------------------------------


def create_search_index(index_name: str, search_endpoint: str, search_key: str):
    """
    Creates a new search index with the specified name, or recreates it.

    Args:
        index_name (str): The name of the search index to create or update.

    Returns:
        None
    """
    search_index_client = SearchIndexClient(search_endpoint, AzureKeyCredential(search_key))

    # DELETE THE INDEX IF IT EXISTS
    if "architecture" in [index.name for index in search_index_client.list_indexes()]:
        print("The 'architecture' index already exists. Deleting old index.")
        search_index_client.delete_index("architecture")
        print("Old index deleted.")

    # CREATE THE INDEX
    fields = [
            SearchableField(name="name", type=SearchFieldDataType.String, key=True),
            SearchableField(name="information", type=SearchFieldDataType.String)
        ]
    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles = []

    index = SearchIndex(
        name=index_name,
        fields=fields,
        scoring_profiles=scoring_profiles,
        cors_options=cors_options)

    result = search_index_client.create_index(index)
    print(f"Create Index {index_name} succeeded.")


def upload_documents_to_index(index_name: str, documents: list[dict[str, str]],
                              search_endpoint: str, search_key: str):
    search_client = SearchClient(search_endpoint, index_name, AzureKeyCredential(search_key))

    # UPLOAD DOCUMENTS TO THE INDEX
    result = search_client.upload_documents(documents=documents)
    print(f"Upload of new document succeeded: {result[0].succeeded}")


# ---------------------------------- SEARCH INDEX UPDATE ----------------------------------


def update_index() -> None:
    """
    Run this function to create or re-create an index in the Azure Cognitive Search service and at the same time to upload the documents, found in the associated
    storage account, to the index.
    Returns:
        None
    """
    # CREATE THE INDEX
    create_search_index(SEARCH_INDEX_NAME, SEARCH_ENDPOINT, SEARCH_ACCESS_KEY)
    print("-----Index created successfully.-----")

    # GET THE DOCUMENT NAMES AND URLS
    blobs_info = get_blob_infos(STORAGE_STRING, CONTAINER_NAME)
    print("-----Blobs info retrieved successfully.-----")

    # GET THE DOCUMENTS' TEXT
    documents = analyze_general_documents(blobs_info, DI_ENDPOINT, DI_KEY)
    print("-----Documents analyzed successfully.-----")
    
    # UPLOAD DOCUMENTS TO THE INDEX
    upload_documents_to_index(index_name=SEARCH_INDEX_NAME, 
                                               documents=documents,
                                               search_endpoint=SEARCH_ENDPOINT,
                                               search_key=SEARCH_ACCESS_KEY)
    print("-----Documents uploaded to index successfully.-----")


@app.route(route="pdf_to_speech", auth_level=func.AuthLevel.FUNCTION)
def pdf_to_speech(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )