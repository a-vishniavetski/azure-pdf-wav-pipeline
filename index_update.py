"""Run this module to create or re-create an index in the Azure Cognitive Search service and at the same time to upload the documents, found in the associated
storage account, to the index."""
import os
import document_intelligence.document_analysis as document_analysis
import cognitive_search.cognitive_search as cognitive_search

# COGNITIVE SEARCH ENVIRONMENT VARIABLES
SEARCH_KEY = os.environ.get("COGSEARCH_KEY")
SEARCH_ENDPOINT = os.environ.get("COGSEARCH_ENDPOINT")
INDEX_NAME = "architecture"

# AZURE BLOB STORAGE ENVIRONMENT VARIABLES
STORAGE_STRING = os.environ.get("STORAGE_STRING1")  # Azure Storage Account Connection String
CONTAINER_NAME = "pdfs"  # Azure pdfs Blob Container  Name

# AZURE DOCUMENT INTELLIGENCE ENVIRONMENT VARIABLES
DI_KEY = os.environ.get("DI_KEY1") 
DI_ENDPOINT = os.environ.get("DI_ENDPOINT")


if __name__ == "__main__":
    # CREATE THE INDEX
    cognitive_search.create_search_index(INDEX_NAME, SEARCH_ENDPOINT, SEARCH_KEY)
    print("-----Index created successfully.-----")

    # GET THE DOCUMENT NAMES AND URLS
    blobs_info = document_analysis.get_blob_infos(STORAGE_STRING, CONTAINER_NAME)
    print("-----Blobs info retrieved successfully.-----")

    # GET THE DOCUMENTS' TEXT
    documents = document_analysis.analyze_general_documents(blobs_info, DI_ENDPOINT, DI_KEY)
    print("-----Documents analyzed successfully.-----")
    
    # UPLOAD DOCUMENTS TO THE INDEX
    cognitive_search.upload_documents_to_index(index_name=INDEX_NAME, 
                                               documents=documents,
                                               search_endpoint=SEARCH_ENDPOINT,
                                               search_key=SEARCH_KEY)
    print("-----Documents uploaded to index successfully.-----")
