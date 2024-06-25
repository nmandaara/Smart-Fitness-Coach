"""
This utility encapsulates LangChain agent that can be
used to answer questions about the Fitness Db and users
can get personalized recommendations. 
"""
import os
import logging
import json
from pymongo import MongoClient
from datetime import datetime, timedelta
from pymongo.errors import DuplicateKeyError
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureCosmosDBVectorSearch
from langchain.schema.document import Document
from langchain.agents import Tool
from langchain.tools import StructuredTool
from langchain.chat_models import AzureChatOpenAI
from langchain.agents.agent_toolkits import create_conversational_retrieval_agent
from openai import AzureOpenAI
from app.models import User
from typing import List, Optional
from langchain_core.messages import SystemMessage

# Configure Logger
logger = logging.getLogger()
handler = logging.StreamHandler()
format = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Fetch the details from env")
load_dotenv()

# Fetch environment Variables
keyvault_uri = os.getenv("AKV_URL")
app_clientid=os.getenv("CLIENT_ID")
app_clientsecret= os.getenv("CLIENT_SECRET")
app_tenantid = os.getenv("TENANT_ID")

# Fetch secrets from KeyVault
credentials = ClientSecretCredential(client_id=app_clientid, client_secret=app_clientsecret, tenant_id=app_tenantid)
secret_client = SecretClient(vault_url=keyvault_uri, credential=credentials)

logger.info("Connected to Keyvault. Fetching the secrets")

MONGODB_CONNECTION_STRING = secret_client.get_secret("mongodb-connection-string").value
OPENAI_API_KEY = secret_client.get_secret("openai-api-key").value
OPENAI_PROXY_ENDPOINT = secret_client.get_secret("openai-proxy-endpoint").value

logger.info("Secrets fetched successfully")

# MongoDB related Connections
mongodb_client = MongoClient(MONGODB_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True)
database = mongodb_client.get_database("smart-fitness")
users_collection = database.get_collection("users")
workout_collection = database.get_collection("workouts")
user_history_collection = database.get_collection("user_history")
challenges_collection = database.get_collection("challenges")
challenge_history_collection = database.get_collection("challenge_history")

# AzureOpenAI, Chat and Embeddings
openai_client = AzureOpenAI(
    azure_endpoint=OPENAI_PROXY_ENDPOINT,
    api_key=OPENAI_API_KEY,
    api_version="2024-02-01"
)
llm = AzureChatOpenAI(            
        temperature = 0,
        openai_api_version = "2024-02-01",
        azure_endpoint = OPENAI_PROXY_ENDPOINT,
        openai_api_key = OPENAI_API_KEY,         
        azure_deployment = "gpt-4" #check this again
)

embedding_model = AzureOpenAIEmbeddings(
    openai_api_version = "2024-02-01",
    azure_endpoint = OPENAI_PROXY_ENDPOINT,
    openai_api_key = OPENAI_API_KEY,   
    azure_deployment = "embeddings",
    chunk_size=10
)

# Function creates Vector Store Retriever based on the collection given
def create_vector_store_retriever(collection_name: str, top_k: int=3):
    vector_store = AzureCosmosDBVectorSearch.from_connection_string(
        connection_string=MONGODB_CONNECTION_STRING,
        namespace=f"smart-fitness.{collection_name}",
        embedding=embedding_model,
        index_name="VectorSearchIndex",
        embedding_key="contentVector",
        text_key="_id"
    )
    return vector_store.as_retriever(search_kwargs={"k": top_k})

# Function to add a user to the DB
def add_user(user):
    try:
        user_dict = user.dict(by_alias=True)
        print(user_dict)
        users_collection.insert_one(user.dict())
        return {"status":"user added", "user":user_dict}
    except DuplicateKeyError:
        raise ValueError("user already exists")

