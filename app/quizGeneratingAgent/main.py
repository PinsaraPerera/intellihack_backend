from .agents import QuizGeneratingAgent
from .tasks import QuizGeneratingTask
from app.core.openAI_embeddings import download_vector_db
from crewai import Crew
import json

def main(no_of_questions, request, user_email):

    # create vectorstore
    vectorstore = download_vector_db(session_id=request.state.session_id, user_email=user_email)

    agents = QuizGeneratingAgent(request=request, user_email=user_email, vectorstore=vectorstore)
    tasks = QuizGeneratingTask()

    # create agents
    questionGeneratingAgent = agents.questionGeneratingAgent()
    formatValidatorAgent = agents.formatValidatorAgent()

    # create tasks
    generate_quizes = tasks.generate_quizes(number_of_questions=no_of_questions, agent=questionGeneratingAgent)
    format_output = tasks.format_output(agent=formatValidatorAgent)

    format_output.context = [generate_quizes]

    # create crew
    crew = Crew(
        agents=[questionGeneratingAgent, formatValidatorAgent],
        tasks=[generate_quizes, format_output],
        verbose=2,
    )

    # execute crew
    result = crew.kickoff()

    print("####################################")
    result_response = json.dumps(result)
    print(result_response)

    return result

# if __name__ == "__main__":
#     main(no_of_questions=5)