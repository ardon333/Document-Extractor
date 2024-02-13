import spacy
import re
from spacy.matcher import Matcher
from spacy.language import Language
import streamlit as st
import spacy_streamlit
from PyPDF2 import PdfFileReader
import docx2txt
import io


# Load the model
nlp = spacy.load('en_core_web_sm')

# Define the patterns
pattern_email = [{"LIKE_EMAIL": True}]
pattern_aadhaar = [{"SHAPE": "dddd"}, {"ORTH": " ", "OP": "?"}, {"SHAPE": "dddd"}, {"ORTH": " ", "OP": "?"}, {"SHAPE": "dddd"}]
##pattern_mobile = [{"TEXT": {"REGEX": "((\d){5})"}}]
pattern_mobile = [{"TEXT": {"REGEX": r"(\b\d{10}\b)"}}]
pattern_pan = [{"SHAPE": "XXXXX"}, {"SHAPE": "dddd"}, {"SHAPE": "X"}]
pattern_gstin = [{"TEXT": {"REGEX": r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}\b"}}]
pattern_pan = [{"TEXT": {"REGEX": r"\b[A-Z]{5}\d{4}[A-Z]{1}\b"}}]
pattern_llpin = [{"TEXT": {"REGEX": r"\b[A-Z]{1}\d{5}\b"}}]
pattern_tan = [{"TEXT": {"REGEX": r"\b[A-Z]{4}\d{5}\b"}}]
pattern_bank_acc_num = [{"TEXT": {"REGEX": r"\b\d{9,18}\b"}}]
pattern_swift_code = [{"TEXT": {"REGEX": r"\b[A-Z]{6}[A-Z2-9][A-NP-Z0-9]([A-Z0-9]{3})?\b"}}]
pattern_ifsc_code = [{"TEXT": {"REGEX": r"\b[A-Z]{4}0[A-Z0-9]{6}\b"}}]
pattern_din = [{"TEXT": {"REGEX": r"\b\d{8}\b"}}]
pattern_pincode = [{"TEXT": {"REGEX": r"\b\d{6}\b"}}]
#Below is not working
pattern_id = [{"lower": "pan"}]




# Initialize the matcher and add the patterns
matcher = Matcher(nlp.vocab)
matcher.add("EMAIL", [pattern_email])
matcher.add("AADHAAR", [pattern_aadhaar])
matcher.add("MOBILE", [pattern_mobile])
matcher.add("PAN", [pattern_pan])
matcher.add("GSTIN", [pattern_gstin])
matcher.add("LLPIN", [pattern_llpin])
matcher.add("TAN", [pattern_tan])
matcher.add("BANK_ACC_NUM", [pattern_bank_acc_num])
matcher.add("SWIFT_CODE", [pattern_swift_code])
matcher.add("IFSC_CODE", [pattern_ifsc_code])
matcher.add("DIN", [pattern_din])
matcher.add("PINCODE", [pattern_pincode])
matcher.add("ID", [pattern_id])


# Define the custom component
@Language.component("custom_entity_ruler")
def custom_entity_ruler(doc):
    matches = matcher(doc)
    new_entities = []
    for match_id, start, end in matches:
        span = spacy.tokens.Span(doc, start, end, label=nlp.vocab.strings[match_id])
        # Only add the span if it doesn't overlap with existing entities
        if not any([span.start < ent.end and span.end > ent.start for ent in new_entities]):
            new_entities.append(span)
    doc.ents = new_entities
    return doc

# Add the custom component to the pipeline before 'ner'
nlp.add_pipe("custom_entity_ruler", before='ner')

# Streamlit code for the user interface
st.title('GPT Anonymizes')

# Text input
user_text = st.text_area("Enter Text", 'Your text goes here...')
# File uploader
uploaded_file = st.file_uploader("Upload a file", type=["txt", "docx", "pdf"])
# Read the file contents if uploaded
if uploaded_file is not None:
    if uploaded_file.type == "text/plain":
        # Text file
        user_text = io.TextIOWrapper(uploaded_file, encoding="utf-8").read()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Docx file
        docx_bytes = uploaded_file.read()
        user_text = docx2txt.process(io.BytesIO(docx_bytes))
    elif uploaded_file.type == "application/pdf":
        # PDF file
        pdf_bytes = uploaded_file.read()
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_reader = PdfFileReader(pdf_io)
        user_text = ""
        for page in range(pdf_reader.getNumPages()):
            user_text += pdf_reader.getPage(page).extractText()



colors = {"ORG": "linear-gradient(90deg, #aa9cfc, #fc9ce7)"}
options = {"ents": ["ORG"], "colors": colors}


# NER visualization button
if st.button('Visualize NER'):
    doc = nlp(user_text)
    spacy_streamlit.visualize_ner(doc)

# Define a function to redact names in a text
if st.button('Redact'):
    doc = nlp(user_text)
    redacted_text = user_text
    entities_to_redact = ['PERSON', 'GPE', 'ORG', 'MOBILE', 'GSTIN', 'AADHAAR', 'EMAIL', 'PAN', 'PAN_NO', 'BANK_ACC_NUM', 'IFSC_CODE', 'SWIFT_CODE', 'DIN', 'LLPIN', 'TAN', 'PINCODE']

    # Create a dictionary to store unique placeholders for each entity label
    placeholders = {}
    person_counter = 1  # Counter for person entities
    person_dict = {}  # Dictionary to track person tags for the same name

    # Iterate over entities in reverse order to not mess up the start and end character indices
    for ent in reversed(doc.ents):
        if ent.label_ in entities_to_redact:
            start = ent.start_char
            end = ent.end_char
            label = ent.label_

            # Create a placeholder if it doesn't exist for the label
            if label not in placeholders:
                placeholders[label] = f'[REDACTED_{label}]'

            placeholder = placeholders[label]

            # Check if the entity is a person and update the placeholder and person tag accordingly
            if label == 'PERSON':
                name = ent.text
                if name not in person_dict:
                    person_dict[name] = f'[REDACTED_PERSON_{person_counter}]'
                    person_counter += 1
                placeholder = person_dict[name]

            redacted_text = redacted_text[:start] + placeholder + redacted_text[end:]

    st.write(redacted_text)