# For every workout entered into the Database,
# This function runs and enters the info into challenge_history
def check_challenges(username):
    # Weekly challenge
    one_week_ago = str(datetime.now() - timedelta(days=7))
    weekly_calories = workout_collection.aggregate([
        { "$match": { "username": username, "date": { "$gte": one_week_ago } } },
        { "$group": { "_id": "$username", "total_calories": { "$sum": "$calories_burned" } } }
    ])

    for result in weekly_calories:
        total_calories_burned = result["total_calories"]
        logger.info(total_calories_burned)
        if total_calories_burned >= 3000:
            challenge_history_collection.update_one(
                { "username": username, "challengeTitle": "3000 Calorie Fry" },
                { "$set": { "status": "Completed", "completionDate": datetime.now() } },
                upsert=True
            )
        elif total_calories_burned <3000 and total_calories_burned >=2000:
            challenge_history_collection.update_one(
                { "username": username, "challengeTitle": "2000 Calorie Roast" },
                { "$set": { "status": "Completed", "completionDate": datetime.now() } },
                upsert=True
            )
        elif total_calories_burned <2000 and total_calories_burned >=1500:
            challenge_history_collection.update_one(
                { "username": username, "challengeTitle": "1500 Calorie Sizzle" },
                { "$set": { "status": "Completed", "completionDate": datetime.now() } },
                upsert=True
            )
    
    # Check for active month challenge
    start_of_month = str(datetime(datetime.now().year, datetime.now().month, 1))
    end_of_month = str(datetime(datetime.now().year, datetime.now().month + 1, 1) - timedelta(days=1))

    monthly_calories = workout_collection.aggregate([
        { "$match": { "username": username, "date": { "$gte": start_of_month, "$lte":end_of_month } } },
        { "$group": { "_id": "$username", "total_calories": { "$sum": "$calories_burned" } } }
    ])
    for result in monthly_calories:
    
        total_month_calories = result["total_calories"]
        logger.info(total_month_calories)   
        if total_month_calories >= 10000:        
            challenge_history_collection.update_one(
                { "username": username, "challengeTitle": "10000 Calorie Blaze" },
                { "$set": { "status": "Completed", "completionDate": datetime.now() } },
                upsert=True
            )
        
    monthly_workouts = workout_collection.count_documents({
            "username": username,
            "date": { "$gte": start_of_month, "$lte": end_of_month }
        })

    if monthly_workouts >= 20:
        challenge_history_collection.update_one(
            { "username": username, "challengeTitle": "Track 20 days of workouts" },
            { "$set": { "status": "Completed", "completionDate": datetime.now() } },
            upsert=True
        )

# Function to add a workout
def add_workout(username, workout):
    user = fetch_user(username)
    if not user:
        raise ValueError("User not found")
    logger.info(username)
    workout_collection.insert_one(workout.dict())
    check_challenges(username)

# Function to add weight entry   
def user_history(username, uh_payload):
    user = fetch_user(username)
    if not user:
        raise ValueError("User not found")
    uh_payload_dict = uh_payload.dict(by_alias=True)
    uh_payload_dict["start_weight"] = user["user"]["weight"]

    logger.info(uh_payload_dict)

    user_history_collection.find_one_and_update(
        {"username":username},
        {"$set":uh_payload_dict},
        return_document=True,
        upsert=True
    )
    
# Function to get user
def fetch_user(username) -> Optional[User]:
    user_details = users_collection.find_one({"username": username})
    if user_details:
        user_details["_id"] = str(user_details["_id"])
        return {"status": "user fetched", "user": user_details}
    else:
        None

# Function to generate recommendations for a user
def generate_recommendation(username: str) -> str:
    user = fetch_user(username)
    if not user:
        raise ValueError("User not found")
    
    user_workouts = list(workout_collection.find({"username":username}))
    workout_descriptions = ", ".join([f"{w['muscle']} on {w['date']}" for w in user_workouts])
    phrase = f'Create a personalized workout plan for {user["user"]["username"]} who has done workouts: {workout_descriptions},  age is {user["user"]["age"]} and weight is {user["user"]["weight"]}.'
    MESSAGES =  [
    {"role": "system", "content": "You are a helpful gym trainer, who can recommend based on age, weight and past workouts."},
    {"role": "system", "content": "You should always give the workout plan by mentioning Day 1 instead of weekday in your response."},
    {"role": "user", "content": phrase},
    ]
    deployment_name = "gpt-4"

    completion = openai_client.chat.completions.create(
    model=deployment_name,
    messages=MESSAGES,
    )
    response = json.loads(completion.model_dump_json(indent=2))
    return response["choices"][0]["message"]["content"]

