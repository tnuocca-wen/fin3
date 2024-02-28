import os, json
import openai
from openai import OpenAI
import pdftotext
import re
import requests
from .bucket import upload_blob, file_exists, download_blob, download_folder, upload_folder, list_blobs
from django.shortcuts import HttpResponse
import chromadb
from chromadb.utils import embedding_functions
import nltk
import tiktoken
import string
import pandas as pd
from transformers import pipeline
from .models import Company

client = OpenAI()
openai.api_key = os.environ["OPENAI_API_KEY"]


def text_extraction(path):
  with open(path, "rb") as f:
      pdf = pdftotext.PDF(f)
  text = []
  # All pages
  for txt in pdf:
    text.append(txt)
  return text


def text_extractionTXT(path):
  with open (path, 'r', encoding="utf8") as f:
    txt = f.read()
  # for txt in pdf:
  return txt


def split_into_paragraphs(long_string):
    paragraphs = re.split(r'\n{1,}', long_string)
    return paragraphs


def split_into_sentences(text):
  tokenizer = nltk.data.load(f"/static/nltk_punkt/tokenizers/punkt/english.pickle")
  return tokenizer.tokenize(text)

def num_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def remove_punct(input_string):
  return input_string.translate(str.maketrans('', '', string.punctuation)).lower()

def count_words(input_string):
    words = input_string.split()
    return len(words)

def namingFunc(pdf):
  parts = pdf.split('/')
  compID = parts[-4]
  qurtr = parts[-2]
  year = parts[-3]
  print(pdf)
  return [compID, year, qurtr]

def download_pdf(link, path):
  headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
  res = requests.get(link, headers=headers)
  print(res)
  # os.remove(path)
  if not os.path.exists('/'.join(path.split('/')[0:-1])):
     os.makedirs('/'.join(path.split('/')[0:-1]))
  with open(path, 'wb+') as pdf:
    pdf.write(res.content)
    pdf.close()
  if not file_exists(f"fin/{path.split('/')[-4]}/{path.split('/')[-3]}/{path.split('/')[-2]}/{path.split('/')[-4]}.pdf"):
    upload_blob(path, f"fin/{path.split('/')[-4]}/{path.split('/')[-3]}/{path.split('/')[-2]}/{path.split('/')[-4]}.pdf")
    if not file_exists(f"fin/{path.split('/')[-4]}/{path.split('/')[-3]}/{path.split('/')[-2]}/db/chroma.sqlite3"):
      create_vectors(path.split('/')[-4],path.split('/')[-3],path.split('/')[-2])

def upload_data(request):
   if request.method == 'POST':
      data = json.loads(request.POST.get('dat'))
      if int(data['sr']) == 1:
        finfl = "summary"
      else:
         finfl = "keytakeaways"
      if data['done'] == True:
        with open(f'static/documents/{data["tic"]}/{data["yr"]}/{data["qr"]}/{finfl}/{data["tic"]}.txt', "r+") as f:
          t = f.read()
          if t != '':
            upload_blob(f'static/documents/{data["tic"]}/{data["yr"]}/{data["qr"]}/{finfl}/{data["tic"]}.txt', f'fin/{data["tic"]}/{data["yr"]}/{data["qr"]}/{finfl}/{data["tic"]}.txt')
        return HttpResponse("Uploaded")
      return HttpResponse("Not Uploaded")


def summarize_stream(model, text_list, tic, yr, qr):
  summary = []
  for para in text_list:
    print('')
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a business analyst with expertise in summarizing business meeting transcripts."},
            {"role": "user", "content": f'''summarize the following paragraph with
            short simple sentences. If you encounter any difficulty, just don't say anything about it: "{para}"'''}
            ],
        temperature = 0,
        stream = True
        )
    collected_chunks = []
    collected_messages = []
    for chunk in completion:
        collected_chunks.append(chunk)
        chunk_message = chunk.choices[0].delta.content 
        collected_messages.append(chunk_message)
        # print(chunk_message, end='')
        yield chunk_message if chunk_message is not None else ''
    
    collected_messages = [m for m in collected_messages if m is not None]
    summary.append(''.join([m for m in collected_messages]))
    yield "<br><br>"
    
  summary = '\n\n'.join(summary)
  if not os.path.exists(f'static/documents/{tic}/{yr}/{qr}/summary/'):
      os.makedirs(f'static/documents/{tic}/{yr}/{qr}/summary/')
  with open(f'static/documents/{tic}/{yr}/{qr}/summary/{tic}.txt', 'w+', encoding='utf-8') as sum:
      sum.write(summary)
      sum.close()


