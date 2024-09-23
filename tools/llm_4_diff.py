"""
Use gpt-4-turbo to summarise DeepDiff output
"""

import re
import string
import os
from openai import OpenAI
import tiktoken


os.environ['OPENAI_API_KEY'] = ""
os.environ['ORGANIZATION_KEY'] = ""
os.environ['PROJECT_KEY'] = ""

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
"Summary" : "Summarise the deepdiff results in less than 70 words, only highlighting the differences in the deepdiff result."
"Category" : "High/Medium/Low"
}

DeepDiff Output - 

'''

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    organization=os.environ.get("ORGANIZATION_KEY"),
    project=os.environ.get("PROJECT_KEY")
    )


def num_tokens_in_text(text, encoding_name="cl100k_base"):
    """ Function to calculate number of tokens contained in text"""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(text))
    return num_tokens


def preprocess_text(text):
    """Function to preprocess text for efficient retrieval"""
    # TO DO: Modify this for dict type data
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


# def tokenize(text):
#     """Function to split text into tokens"""
#     return preprocess_text(text).split()
 

# TO DO: Split input corpus into relevant key value pairs and retrieve only the relevant key value pairs as chunks

# def retrieve_relevant_chunks(query, corpus, top_n=2):
#     """Function to retrieve the most relevant text from input text"""
#     query_tokens = set(tokenize(query)) # user_message
#     similarities = []

#     corpus_tokens = set(tokenize(corpus)) # diff output
#     # using Jaccard similarity here
#     similarity = len(query_tokens.intersection(corpus_tokens)) / len(query_tokens.union(corpus_tokens))
    
#     similarities.append((corpus, similarity))
#     similarities.sort(key=lambda x: x[1], reverse=True)
#     return [chunk for chunk, _ in similarities[:top_n]]


def rag_prompt(query, corpus, top_n=2):
    """Function to use RAG to prompt gpt-4"""
    # relevant_chunks = retrieve_relevant_chunks(query, corpus, top_n)
    # if not relevant_chunks:
    #     return "Not enough information to summarise."

    context = "\n".join(corpus)
    completion = client.chat.completions.create(
        model="gpt-4-turbo", # the 128k model is quite expensive, esp given that diff tokens are extremely large. Either try using RAG or try vector embeddings next.
        messages=[
            {
                "role": "system",
                "content": f"{SYSTEM_MESSAGE} Based on the given context, answer this question: {query}\n\nContext:\n{context} "
            },
            {
                "role": "user",
                "content": query
            }
        ] 
    ) # TO DO: handle exceptions and retries
    return completion.choices[0].message.content


def direct_gpt_prompt(diff):
    """Direct prompting of gpt-4"""
    mod_user_message = USER_MESSAGE + str(diff)
    completion = client.chat.completions.create(
    model="gpt-4-turbo",
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
    ) # TO DO: handle exceptions and retries
    return completion.choices[0].message.content


def gpt_diff_output(diff):
    """ Function to call gpt-4 """
    # Check for token length. If token length >100000, use RAG, else send it to openai directly
    num_tokens = num_tokens_in_text(str(diff))
    if num_tokens < 20000:
        gpt_output = direct_gpt_prompt(diff)
    else:
        # Use simple RAG implementation to process this text
        corpus = preprocess_text(str(diff))
        gpt_output = rag_prompt(USER_MESSAGE, corpus)
    return gpt_output