def format_docs(docs:List[Document]) -> str:
        """
        Prepares the users list for the system prompt.
        """
        str_docs = []
        for doc in docs:
                # Build the product document without the contentVector
                doc_dict = {"_id": doc.page_content}
                doc_dict.update(doc.metadata)
                if "contentVector" in doc_dict:  
                        del doc_dict["contentVector"]
                str_docs.append(json.dumps(doc_dict, default=str))                  
        # Return a single string containing each product JSON representation
        # separated by two newlines
        return "\n\n".join(str_docs)

# Get similar users by weight group within 5 pound variance
def get_users_by_weight(weight: int) -> str:
    """
    Retrieves users by weight
    """
    tolerance = 5
    query = {
         "weight":{
              "$gte": weight-tolerance,
              "$lte" : weight+tolerance
         }
    }
    
    doc = list(users_collection.find(query))
    for user_doc in doc:
        if "contentVector" in doc:
            del user_doc["contentVector"]
    doc_dict = {str(user['_id']): user for user in doc}
    return json.dumps(doc_dict, default = str)

# Fetches the user's weight loss after entering this site. 
def users_weight_loss(username: str) -> str:
    """
    Fetches the username and weight loss.  
    """
    user_details = fetch_user(username)
    if not user_details:
        raise ValueError("User not found")
    start_weight = user_details["user"]["weight"]

    user_history_details = list(user_history_collection.find({"username":username}))
    if not user_history_details:
        return json.dumps({"message": f"{username} did not enter any recent weight entries."}, indent=2)
    logger.info(user_history_details)
    current_weight = user_history_details[0]["current_weight"]

    weight_difference = current_weight - start_weight
    if weight_difference >= 0:
        result = {
            "username":username, 
            "weight_loss": weight_difference,
            "text": "Weight lost"
        }
    else:
        result = {
            "username":username, 
            "weight_loss": weight_difference*-1,
            "text" : "Weight Gained"
        }
    return json.dumps(result, default = str, indent =2)

# List all the challenges that are in this db
def list_challenges() -> str:
    """
    Fetches the list of challenges
    """
    doc = list(challenges_collection.find())
    for challenge_doc in doc:
        if "contentVector" in doc:
            del challenge_doc["contentVector"]
    challenges_json = json.dumps(doc, default=str, indent =2)
    return challenges_json

# List challenges completed by a user
def challenges_completed_by_user(username: str) -> str:
    """
    Fetches the challenges that are completed by a user
    """

    doc = list(challenge_history_collection.find({"username":username}))
    for user_challenge_doc in doc:
        if "contentVector" in doc:
            del user_challenge_doc["contentVector"]
    
    user_challenge_dict = {str(ch_user["username"]): ch_user for ch_user in doc}
    return json.dumps(user_challenge_dict, default=str)

# Returns the user who lost most meight
def most_weight_lost()-> str:
    """
    fetches the user who lost most weight.
    """
    users_history = list(user_history_collection.find())
    if not user_history:
        return json.dumps({"message": "No users found."}, indent=2)

    weight_loss_data = []

    for user in users_history:
        logger.info(user)
        username = user["username"]
        user_details = fetch_user(username)
        if not user_details:
            return json.dumps({"message": "No users found."}, indent=2)
        
        username = user['username']
        start_weight = user_details["user"]["weight"]
        
        # Fetch the latest weight from the user_history collection
        latest_weight_entry = list(user_history_collection.find({"username": username}))
        current_weight = latest_weight_entry[0]['current_weight']
        
        # Calculate weight loss
        weight_loss = start_weight - current_weight
        
        weight_loss_data.append({
            "username": username,
            "start_weight": start_weight,
            "current_weight": current_weight,
            "weight_loss": weight_loss
        })
    
    if not weight_loss_data:
        return json.dumps({"message": "No weight loss data found."}, indent=2)

    # Find the user with the most weight loss
    most_weight_lost_user = max(weight_loss_data, key=lambda x: x["weight_loss"])
    
    return json.dumps(most_weight_lost_user, default=str, indent=2)

# Gets the users who has done a particular workout
def get_users_by_workouts(workout: str) -> str:
    """
    Retrieves users by workouts
    """
    doc = list(workout_collection.find({"exercises":workout}))
    for workout_doc in doc:
        if "contentVector" in doc:
            del workout_doc["contentVector"]
    doc_dict = {str(user['_id']): user for user in doc}        
    return json.dumps(doc_dict, default=str)

