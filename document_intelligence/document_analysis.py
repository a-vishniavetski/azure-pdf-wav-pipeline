import os
import uuid
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


# set credentials to access the service. 
# Environment vars are not very safe, but for test purposes they will do.
DI_KEY = os.environ.get("DI_KEY1")
DI_ENDPOINT = os.environ.get("DI_ENDPOINT")
STORAGE_STRING = os.environ.get("STORAGE_STRING1")
ACCOUNT_URL = "https://avishpdfstorage.blob.core.windows.net"
CONTAINER_NAME = "pdfs"

def analyze_general_documents(doc_infos: dict) -> dict:
    retval = {}

    # document
    docUrl = "https://avishpdfstorage.blob.core.windows.net/pdfs/Ancient_Roman_architecture.pdf"

    # create your `DocumentAnalysisClient` instance and `AzureKeyCredential` variable
    document_analysis_client = DocumentAnalysisClient(endpoint=DI_ENDPOINT, credential=AzureKeyCredential(DI_KEY))

    for name, url in doc_infos.items():
        doc_text = analyze_general_document(document_analysis_client=document_analysis_client,
                                            url=url)
        retval[name] = doc_text

    return retval


def analyze_general_document(document_analysis_client: DocumentAnalysisClient, url: str):
    retval = ""

    poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-document", url)
    
    result = poller.result()

    for page in result.pages:
        retval = "".join(line.content for line in page.lines)
        
    return retval


def get_blob_infos(storage_account_string: str, container_name: str) -> dict:
    # ACCESS THE STORAGE ACCOUNT
    blob_service_client = BlobServiceClient.from_connection_string(STORAGE_STRING)
    
    # ACCES THE CONTAINER
    container_name = "pdfs"    
    container_client = blob_service_client.get_container_client(container=container_name)

    # ACCESS THE BLOBS, GET THEIR URLS
    blob_info = {}
    blobs_properties = container_client.list_blobs()
    for blob_property in blobs_properties:
        blob_client = container_client.get_blob_client(blob=blob_property.name)
        blob_url = blob_client.url
        blob_name = blob_client.blob_name
        blob_info[blob_name] = blob_url

    return blob_info


if __name__ == "__main__":
    documents_information = get_blob_infos(STORAGE_STRING, CONTAINER_NAME)

    documents_analysed = analyze_general_documents(doc_infos=documents_information)
    for name, text in documents_analysed.items():
        print(name, text, sep='\n')
        print('\n')



    #container_client.get_blob_client(blob=)
    # blob_service_client.get_blob_client(container=container_name, blob=)


    