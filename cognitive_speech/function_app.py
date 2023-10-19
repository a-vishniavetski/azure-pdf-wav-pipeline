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


# COGNITIVE SEARCH 
SEARCH_ACCESS_KEY = os.environ.get("COGSEARCH_KEY")
SEARCH_ENDPOINT = os.environ.get("COGSEARCH_ENDPOINT")
SEARCH_INDEX_NAME = "architecture"

# AZURE BLOB STORAGE 
SPEECH_STORAGE_STRING = os.environ.get("TTS_STORAGE_STRING")

# AZURE SPEECH 
SPEECH_ACCESS_KEY = os.environ.get("SPEECH_KEY")
SPEECH_LOCATION = os.environ.get("SPEECH_LOCATION")

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
    print("HELLO")
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
    HTML_FINAL = ""
    HTML_FAIL = ""
    entries = get_all_entry_names()

    with open("html_initial.html", "r") as file:
        HTML_INITIAL = file.read()
        HTML_INITIAL = HTML_INITIAL.replace("{entries}", entries)
        HTML_INITIAL = HTML_INITIAL.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    with open("html_final.html", "r") as file:
        HTML_FINAL = file.read()
        HTML_FINAL = HTML_FINAL.replace("{entries}", entries)
        HTML_FINAL = HTML_FINAL.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    with open("html_fail.html", "r") as file:
        HTML_FAIL = file.read()
        HTML_FAIL = HTML_FAIL.replace("{entries}", entries)
        HTML_FAIL = HTML_FAIL.replace("{FUNC_CODE}", FUNCTION_ACCESS_CODE)
    
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
            audio_data = generate_speech_stream(text_to_speech=text_to_speech)

            # UPLOAD THE WAV FILE TO AZURE BLOB STORAGE
            blob_url = send_speech_to_storage(filename, audio_data)
            
            # PREPARE THE HTML PAGE
            HTML_FINAL = HTML_FINAL.replace("{filename}", filename)
            HTML_FINAL = HTML_FINAL.replace("{information}", text_to_speech)
            HTML_FINAL = HTML_FINAL.replace("{blob_url}", blob_url)

            return func.HttpResponse(HTML_FINAL, status_code=200, mimetype="text/html")
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


def generate_speech_stream(text_to_speech: str) -> bytes:
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
    
    speech_config.set_property(speechsdk.PropertyId.Speech_LogFilename, "SPEECH_LOG.txt")
    VOICE_NAME = "en-AU-WilliamNeural"
    speech_config.speech_synthesis_voice_name=VOICE_NAME
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)  # None for audio_config stops the audio from playing automatically

    # GENERATE SPEECH
    text = text_to_speech
    speech_synthesis_result: speechsdk.SpeechSynthesisResult = speech_synthesizer.speak_text_async(text).get()
    audio_data = speech_synthesis_result.audio_data

    return audio_data

    