def takeaways (model, text_list, tic, yr, qr):
  takeaways = ''
  full_summary = '\n\n'.join(text_list)

  completion = client.chat.completions.create(
      model=model,
      messages=[
          {"role": "system", "content": "You are a business analyst."},
          {"role": "user", "content": f'''list out key takeaways from the following text: "{full_summary}"'''}
          ],
      temperature=0,
      stream=True,)
  collected_chunks = []
  collected_messages = []
  for chunk in completion:
      collected_chunks.append(chunk)
      chunk_message = chunk.choices[0].delta.content 
      collected_messages.append(chunk_message)
      # print(chunk_message, end='')
      yield chunk_message if chunk_message is not None else ''
  
  collected_messages = [m for m in collected_messages if m is not None]
  takeaways = ''.join([m for m in collected_messages])
    
  if not os.path.exists(f'static/documents/{tic}/{yr}/{qr}/keytakeaways/'):
      os.makedirs(f'static/documents/{tic}/{yr}/{qr}/keytakeaways/')
  with open(f'static/documents/{tic}/{yr}/{qr}/keytakeaways/{tic}.txt', 'w+', encoding='utf-8') as tk:
      tk.write(takeaways)
      tk.close()
  elab_gen(tic, yr, qr, 5, -1)

def create_vectors(ticker, year, qrtr):
  if os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf"):
    pdf_path = f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf"
    if not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/db"):
      os.makedirs(f"static/documents/{ticker}/{year}/{qrtr}/db")
    if not file_exists(f"fin/{ticker}/{year}/{qrtr}/db/chroma.sqlite3"):
      chclient = chromadb.PersistentClient(path=f"static/documents/{ticker}/{year}/{qrtr}/db")
      exst = 1
    else:
      exst = 0
  elif file_exists(f"fin/{ticker}/{year}/{qrtr}/{ticker}.pdf") and not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf"):
    download_blob(f"fin/{ticker}/{year}/{qrtr}/{ticker}.pdf", f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf")
    pdf_path = f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf"
    if not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/db"):
      os.makedirs(f"static/documents/{ticker}/{year}/{qrtr}/db")
    if not file_exists(f"fin/{ticker}/{year}/{qrtr}/db/chroma.sqlite3"):
      chclient = chromadb.PersistentClient(path=f"static/documents/{ticker}/{year}/{qrtr}/db")
      exst = 1
    else:
      exst = 0
  else:
    try:
        c = Company.objects.get(pk=ticker).pdf_data_set.all()[0]
    except:
        c = None
    if c is not None:
        wrkarr = c.pdfs
        if wrkarr != []:
            print(wrkarr)
            print("enter if you have pdfs")
            for i in wrkarr:
                # if i != []:
                # print(i[1], i[2])
                # print(type(year), type(qrtr))
                if str(i[1]) == year and str(i[2]) == qrtr:
                    print("enter if pdfs are a match for y a q")
                    pdf = i[0] #if c.pdf1 != [] else ''
                    yr = i[1] # if c.pdf1 != [] else ''
                    qr = i[2] # if c.pdf1 != [] else ''
                    pdf_path = f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf"
                    download_pdf(pdf, pdf_path)
                    if not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/db"):
                      os.makedirs(f"static/documents/{ticker}/{year}/{qrtr}/db")
                      if not file_exists(f"fin/{ticker}/{year}/{qrtr}/db/chroma.sqlite3"):
                        chclient = chromadb.PersistentClient(path=f"static/documents/{ticker}/{year}/{qrtr}/db")
                        exst = 1
                      else:
                        exst = 0
                    break
                else:
                    yr = ''
                    qr = ''
                    pdf = ''
                    exst = -1
        else:
            yr = ''
            qr = ''
            pdf = ''
            return 1
  if exst == -1:
    return 1
  if exst == 1:
    texts = text_extraction(pdf_path)
    sentences = []
    for i in texts:
      sentences += split_into_sentences(i)

    #corpus
    corpus = []
    for i in range(len(texts) - 4):
      # Concatenate the current element with the next four elements and append to the new list
      concatenated_string = ''.join(texts[i:i+5])
      corpus.append(concatenated_string)

    #cleaned corpus
    cleaned_corpus = []
    for doc in corpus:
      cleaned_doc = remove_punct(doc)
      cleaned_corpus.append(cleaned_doc)

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    model_name="text-embedding-ada-002"
                )

    collection = chclient.get_or_create_collection(name="Sentences")

    embeddings = openai_ef([i for i in cleaned_corpus])
    print(embeddings)

    collection.add(
        embeddings = embeddings,
        documents = [i for i in cleaned_corpus],
        metadatas = [{"source":f"{i+1}"} for i, s in enumerate(cleaned_corpus)],
        ids = [f"id{i+1}" for i, s in enumerate(cleaned_corpus)]
    )

    upload_folder(f"static/documents/{ticker}/{year}/{qrtr}/db", f"fin/{ticker}/{year}/{qrtr}/db")
  else:
    pass


