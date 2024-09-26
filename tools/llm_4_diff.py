"""
Use gpt-4o to summarise DeepDiff output
"""

import re
import string
import os
from openai import OpenAI
import tiktoken


os.environ['OPENAI_API_KEY'] = ''
os.environ['ORGANIZATION_KEY'] = ''
os.environ['PROJECT_KEY'] = ''

SYSTEM_MESSAGE = '''
You are a summarising agent part of a larger software tool that studies the interoperability of electronic medical records between different electronic health record (EHR) management systems. 
The tool passes a patient medical record in JSON or XML format from one EHR system to another and identifies the differences between the input patient file and the output patient file through that system. 
You're the agent that helps analyze the differences and convey it to the end user in an easy-to-understand form.  
'''

USER_MESSAGE = '''
The differences between the input and output patient medical records are in the form of DeepDiff outputs. 
Analyse the DeepDiff output and classify it into 3 categories of severity - High, Medium, and Low. 

High Severity:
Changes in critical patient personal information like name, date of birth, insurance, or emergency contact information.
Changes in critical medical information such as diagnosis, treatment, medications and dosage, lab results and sensitive data related to allergies, pre-existing conditions.
Any changes that could affect patient care or lead to misdiagnosis or incorrect treatment.

Medium Severity:
Missing or removal of demographic or administrative details of patient like contact number, gender, marital status, and address.
Removal of medical data that isn't immediately life-threatening or treatment-altering, like medical history of non-critical conditions.
Missing optional information such as secondary emergency contacts or treatment history.

Low Severity:
Changes in metadata, record ID values, timestamps (if not related to medical events).
Formatting changes such as whitespace, ordering of lists, or non-critical restructuring of data.
Minor alterations that do not impact the core medical data (e.g., changes in how a patient's name is displayed but not an actual change in the name).

Kindly return the result in the following JSON format only.

{
"Summary" : "Summarise the deepdiff results in less than 100 words, highlighting the differences in the deepdiff result."
"Category" : "High/Medium/Low"
}

The output should only be a JSON object.

DeepDiff Output - 

'''

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("ORGANIZATION_KEY"),
    project=os.environ.get("PROJECT_KEY")
    )

def num_tokens_in_text(text, encoding_name="cl100k_base"):
    """ Function to calculate number of tokens contained in text """
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens

def split_deepdiff_output(diff_output):
    """Split DeepDiff output into smaller chunks for processing."""
    chunks = []
    
    # From the output we get so far, we see the following keys
    if 'dictionary_item_added' in diff_output:
        dict_item_add = diff_output['dictionary_item_added']
        for item in dict_item_add:
            chunks.append(f"Item Added: {item}")
    if 'dictionary_item_removed' in diff_output:
        dict_item_rem = diff_output['dictionary_item_removed']
        for item in dict_item_rem:
            chunks.append(f"Item Removed: {item}")
    if 'values_changed' in diff_output:
        for key, value in diff_output['values_changed'].items():
            old_value = value['old_value']
            new_value = value['new_value']
            chunks.append(f"Value Changed at {key}: from {old_value} to {new_value}")

    return chunks

def tokenize(text):
    """Function to split text into tokens"""
    return re.findall(r'\w+', text.lower())

def retrieve_relevant_chunks(query, corpus, top_n=10):
    """Function to retrieve the most relevant chunks from the corpus"""
    query_tokens = set(tokenize(query))
    similarities = []

    for doc in corpus:
        doc_tokens = set(tokenize(doc))
        # Using Jaccard similarity
        union = query_tokens.union(doc_tokens)
        if not union:
            similarity = 0
        else:
            similarity = len(query_tokens.intersection(doc_tokens)) / len(union)
        similarities.append((doc, similarity))

    # Sort chunks by similarity score metric
    similarities.sort(key=lambda x: x[1], reverse=True)
    # Return top_n most relevant chunks from corpus
    return [chunk for chunk, _ in similarities[:top_n]]

def rag_prompt(query, context):
    """Function to use RAG to prompt GPT-4"""
    if not context:
        return "Not enough information to summarize."

    completion = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system",
                "content": f"{SYSTEM_MESSAGE}\nContext:\n{context}"
            },
            {
                "role": "user",
                "content": query
            }
        ] 
    )
    return completion.choices[0].message.content

def direct_gpt_prompt(diff_text):
    """Direct prompting of GPT-4"""
    mod_user_message = USER_MESSAGE + diff_text
    completion = client.chat.completions.create(
        model="gpt-4o",
        response_format={ "type": "json_object" },
        messages=[
            {
                "role": "system", 
                "content": SYSTEM_MESSAGE
            },
            {
                "role": "user", 
                "content": mod_user_message
            }
        ]
    )
    return completion.choices[0].message.content

def gpt_diff_output(diff):
    """ Function to call GPT-4 """
    # Split diff into chunks
    chunks = split_deepdiff_output(diff)
    
    # Calculate num of tokens to choose between RAG or not
    diff_text = "\n".join(chunks)
    num_tokens = num_tokens_in_text(diff_text)
    print(num_tokens)
    
    if num_tokens < 80000:
        # Send whole diff to GPT-4
        gpt_output = direct_gpt_prompt(diff_text)
    else:
        # RAG to find most relevant chunks
        relevant_chunks = retrieve_relevant_chunks(USER_MESSAGE, chunks, top_n=10)
        # Prepare the context from relevant chunks
        context = "\n".join(relevant_chunks)
        gpt_output = rag_prompt(USER_MESSAGE, context)
    
    return gpt_output