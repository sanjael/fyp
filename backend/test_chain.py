print("1")

from app.core.evaluator_provider.factory import get_evaluator_provider
print("2")

import chromadb
print("3")

from langchain_community.vectorstores import Chroma
print("4")