def kt_search(text, ticker, year, qrtr):
  print(text, ticker, year, qrtr)
  if file_exists(f"fin/{ticker}/{year}/{qrtr}/db/chroma.sqlite3"):

    if not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/db/chroma.sqlite3"):
      download_folder(f"fin/{ticker}/{year}/{qrtr}/db", f"static/documents/{ticker}/{year}/{qrtr}/db")

    chclient = chromadb.PersistentClient(path=f"static/documents/{ticker}/{year}/{qrtr}/db")

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-ada-002")
    collection = chclient.get_or_create_collection(name="Sentences", embedding_function=openai_ef)

    # print([i for i in ktaways])

    seres = collection.query(
    query_texts=[text],
    n_results=1)

    return seres["documents"][0][0]
  else:
    print("creating vector")
    create_vectors(ticker, year, qrtr)
    try:
      chclient = chromadb.PersistentClient(path=f"static/documents/{ticker}/{year}/{qrtr}/db")

      openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                  model_name="text-embedding-ada-002")
      collection = chclient.get_or_create_collection(name="Sentences", embedding_function=openai_ef)

      # print([i for i in ktaways])

      seres = collection.query(
      query_texts=[text],
      n_results=1)

      return seres["documents"][0][0]
    except:
      return ""
  

def elaborate(query, note, ticker, year, qrtr):
  data = kt_search(query, ticker, year, qrtr)
  if data != "":
    if num_tokens(data) > 2000:
      encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
      data = encoding.decode(encoding.encode(data)[:2000])
    print(num_tokens(data))
    message = f'''Elaborate this key takeaway from the quarterly earnings conference call of the company with ticker {ticker} for the quarter {qrtr} of the Fiancial Year {year},
    Sentence: `{query}`,
    {note}. based on the following extract.
    Extract: {data}'''

    messages = [
        {"role": "system", "content": "You are very good at efficiently elaborating small sentences based on the provided context."},
        {"role": "user", "content": message},
      ]

    response = client.chat.completions.create(
        model= "gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        stream = True
        )
    # collected = []
    # collected_msgs = []
    for chunk in response:
      # collected.append(chunk)
      chunk_msg = chunk.choices[0].delta.content
      # collected_msgs.append(chunk_msg)
      yield chunk_msg if chunk_msg is not None else ''
    
    # collected_msgs = [m for m in collected_msgs if m is not None]

    # response = response.choices[0].message.content
    # print(message)
    # print(response)
    # return response
  else:
    return ""
  
df = None
dfinit = 0
def dfinitfn(ticker, year, qrtr):
  global df, dfinit
  try:
    if not pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv").empty:
      df = pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
    else:
      df = pd.DataFrame()
  except:
    df = pd.DataFrame()
  dfinit = 1