#
def get_workouts_by_user(username: str) -> str:
    """
    Retrieves workouts done by username
    """
    doc = list(workout_collection.find({"username":username}))
    for workout_doc in doc:
        if "contentVector" in doc:
            del workout_doc["contentVector"]
    doc_dict = {str(user['_id']): user for user in doc}        
    return json.dumps(doc_dict, default=str)

# count all the workouts tracked
def count_workouts(username: Optional[str] = None) -> str:
    """
    Retrieves total number of workouts tracked
    """
    if username:
        count = workout_collection.count_documents({"username":username})    
    else:
        count = workout_collection.count_documents({})
    return json.dumps({"count":count})

# Count all the users in the database
def count_users() -> str:
    """
    Retrieves user count
    """
    count = users_collection.count_documents({})
    return json.dumps({"count":count})

# Total calories burned by a user or total calories burned by all users in the database
def total_calories_burned(username: Optional[str] = None) -> str:
    """
    Retrieves calories burned by user
    """
    match_stage = {}
    if username:
        match_stage["username"]=username
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": None,
                "total_calories_burned": {"$sum": "$calories_burned"}
            }
        }
    ]

    total_calories_burned = workout_collection.aggregate(pipeline)
    result = list(total_calories_burned)
    logger.info(result)
    if result:
        return json.dumps({"total_calories_burned": result[0]["total_calories_burned"]})
    else:
        return json.dumps({"total_calories_burned": 0})

# Total duration of workouts by a user or total duration of workouts by all users in the database
def total_duration(username: Optional[str] = None) -> str:
    """
    Retrieves calories burned by user
    """
    match_stage = {}
    if username:
        match_stage["username"]=username
    pipeline = [
        {"$match": match_stage} if match_stage else {"$match": {}},
        {
            "$group": {
                "_id": None,
                "total_duration": {"$sum": "$duration"}
            }
        }
    ]

    total_duration = workout_collection.aggregate(pipeline)
    result = list(total_duration)
    if result:
        return json.dumps({"total_duration": result[0]["total_duration"]})
    else:
        return json.dumps({"total_duration": 0})

# Average workout duration by user
def average_duration_by_user() -> str:
    """
    Reterives the average duration that a user workedout
    """
    pipeline = [
        {"$group": {"_id": "$username", "averageDuration": {"$avg": "$duration"}}}
    ]
    result = list(workout_collection.aggregate(pipeline))
    return json.dumps(result, default=str)

# Returns the similar users by weight
def similar_users_weight(username: str) -> List[str]:
    """
    Returns similar users by weight using agent_executor
    """
    username_dict = fetch_user(username)
    if not username_dict:
        raise ValueError("User not found")
    weight = str(username_dict["user"]["weight"])

    user_retriever = create_vector_store_retriever("users")
    user_retriever_chain = user_retriever | format_docs
    
    tools = [
        Tool(
            name = "vector_search_users", 
            func = user_retriever_chain.invoke,
            description = "Searches smart fitness database for similar users based on the weight group. Returns the username in JSON format."
        )
    ]

    tools.extend([
         StructuredTool.from_function(get_users_by_weight)
    ])

    system_message = SystemMessage(
         content = """
            You are a helpful, fun and friendly gym trainer for Smart fitness. 
            Your name is BuffBot.
            You are designed to answer questions about the similar users by weight, so that they can work together.
            If you don't know the answer to a question, respond with "I don't know". 
            Do not include the current username in your output.
            Only answer questions related to Smart fitness.
         """
    )
    agent_executor = create_conversational_retrieval_agent(llm, tools, system_message = system_message, verbose=True)
    input_str = f"Find users who are within the five pound range of {weight}."
    result = agent_executor({"input": input_str})
   
    result = result.get("output")
    return result

