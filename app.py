import streamlit as st
import openai
import uuid

# Set your OpenAI API key
openai.api_key = st.secrets["openai_api_key"]

# Initialize session state
if "clarifications" not in st.session_state:
    st.session_state.clarifications = []
if "clarified_inputs" not in st.session_state:
    st.session_state.clarified_inputs = {}
if "posts" not in st.session_state:
    st.session_state.posts = {}
if "awaiting_clarification" not in st.session_state:
    st.session_state.awaiting_clarification = False
if "clarification_index" not in st.session_state:
    st.session_state.clarification_index = 0

st.title("🎯 Social Media Post Generator")

# Step 1: Get user input
with st.form("input_form"):
    event = st.text_area("Describe the event:")
    audience = st.text_input("Who is the audience for this post?")
    tone = st.text_input("What tone do you want? (e.g., inspiring, playful, professional)", placeholder="You can enter multiple comma-separated tones")
    submitted = st.form_submit_button("Next")

# Helper: Ask AI for clarifying questions
def get_clarifying_questions(event, audience, tone):
    prompt = f"""
You are a social media content expert. The user wants to create posts for LinkedIn, Instagram, and WhatsApp about this event:

Event: {event}
Audience: {audience}
Tone: {tone}

Ask 2–3 short clarifying questions, one at a time, to better understand the event and write the most effective posts. Keep it crisp and relevant.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return [q.strip("- ").strip() for q in response.choices[0].message.content.split("\n") if q.strip()]

# Step 2: Ask clarifying questions
if submitted and event and audience and tone:
    st.session_state.clarifications = get_clarifying_questions(event, audience, tone)
    st.session_state.clarified_inputs = {"event": event, "audience": audience, "tone": tone}
    st.session_state.awaiting_clarification = True
    st.experimental_rerun()

# Step 3: Answer clarifying questions
if st.session_state.awaiting_clarification and st.session_state.clarification_index < len(st.session_state.clarifications):
    question = st.session_state.clarifications[st.session_state.clarification_index]
    st.subheader(f"Clarifying Question {st.session_state.clarification_index + 1}")
    st.write(question)
    answer = st.text_input("Your answer:")
    if st.button("Submit Answer"):
        st.session_state.clarified_inputs[f"clarification_{st.session_state.clarification_index + 1}"] = answer
        st.session_state.clarification_index += 1
        st.experimental_rerun()
elif st.session_state.awaiting_clarification:
    # All clarifications answered
    st.session_state.awaiting_clarification = False

    # Call AI to generate posts
    def generate_posts(inputs):
        prompt = f"""
You are a social media content expert. Based on the inputs below, generate:

1. A professional, slightly inspiring LinkedIn post.
2. An Instagram caption with emojis, tags, and light hashtags.
3. A WhatsApp message for a group.

Inputs:
{inputs}

Make sure the tone matches: {inputs.get("tone")}
Avoid too many emojis. Keep each post platform-appropriate and engaging.
"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    generated = generate_posts(st.session_state.clarified_inputs)

    # Save results
    st.session_state.posts = {
        "LinkedIn": generated.split("2.")[0].strip(),
        "Instagram": "2." + generated.split("2.")[1].split("3.")[0].strip(),
        "WhatsApp": "3." + generated.split("3.")[1].strip(),
    }
    st.experimental_rerun()

# Step 4: Display results
if st.session_state.posts:
    st.success("✅ Posts generated!")
    for platform, text in st.session_state.posts.items():
        st.subheader(f"{platform} Post")
        st.code(text)

        # Download button
        post_id = str(uuid.uuid4())
        st.download_button(
            label=f"📥 Download {platform} Post",
            data=text,
            file_name=f"{platform}_post_{post_id[:8]}.txt",
            mime="text/plain"
        )