ktelabq = []
def elab_gen(ticker, year, qrtr, wq, id):
  global ktelabq, df, dfinit
  if file_exists(f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt") and (not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt")):
    if not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/"):
      os.makedirs(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways")
    download_blob(f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt", f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt")
    path = f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt"
  else:
    path = f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.txt"

  kttexts = text_extractionTXT(path)
  ktaways = []
  sent = kttexts.split('\n')
  for i in sent:
    if i != '':
      ktaways.append(i)

  print(kttexts)

  # tempkt = []
  indicators = ['key', 'takeaways', 'takeaways:']
  # for i in range(len(ktaways)):
  tkt = []
  for j in range(len(ktaways)):
    if j==0:
      split = ktaways[j].lower().split()
      try:
        for w in range(len(split)):
          if indicators[0] == split[w] and (indicators[1] == split[w+1] or indicators[2] == split[w+1]):
            tf = True
            break
          else :
            tf = False
      except IndexError:
        tf = False
    if (j==0 and tf): #or (ktaways[j]==''):
      pass# print(ktaways[j])
    else:
      x = ktaways[j].find(" ")
      tkt.append(ktaways[j][(x+1):])
  ktaways = tkt
  del tkt
  if wq == 0:
    df = pd.DataFrame()
    top1 = []
    top2 = []
    top3 = []
    for i in ktaways:
      top1.append(elaborate(i, '', ticker, year, qrtr))
      pyear = str(eval(year) - 1) if ((eval(qrtr)-2+4)%4)+1 == 4 else year
      if os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt"):
        top2.append(elaborate(i, '',ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
      elif file_exists(f"fin/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt") and not os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt"):
        if not os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways"):
          os.makedirs(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways")
        download_blob(f"fin/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt", f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt")
        top2.append(elaborate(i, '',ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
      ppyear = eval(year) - 1 if ((eval(qrtr)-3+4)%4)+1 == 3 or ((eval(qrtr)-3+4)%4)+1 == 4 else year
      if os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt"):
        top3.append(elaborate(i, '',ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)))
      elif file_exists(f"fin/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt") and not os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt"):
        if not os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways"):
          os.makedirs(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways")
        download_blob(f"fin/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt", f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt")
        top3.append(elaborate(i, '',ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)))
    if top1 != ["" for i in range(len(top1))] or top2 != ["" for i in range(len(top2))] or top3 != ["" for i in range(len(top3))]:
      df["takeaways"] = ktaways
      df["elaboration1"] = top1
      df["elaboration2"] = top2
      df["elaboration3"] = top3
      df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
  elif wq == 1:
    # try:
    #   if not pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv").empty:
    #     n = 0
    #     df = pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
    #   else:
    #     n = 1
    #     df = pd.DataFrame()
    # except:
    #   n = 1
    #   df = pd.DataFrame()
    if dfinit != 1:
      dfinitfn(ticker, year, qrtr)
    
    ktelabq.append(1)
    # top1 = []
    collected_msgs = []
    # lat = 0
    for j in elaborate(ktaways[id], '',ticker, year, qrtr):
      collected_msgs.append(j)
      yield j
    # top1.append(''.join(collected_msgs))
    df["elaboration1"] = df["elaboration1"].astype('object')
    df.at[id, "elaboration1"] = ''.join(collected_msgs)
    # for n, i in enumerate(ktaways):
    #   if n == id:
    #     continue
    #   collected_msgs = []
    #   for j in elaborate(i, ticker, year, qrtr):
    #     collected_msgs.append(j)
    #     # yield j
    #   if n < id:
    #     top1.insert(lat, ''.join(collected_msgs))
    #     lat += 1
    #   else:
    #     top1.append(''.join(collected_msgs))

    # if top1 != ["" for i in range(len(top1))]:
    # if n == 1:
    #   df["takeaways"] = ktaways
      # df["elaboration1"] = top1
    df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")

    ktelabq = [el for el in ktelabq if el != 1]
    # upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
    # else:
    #   # df["elaboration1"] = top1
    #   df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", index = False)
    #   upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
  elif wq == 2:
    print("first option")
    # try:
    #   if not pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv").empty:
    #     n = 0
    #     df = pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
    #   else:
    #     n = 1
    #     df = pd.DataFrame()
    # except:
    #   n = 1
    #   df = pd.DataFrame()
    if dfinit != 1:
      dfinitfn(ticker, year, qrtr)
    
    ktelabq.append(2)

    fnd = 0
    # top2 = []
    # for i in ktaways:
    pyear = str(eval(year) - 1) if ((eval(qrtr)-2+4)%4)+1 == 4 else year
    print(pyear)
    if os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt"):
      # top2.append(elaborate(i, ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
      collected_msgs = [] 
      # lat = 0
      for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-2+4)%4)+1)} of the Financial Year {pyear}, 
                         which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''', ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)):
        collected_msgs.append(j)
        yield j
      # top1.append(''.join(collected_msgs))
      fnd = 1
    elif file_exists(f"fin/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt") and not os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt"):
      if not os.path.exists(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways"):
        os.makedirs(f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways")
      download_blob(f"fin/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt", f"static/documents/{ticker}/{pyear}/{str(((eval(qrtr)-2+4)%4)+1)}/keytakeaways/{ticker}.txt")
      # top2.append(elaborate(i, ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
      collected_msgs = []
      # lat = 0
      for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-2+4)%4)+1)} of the Financial Year {pyear}, 
                         which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''', ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)):
        collected_msgs.append(j)
        yield j
      # top1.append(''.join(collected_msgs))
      # df["elaboration1"] = df["elaboration1"].astype('object')
      # df.at[id, "elaboration1"] = ''.join(collected_msgs)
      fnd = 1
    else:
      if create_vectors(ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)) == 1:
        yield "<strong>Pdfs</strong> for this quarter was <strong>not found</strong>"
      else:
        # create_vectors(ticker, pyear, str(((eval(qrtr)-2+4)%4)+1))
        # top2.append(elaborate(i, ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
        collected_msgs = [] 
        # lat = 0
        for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-2+4)%4)+1)} of the Financial Year {pyear}, 
                          which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''', ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)):
          collected_msgs.append(j)
          yield j
        # top1.append(''.join(collected_msgs))
        fnd = 1
    if fnd == 1:
      df["elaboration2"] = df["elaboration2"].astype('object')
      df.at[id, "elaboration2"] = ''.join(collected_msgs)
      # if top2 != []:
      # if n == 1:
        # df["takeaways"] = ktaways
        # df["elaboration2"] = top2
      df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      ktelabq = [el for el in ktelabq if el != 2]
      # upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      # else:
      #   # df["elaboration2"] = top2
      #   df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", index=False)
      #   upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
  elif wq == 3:
    print("second option")
    # try:
    #   if not pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv").empty:
    #     n = 0
    #     df = pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
    #   else:
    #     n = 1
    #     df = pd.DataFrame()
    # except:
    #   n = 1
    #   df = pd.DataFrame()
    if dfinit != 1:
      dfinitfn(ticker, year, qrtr)

    ktelabq.append(3)
    # top3 = []
    fnd = 0
    # for i in ktaways:
    ppyear = str(eval(year) - 1) if ((eval(qrtr)-3+4)%4)+1 == 3 or ((eval(qrtr)-3+4)%4)+1 == 4 else year
    print(ppyear)
    if os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt"):
      # top2.append(elaborate(i, ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
      collected_msgs = []
      # lat = 0
      for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-3+4)%4)+1)} of the Financial Year {ppyear}, 
                         which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''',ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)):
        collected_msgs.append(j)
        yield j
      # top1.append(''.join(collected_msgs))
      fnd = 1
    elif file_exists(f"fin/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt") and not os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt"):
      if not os.path.exists(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways"):
        os.makedirs(f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways")
      download_blob(f"fin/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt", f"static/documents/{ticker}/{ppyear}/{str(((eval(qrtr)-3+4)%4)+1)}/keytakeaways/{ticker}.txt")
      # top3.append(elaborate(i, ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)))
      collected_msgs = []
      # lat = 0
      for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-3+4)%4)+1)} of the Financial Year {ppyear}, 
                         which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''',ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)):
        collected_msgs.append(j)
        yield j
      # top1.append(''.join(collected_msgs))
      # df["elaboration1"] = df["elaboration1"].astype('object')
      # df.at[id, "elaboration1"] = ''.join(collected_msgs)
      fnd = 1
    else:
      if create_vectors(ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)) == 1:
        yield "<strong>Pdfs</strong> for this quarter was <strong>not found</strong>"
      else:
        # create_vectors(ticker, pyear, str(((eval(qrtr)-2+4)%4)+1))
        # top2.append(elaborate(i, ticker, pyear, str(((eval(qrtr)-2+4)%4)+1)))
        collected_msgs = [] 
        # lat = 0
        for j in elaborate(ktaways[id], f'''It is important to note that the following extract is from the earnings conference call of the company with the ticker {ticker} for the quarter {str(((eval(qrtr)-3+4)%4)+1)} of the Financial Year {ppyear}, 
                          which is the last quarter. The extract from the last quarter is given so that the general idea in the current quarter's key takeaway can be checked against the last quarter to see what the sentiments were towards this idea in the last quarter.''', ticker, ppyear, str(((eval(qrtr)-3+4)%4)+1)):
          collected_msgs.append(j)
          yield j
        # top1.append(''.join(collected_msgs))
        fnd = 1
    if fnd == 1:
      df["elaboration3"] = df["elaboration3"].astype('object')
      df.at[id, "elaboration3"] = ''.join(collected_msgs)
      # if top3 != []:
      # if n == 1:
        # df["takeaways"] = ktaways
        # df["elaboration3"] = top3
      df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      ktelabq = [el for el in ktelabq if el != 3]
      # upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      # else:
      #   # df["elaboration3"] = top3
      #   df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", index=False)
      #   upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
  elif wq == 5:
    try:
      if not pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv").empty:
        n = 0
        df = pd.read_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")
      else:
        n = 1
        df = pd.DataFrame()
    except:
      n = 1
      df = pd.DataFrame()
    print("yoyo")
    print(len(ktaways))
    df["takeaways"] = ktaways
    df["elaboration1"] = ["" for i in range(len(ktaways))]
    df["elaboration2"] = ["" for i in range(len(ktaways))]
    df["elaboration3"] = ["" for i in range(len(ktaways))]
    df.to_csv(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", index=False)
    # upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")

  if ktelabq == []:
    dfinit = 0
    df = None
    upload_blob(f"static/documents/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv", f"fin/{ticker}/{year}/{qrtr}/keytakeaways/{ticker}.csv")


def sentiment_gen(ticker, year, qrtr):
  sentiment_pipeline = pipeline('sentiment-analysis', model="static\sent_model", tokenizer="static\sent_model")
  # names = namingFunc(name)

  items = split_into_sentences(''.join(text_extraction(f"static/documents/{ticker}/{year}/{qrtr}/{ticker}.pdf")))
  sent_count = len(items)
  sentiment_list = []
  positive_sent = []
  negative_sent = []
  neutral_sent = []

  for item in items:
    sentiment = sentiment_pipeline(item)[0]['label']
    sentiment_list.append (sentiment)

    if sentiment == 'positive':
      positive_sent.append(item)
    elif sentiment == 'negative':
      negative_sent.append(item)
    else:
      neutral_sent.append(item)

  neutral = sentiment_list.count('neutral')/sent_count
  positive = sentiment_list.count ('positive')/sent_count
  negative = sentiment_list.count ('negative')/sent_count
  score = [positive, neutral, negative]
  if os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/"):
    pass
  else:
    os.makedirs(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/")
  with open(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt","w+", encoding="utf8") as fp:
    for i in score:
        fp.write(str(i)+"\n")
  with open(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_POS.txt","w+", encoding="utf8") as fp:
    for i in positive_sent:
      i = re.sub(r"\n+"," ",i)
      fp.write(i+"\n")
  with open(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEG.txt","w+", encoding="utf8") as fp:
    for i in negative_sent:
      i = re.sub(r"\n+"," ",i)
      fp.write(i+"\n")
  with open(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEU.txt","w+", encoding="utf8") as fp:
    for i in neutral_sent:
      i = re.sub(r"\n+"," ",i)
      fp.write(i+"\n")
  
  upload_folder(f"static/documents/{ticker}/{year}/{qrtr}/sentiment", f"fin/{ticker}/{year}/{qrtr}/sentiment")


def sentiment_gen_all(ticker):
  years = list_blobs(f"fin/{ticker}/","/")[1]
  scores = []
  pos = []
  neg = []
  neu = []
  try:
      c = Company.objects.get(pk=ticker).pdf_data_set.all()[0]
  except:
      c = None
  for year in years:
    qrtrs = list_blobs(f"fin/{ticker}/{year}/", "/")[1]
    for qrtr in qrtrs:
      if file_exists(f"fin/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt") and not os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt"):
        download_folder(f"fin/{ticker}/{year}/{qrtr}/sentiment", f"static/documents/{ticker}/{year}/{qrtr}/sentiment")
        scores.append([year, qrtr, [i for i in text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt").strip().split("\n")]])
        pos.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_POS.txt")])
        neg.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEG.txt")])
        neu.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEU.txt")])
        if c is not None:
            wrkarr = c.pdfs
            if wrkarr != []:
                print(wrkarr)
                print("enter if you have pdfs")
                for i in wrkarr:
                    if str(i[1]) == year and str(i[2]) == qrtr:
                      continue
                    else:
                      scores.append([year, qrtr, []])
                      pos.append([year, qrtr, ""])
                      neg.append([year, qrtr, ""])
                      neu.append([year, qrtr, ""])
            else:
                continue
      elif os.path.exists(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt"):
        scores.append([year, qrtr, [i for i in text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_SCO.txt").strip().split("\n")]])
        pos.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_POS.txt")])
        neg.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEG.txt")])
        neu.append([year, qrtr, text_extractionTXT(f"static/documents/{ticker}/{year}/{qrtr}/sentiment/{ticker}_NEU.txt")])
      else:
        pass
  return [scores, pos, neg, neu]