# Returns the similar users by workouts done. 
def similar_users_workouts(username: str, workouts: str) ->str:
    user = fetch_user(username)
    if not user:
        raise ValueError("User not found")

    if workouts is not None:
        workouts_retriver = create_vector_store_retriever("workouts")
        workouts_retriver_chain = workouts_retriver | format_docs
         
    tools = [
        Tool(
            name = "vector_search_workouts", 
            func = workouts_retriver_chain.invoke,
            description = "Searches smart fitness database and retrieves users who completed the similar workouts. Returns username and workout information in JSON format."
        )
    ]

    tools.extend([
         StructuredTool.from_function(get_users_by_workouts)
    ])

    system_message = SystemMessage(
         content = """
            You are a helpful, fun and friendly gym trainer for Smart fitness. 
            Your name is BuffBot.
            You are designed to answer questions about the similar users by workout, so that they can work together.
            If you don't know the answer to a question, respond with "I don't know". 
            Only answer questions related to Smart fitness.
         """
    )
    agent_executor = create_conversational_retrieval_agent(llm, tools, system_message = system_message, verbose=True)
    result = agent_executor({"input": f"Find users similar to who has completed the workout {workouts}"})
    result = result.get("output")
    return result

# General Chat
def chat(question: str) -> str:
    
    phrase = str(question)
    logger.info("PHRASE")
    MESSAGES =  [
    {"role": "system", "content": "You are a helpful gym trainer, who can recommend based on age, weight and past workouts."},
    {"role": "system", "content": "You should always answer questions related to fitness or workouts or diet. You should not answer any other questions. If user asks other questions simply say sorry, please ask questions about fitness"},
    {"role": "user", "content": phrase},
    ]
    deployment_name = "gpt-4"

    completion = openai_client.chat.completions.create(
    model=deployment_name,
    messages=MESSAGES,
    )
    response = json.loads(completion.model_dump_json(indent=2))
    logger.info(type(response))
    answer = response["choices"][0]["message"]["content"]
    logger.info(f"Answer is {answer}")
    return answer

# Chat with the database
def chat_db(question: str) -> str:

    user_retriever = create_vector_store_retriever("users")
    user_retriever_chain = user_retriever | format_docs

    workouts_retriver = create_vector_store_retriever("workouts")
    workouts_retriver_chain = workouts_retriver | format_docs

    user_history_retriever = create_vector_store_retriever("user_history")
    user_history_retriever_chain = user_history_retriever | format_docs

    challenge_history_retriever = create_vector_store_retriever("user_history")
    challenge_history_retriever_chain = challenge_history_retriever | format_docs

    challenge_retriever = create_vector_store_retriever("user_history")
    challenge_retriever_chain = challenge_retriever | format_docs

    tools = [
        Tool(
            name = "vector_search_users", 
            func = user_retriever_chain.invoke,
            description = "Searches smart fitness database for users. Returns the username in JSON format."
        ),
        Tool(
            name = "vector_search_workouts", 
            func = workouts_retriver_chain.invoke,
            description = "Searches smart fitness database for workouts. Returns information in JSON format."
        ),
        Tool(
            name = "vector_search_workouts", 
            func = user_history_retriever_chain.invoke,
            description = "Searches smart fitness database for userhistory. Returns results in JSON format."
        ),
        Tool(
            name = "vector_search_workouts", 
            func = challenge_history_retriever_chain.invoke,
            description = "Searches smart fitness database challenge history. Returns results in JSON format."
        ),
        Tool(
            name = "vector_search_workouts", 
            func = challenge_retriever_chain.invoke,
            description = "Searches smart fitness database challenges. Returns results in JSON format."
        )
    ]

    tools.extend([
         StructuredTool.from_function(get_users_by_weight),
         StructuredTool.from_function(count_users),
         StructuredTool.from_function(get_users_by_workouts),
         StructuredTool.from_function(total_calories_burned),
         StructuredTool.from_function(count_workouts),
         StructuredTool.from_function(total_duration),
         StructuredTool.from_function(count_users),
         StructuredTool.from_function(average_duration_by_user),
         StructuredTool.from_function(list_challenges),
         StructuredTool.from_function(users_weight_loss),
         StructuredTool.from_function(most_weight_lost),
         StructuredTool.from_function(challenges_completed_by_user),
         StructuredTool.from_function(get_workouts_by_user)
    ])

    system_message = SystemMessage(
         content = """
            You are a helpful, fun and friendly gym trainer for Smart fitness. 
            Your name is BuffBot.
            You are designed to answer questions about the similar users by workout, so that they can work together.
            If you don't know the answer to a question, respond politely with "I don't know".
            Only answer questions related to Smart fitness.
         """
    )
    agent_executor = create_conversational_retrieval_agent(llm, tools, system_message = system_message, verbose=True)
    result = agent_executor({"input": str(question)})
    result = result.get("output")
    return result