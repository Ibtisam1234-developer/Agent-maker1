import streamlit as st
import asyncio
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel

# Setup Gemini API
gemini_api = "AIzaSyBWOH8VTt5dgEs6WD124soShBAnRQh9vkk"
provider = AsyncOpenAI(
    api_key=gemini_api,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=provider)

st.set_page_config(page_title="AI Agent Maker", layout="centered")
st.title("🤖 AI Agent Maker")

# === (1) Optional: AI Instruction Generator ===
st.subheader("✨ Need help writing agent instructions?")

with st.expander("Let Gemini generate your agent's instructions"):
    user_description = st.text_input("Describe your agent (e.g. A friendly Python tutor for kids)")

    if st.button("Generate Instructions with Gemini"):
        with st.spinner("Generating instructions..."):

            system_prompt = """
You are a prompt engineer that helps generate system prompts for AI agents.

Based on the user's description of the agent, generate a clear and detailed instruction that will help the AI agent behave as desired.

Always include tone, subject expertise, and behavior rules if possible.
"""

            user_prompt = f"The user wants this agent: {user_description}"

            temp_agent = Agent(
                name="Prompt Engineer",
                instructions=system_prompt,
                model=model,
            )

            async def generate_prompt(prompt):
                return await Runner.run(temp_agent, prompt)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(generate_prompt(user_prompt))

            # Store in session state
            st.session_state.generated_instructions = result.final_output
            st.success("✅ Instructions generated!")
            st.markdown("**Generated Instructions:**")
            st.markdown(result.final_output)

# === (2) Agent Creation ===
st.subheader("🛠️ Create Your Custom AI Agent")

with st.form("agent_form"):
    agent_name = st.text_input("Agent Name", value="My Custom Agent")
    agent_instructions = st.text_area(
        "Agent Instructions (system prompt)",
        height=200,
        value=st.session_state.get("generated_instructions", """
You are a helpful assistant specialized in programming. Answer questions clearly, and only if they are related to coding.
""")
    )
    submitted = st.form_submit_button("🚀 Create Agent")

if submitted:
    # Save agent + reset chat
    st.session_state.user_agent = Agent(
        name=agent_name,
        instructions=agent_instructions,
        model=model,
    )
    st.session_state.chat_history = []
    st.success(f"✅ {agent_name} is ready to answer your questions!")

# === (3) Chat Interface ===
if "user_agent" in st.session_state:

    st.subheader("💬 Chat with Your Agent")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask something...")

    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):

                async def get_response(prompt):
                    return await Runner.run(st.session_state.user_agent, prompt)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(get_response(prompt))

                st.markdown(response.final_output)

        st.session_state.chat_history.append({"role": "assistant", "content": response.final_output})

else:
    st.info("👆 Please create an agent using the form above to start chatting.")
