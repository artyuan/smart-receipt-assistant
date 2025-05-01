import streamlit as st
from src.postgres_sql import insert_sql_query
from src.invoice_agent import build_graph
from datetime import datetime
from langchain_core.messages import HumanMessage

st.title("🛒 Smart Receipt Assistant")
st.divider()

graph = build_graph()
config = {"configurable": {"thread_id": 42}}

# --- Feature 1: Upload Receipt ---
st.header("📤 Upload Your Receipt")
st.markdown("Upload a supermarket receipt in **PDF** format.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file:
    st.session_state.uploaded_file = uploaded_file
    path = "temp_receipt.pdf"
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Processing your receipt..."):
        result = graph.invoke({"path": path}, config=config)
        st.success("✅ Receipt processed and saved successfully!")

# --- Feature 2: Add Purchase Details Manually ---
st.divider()
st.header("📝 Purchase Details Manually")
st.markdown("Don't have the receipt in PDF? No problem! Enter your shopping data below.")
with st.form("add_purchase_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        invoice_id = st.text_input("Invoice ID")
        description = st.text_input("Description")
        quantity = st.number_input("Quantity", min_value=0.0, format="%.2f")
        unit = st.text_input("Unit (e.g., kg, l, pcs)")

    with col2:
        supermarket_name = st.text_input("Supermarket Name")
        product = st.text_input("Product")
        unitary_value = st.number_input("Unitary Value", min_value=0.0, format="%.2f")
        volume = st.text_input("Volume (optional)")

    with col3:
        date = st.date_input("Date", value=datetime.today())
        category = st.text_input("Category")
        total_value = st.number_input("Total Value", min_value=0.0, format="%.2f")


    query = f"""
    INSERT INTO invoices (invoice_id, supermarket_name, datetime, description, quantity, unit, unitary_value, total_value, product, volume, category) VALUES
    ({invoice_id},'{supermarket_name}', '{date}', '{description}', '{quantity}', '{unit}', {unitary_value}, {total_value}, '{product}', '{volume}', '{category}');
    """

    submitted = st.form_submit_button("Save Purchase")

    if submitted:
        try:
            insert_sql_query(query)
            st.success("✅ Purchase saved successfully!")
        except Exception as e:
            st.error(f"❌ Failed to save purchase: {e}")

# --- Feature 3: Ask About Purchases ---
st.divider()
st.header("❓ Ask About Your Purchases")
st.markdown("Curious about what you bought last week? Or how much you've spent on beverages? Just ask!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What do you want to know about your purchases?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response using the AI agent
    with st.chat_message("assistant"):
        # Display "typing..." indicator
        message_placeholder = st.empty()
        message_placeholder.markdown("Assistant is typing...")

        # Format the conversation into a compatible format for the agent
        context_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]

        # Use the agent to get the response
        try:
            response = graph.invoke({"question": [HumanMessage(content=prompt)]}, config=config)
            sql_query = response['query']
            answer = response['answer']
            message = f"**Response:**\n{answer}"
            # Display the constructed message
            message_placeholder.markdown(message)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            message_placeholder.markdown(error_message)
            response = error_message

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": message})

