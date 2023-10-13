import os
import uuid
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


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
