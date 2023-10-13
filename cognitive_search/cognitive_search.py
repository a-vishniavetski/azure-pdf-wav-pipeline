"""
This module provides functionality to create an index using Azure Cognitive Search and search through it. It uses the azure-search package to interact with the Azure Cognitive Search service.
"""
import os
from azure.core.credentials import AzureKeyCredential
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


