
from composio_langchain import Action, App, ComposioToolSet
from composio.local_tools import sqltool,filetool
import sqlite3
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import dotenv
dotenv.load_dotenv()

os.environ["COMPOSIO_API_KEY"] = os.getenv("COMPOSIO_API_KEY")

toolset = ComposioToolSet()
tools = toolset.get_tools(apps = [App.SQLTOOL])
file_tool = toolset.get_tools(apps=[App.FILETOOL])
file_tools = toolset.get_actions(actions=[Action.FILE_WRITEFILE])
llm=ChatGoogleGenerativeAI(
        model="gemini-pro", verbose=True, temperature=0.1, google_api_key=os.environ["GOOGLE_API_KEY"]
)
query_writer_agent = Agent(
    role='Query Writer Agent',
    goal="""Form a SQL query based on user input and based on the information about the database.
    After execution of a query evaluate whether the goal given by the user input is achieved. If yes, stop execution""",
    verbose=True,
    memory=True,
    backstory=(
        "You are an expert in understanding user requirements and forming accurate SQL queries."
    ),
    llm=llm,
    allow_delegation=True,
    tools=[],
)

query_executor_agent = Agent(
    role='Query Executor Agent',
    goal="""Execute the SQL query and return the results.
    After execution of a query evaluate whether the goal given by the user input is achieved. If yes, stop execution
    """,
    verbose=True,
    memory=True,
    backstory=(
        "You are an expert in SQL and database management, "
        "skilled at executing SQL queries and providing results efficiently."
    ),
    llm=llm,
    allow_delegation=False,
    tools=tools
)

file_writer_agent = Agent(
    role="File Writer Agent",
    goal = """Document every SQL query executed by the Query Executor Agent in a 'log.txt' file.
    Perform a write operation in the format '<executed_query>\n'
    The log should have the record of every sql query executed """,
    verbose = True,
    memory= True,
    backstory=(
        "You are an expert in logging and documenting changes to SQL databases."
    ),
    llm=llm,
    allow_delegation=False,
    tools = file_tool,
)

user_description = "The database name is company.db"
user_input = "add the entries 1,Book,20 in the products table in database = company.db"  # Example user input

form_query_task = Task(
    description=(
        "This is information about the database: " + user_description +
        ". Form a SQL query based on user input. The input is: " + user_input
    ),
    expected_output='SQL query string is returned. stop once the goal is achieved.',
    agent=query_writer_agent
)


execute_query_task = Task(
    description=(
        "This is the database description="+user_description+"form a sql query based on this input="+user_input+
        "Execute the SQL query formed by the Query Writer Agent, "
        "and return the results. Pass the query and connection string parameter."
        "The connection string parameter should just be of the format <database_name_given>.db"
    ),
    expected_output='Results of the SQL query were returned. Stop once the goal is achieved',
    tools=tools, 
    agent=query_executor_agent,
)

file_write_task = Task(
    description=(
        "the executed query has to be written in a log.txt file to record history"
    ),
    expected_output = 'Executed query was written in the log.txt file',
    tools = file_tool,
    agent = file_writer_agent,
    allow_delegation=False,
)

crew = Crew(
    agents=[query_writer_agent,file_writer_agent],
    tasks=[execute_query_task,file_write_task],
    process=Process.sequential
)

result = crew.kickoff()
print(result)