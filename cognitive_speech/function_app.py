"""
This file contains the Azure Functions code for a serverless application that uses Azure Cognitive Services to perform search indexing and text-to-speech conversion. 

This file is intended to be deployed as an Azure Function, and requires the appropriate Azure services to be set up and configured with the necessary keys and endpoints.

Author: Aliaksei Vishniavetski
Date: October 2023
"""
import os

import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.storage.blob import BlobServiceClient

import azure.cognitiveservices.speech as speechsdk


# COGNITIVE SEARCH ENVIRONMENT VARIABLES
SEARCH_KEY = os.environ.get("COGSEARCH_KEY")
SEARCH_ENDPOINT = os.environ.get("COGSEARCH_ENDPOINT")
INDEX_NAME = "architecture"

# AZURE BLOB STORAGE ENVIRONMENT VARIABLES
TTS_STORAGE_STRING = os.environ.get("TTS_STORAGE_STRING")

# AZURE SPEECH ENVIRONMENT VARIABLES
SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_LOCATION = os.environ.get("SPEECH_LOCATION")

# CHECK IF ENVIRONMENT VARIABLES ARE SET
if any([SEARCH_KEY is None, 
        SEARCH_ENDPOINT is None,
        INDEX_NAME is None,
        TTS_STORAGE_STRING is None,
        SPEECH_KEY is None,
        SPEECH_LOCATION is None]):
    raise ValueError("Missing environment variables. Cannot proceed.")

# CREATE FUNCTION APP
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_tts_trigger")
def http_tts_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function that generates speech from text and stores it in Azure Blob Storage.
    The function expects a keyword as a query parameter or in the request body.
    If the keyword is found in the index, the function generates speech from the corresponding information
    and stores it in Azure Blob Storage. The function returns the filename, information, and URL of the generated audio file as HTTP Response.
    If the keyword is not found in the index, the function returns an error message.
    """
    keyword = req.params.get('keyword')  # the keyword to search for in the search index
    html = req.params.get('html')  # whether to return the response as HTML

    # PREPARE THE HTML FORMS
    HTML_INITIAL = ""
    HTMl_FINAL = ""
    HTML_FAIL = ""
    entries = get_all_entry_names()

    with open("html_initial.html", "r") as file:
        HTML_INITIAL = file.read()
        HTML_INITIAL = HTML_INITIAL.replace("{entries}", entries)
    with open("html_final.html", "r") as file:
        HTML_FINAL = file.read()
        HTML_FINAL = HTML_FINAL.replace("{entries}", entries)
    with open("html_fail.html", "r") as file:
        HTML_FAIL = file.read()
        HTML_FAIL = HTML_FAIL.replace("{entries}", entries)
    
    if not keyword:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            keyword = req_body.get('keyword')
    
    if not keyword:
        return func.HttpResponse(HTML_INITIAL, status_code=200, mimetype="text/html")

    if keyword:
        # SEARCH FOR THE KEYWORD IN THE INDEX
        name_information = find_information(keyword)

        if name_information is None:
            return func.HttpResponse(HTML_FAIL, status_code=200, mimetype="text/html")
        else:
            filename = name_information["name"] + ".wav"
            text_to_speech = name_information["information"]

            # GENERATE THE LOCAL WAV FILE
            generate_speech_locally(text_to_speech=text_to_speech, filename=filename)

            # UPLOAD THE WAV FILE TO AZURE BLOB STORAGE
            blob_url = send_speech_to_storage(filename)

            # OLD IMPLEMENTATION
            # response_text = "Index search successfull! Closes result to the keyword provided:\n\n" + \
            #                 f"Filename: {filename}\nInformation: {text_to_speech}\nYour audio file with the information voiced can by found at URL: {blob_url}"
            
            # PREPARE THE HTML PAGE
            HTML_FINAL = HTML_FINAL.replace("{filename}", filename)
            HTML_FINAL = HTML_FINAL.replace("{information}", text_to_speech)
            HTML_FINAL = HTML_FINAL.replace("{blob_url}", blob_url)

            return func.HttpResponse(HTML_FINAL, status_code=200, mimetype="text/html")
            #return func.HttpResponse(response_text, status_code=200)
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a keyword in the query string or in the request body to use the Text-to-Speech services.",
             status_code=200
        )
     

def find_information(keyword: str) -> dict[str, str] or None:
    """
    Searches for information related to the given keyword using Azure Cognitive Search.
    
    Args:
        keyword (str): The keyword to search for.
    
    Returns:
        dict[str, str] or None: A dictionary containing the search result, or None if no result is found.
    """
    search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
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
    search_client = SearchClient(SEARCH_ENDPOINT, INDEX_NAME, AzureKeyCredential(SEARCH_KEY))
    result = search_client.search(search_text="*", search_fields="name")
    retval = [_dict["name"].replace("_", " ") for _dict in list(result)]
    retval = "".join([f"<li>{_}</li>" for _ in retval])

    return retval


def send_speech_to_storage(filename: str) -> str:
    """
    Uploads an audio file to Azure Blob Storage and returns the URL of the uploaded file.

    Args:
        filename (str): The name of the audio file to upload.

    Returns:
        str: The URL of the uploaded file.
    """
    
    # CONNECT TO THE BLOB CONTAINER
    blob_service_client = BlobServiceClient.from_connection_string(TTS_STORAGE_STRING)
    blob_container_client = blob_service_client.get_container_client("output-wav")

    # SAVE THE AUDIO FILE TO THE BLOB CONTAINER
    with open(filename, "rb") as wav_file:
        blob_container_client.upload_blob(data=wav_file, name=filename, overwrite=True)

    # CLEAN UP
    os.remove(filename)
    
    # GET THE BLOB URL
    blob_client = blob_container_client.get_blob_client(filename)
    blob_url = blob_client.url

    return blob_url


def generate_speech_locally(text_to_speech: str, filename: str) -> None:
    """
    Generates speech locally using Azure Cognitive Services Text-to-Speech API.
    Saves the result as a WAV file in the current directory.
    
    Args:
    text_to_speech (str): The text to be converted to speech.
    filename (str): The name of the file to save the generated speech.
    
    Returns:
    None
    """
    
    # SET SPEECH AND AUDIO CONFIGURATION
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_LOCATION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename=filename)
    speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "SPEECH_LOG.txt")
    VOICE_NAME = "en-AU-WilliamNeural"
    speech_config.speech_synthesis_voice_name=VOICE_NAME
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # GENERATE SPEECH
    text = text_to_speech
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

    