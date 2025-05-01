from docling.document_converter import DocumentConverter
from langchain.prompts import PromptTemplate
from src.config import llm
from src.prompt_template import invoice_prompt
def process_pdf(path: str) -> str:
    """Convert PDF receipt to markdown."""
    converter = DocumentConverter()
    result = converter.convert(path)
    return result.document.export_to_markdown()

def extract_receipt_data(receipt_text: str) -> str:
    """Generate SQL INSERT query from receipt markdown."""
    template = PromptTemplate(
        template=invoice_prompt
    )

    chain = template | llm
    response = chain.invoke({"receipt": receipt_text})
    return response.content