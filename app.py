from langchain_openai import OpenAI
import getpass
import os
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import YoutubeLoader
import googleapiclient.discovery
import googleapiclient.errors
from langchain_community.document_loaders import PyPDFLoader
import nltk
import re
from youtube_transcript_api import YouTubeTranscriptApi

os.environ["OPENAI_API_KEY"] = getpass.getpass(prompt="Enter your OpenAI API key: ")
#api_key = 'AIzaSyCJayaCxJU5S3EqHI-RQPZcTvPxn0x3Ulk'
api_key = getpass.getpass(prompt="Enter your Youtube API key: ")

def summarize(link):
    prompt_template = '''Question: Write a summary of the following youtube video transcript in English in 300 words. Remember to give the answer in 1 paragraph.
    Transcript : "{transcript}" 
    '''
    prompt = PromptTemplate.from_template(prompt_template)

    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="transcript")

    loader = YoutubeLoader.from_youtube_url(
        link, add_video_info=False
    )
    docs = loader.load()
    return stuff_chain.invoke(docs)['output_text']

def youtube_stats(link):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=link
    )
    response = request.execute()
    
    channel_name = response['items'][0]['snippet']['channelTitle']
    likes = response['items'][0]['statistics']['likeCount']
    views = response['items'][0]['statistics']['viewCount']
    comment = response['items'][0]['statistics']['commentCount']
    channel_id = response['items'][0]['snippet']['channelId']
    return channel_name, likes, views, comment, channel_id

def channel_stats(link):
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        id=link
    )
    response = request.execute()    
    image = response['items'][0]['snippet']['thumbnails']['high']['url']
    sub = response['items'][0]['statistics']['subscriberCount']
    videos = response['items'][0]['statistics']['videoCount']
    return image, sub, videos

def basic_info(file):
    print(file)
    
    llm = OpenAI(temperature=0, max_tokens=2000)
    loader = PyPDFLoader(file)
    pages = loader.load_and_split()
    words = nltk.word_tokenize(pages[0].page_content)
    pos_tags = nltk.pos_tag(words)
    name=""
    i=0
    for chunk in pos_tags:
        if chunk[1] == "NNP" and i < 4:
            name +=  chunk[0] + " "
            i += 1
        else:
            break

    template = """CV:{pages} 

    Question: {question}
    """
    prompt = PromptTemplate(input_variables=["question", "pages"],  template=template)

    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    cad_name = name
    mail = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", pages[0].page_content).group(0)
    no = re.search(r"(\+\d{1,3}\s?)?(\d{3,4}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{1,4}[\s.-]?\d{3,6}", pages[0].page_content).group(0)
    summary = llm_chain.invoke({"pages":pages[0].page_content, "question": "Write a 100 words summary of the CV?"})["text"]
    key_points = llm_chain.invoke({"pages":pages[0].page_content, "question": "5 key points of the candidate?"})["text"]

    return cad_name, mail,  no, summary, key_points

def get_answer(question, file):
    print(question)
    if file:
        llm = OpenAI(temperature=0, max_tokens=2000)
        loader = PyPDFLoader(file)
        pages = loader.load_and_split()

        template = """ Your are HR's assistant. Give accurate on the point answers. 
        CV:{pages} 
        Question: {question}
        """

        prompt = PromptTemplate(input_variables=["question", "pages"],  template=template)

        llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
        llm_chain = LLMChain(llm=llm, prompt=prompt)

        answer = llm_chain.invoke({"pages":pages[0].page_content, "question": question})["text"]
        return answer