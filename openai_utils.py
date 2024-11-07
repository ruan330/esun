# openai_utils.py

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import openai
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 知識庫 ID
KB_ID = 'LUTYK2W1HG'

# 初始化 Bedrock 客戶端
def initialize_bedrock_clients():
    session = boto3.session.Session()
    region = session.region_name or 'us-east-1'  # 如果 region_name 為 None，設置預設值
    bedrock_config = Config(
        connect_timeout=120,
        read_timeout=120,
        retries={'max_attempts': 0}
    )
    bedrock_client = boto3.client('bedrock-runtime', region_name=region)
    bedrock_agent_client = boto3.client(
        'bedrock-agent-runtime',
        config=bedrock_config,
        region_name=region
    )
    return bedrock_client, bedrock_agent_client, region

# 從 Bedrock 知識庫中檢索相關文件
def retrieve_documents(query, bedrock_agent_client, kb_id=KB_ID, number_of_results=5):
    try:
        response = bedrock_agent_client.retrieve(
            retrievalQuery={'text': query},
            knowledgeBaseId=kb_id,
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': number_of_results,
                    'overrideSearchType': 'HYBRID',
                }
            }
        )
        retrieval_results = response.get('retrievalResults', [])
        if not retrieval_results:
            return []
        contexts = [result['content']['text'] for result in retrieval_results]
        return contexts
    except ClientError as e:
        logger.error(f'在 retrieve_documents 中發生 ClientError：{e}')
        if e.response['Error']['Code'] == 'ThrottlingException':
            return ['請求過於頻繁，請稍後再試。']
        else:
            return [f'發生錯誤：{e}']
    except Exception as e:
        logger.error(f'在 retrieve_documents 中發生未知錯誤：{e}')
        return [f'發生錯誤：{e}']

# 初始化 OpenAI 客戶端
def initialize_openai_client(api_key):
    openai.api_key = api_key

# 使用 OpenAI 的 ChatCompletion 生成回應
def generate_response(contexts, query, model='gpt-4o-mini', max_tokens=512, temperature=0):
    combined_context = '\n'.join(contexts)
    messages = [
        {"role": "system", "content":  "Human: The following is a conversation between a human and an Al assistant."
        "The assistant is polite and responds to the user input and questions accurately and concisely."
        "The assistant remains on the topic and leverages available options efficiently."
        "The assistant uses the following pieces of retrieved-context to answer the question. If the assistant doesn't know the answer, say that you don't know. "
        "你是玉山銀行的專家，你的所有回答必須根據知識庫的內容，你需要使用繁體中文回答，從知識庫中搜尋對應該問題相關的文件或文章資訊。從相關文或章節中整理出與問題最相關的資訊作為回答。"
},
        {"role": "user", "content": f"上下文：\n{combined_context}\n\n問題：\n{query}"}
    ]
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=1,
            n=1
        )
        return response.choices[0].message['content'].strip()
    except openai.error.OpenAIError as e:
        logger.error(f'在 generate_response 中發生 OpenAIError：{e}')
        return f'發生錯誤：{e}'
    except Exception as e:
        logger.error(f'在 generate_response 中發生未知錯誤：{e}')
        return f'發生錯誤：{e}'

# 綜合調用 Bedrock 和 OpenAI 生成回應
def get_response(query, bedrock_client, bedrock_agent_client, openai_api_key, model_option):
    # 初始化 OpenAI 客戶端
    initialize_openai_client(openai_api_key)
    # 檢索相關文件
    contexts = retrieve_documents(query, bedrock_agent_client, KB_ID, number_of_results=5)
    if not contexts:
        return '抱歉，我無法找到相關資訊。', []

    # 根據 model_option 選擇適當的模型
    if model_option == 'gpt-3.5-turbo':
        model = 'gpt-3.5-turbo'
    elif model_option == 'gpt-4o-mini':
        model = 'gpt-4o-mini'
    elif model_option == 'gpt-4o':
        model = 'gpt-4o'
    else:
        model = 'gpt-3.5-turbo'  # 默認模型

    # 生成回應
    response_text = generate_response(contexts, query, model=model)
    return response_text, contexts  # 返回回應和上下文