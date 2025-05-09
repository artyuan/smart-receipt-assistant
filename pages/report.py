import streamlit as st
from agents.report_workflow import build_report_graph

st.title("🧾 Supermarket Spending Report")
st.markdown("""
> **Get a comprehensive view of your supermarket spending habits.**  
> This report analyzes your purchase history to provide:
> - 🏬 **Total spending per supermarket**  
> - 🛒 **Breakdown by product category**  
> - 📈 **Monthly spending trends across stores**  
> - 🔍 **Key insights, top spending areas, and unusual patterns**  
>
> Use this tool to better understand your financial behavior and make informed budgeting decisions.
""")

if "full_report" not in st.session_state:
    st.session_state.full_report = None

graph = build_report_graph()
if st.button("Generate Report"):
    with st.spinner("Generating your financial report..."):
        config = {
            "configurable": {"thread_id": 42},
            "recursion_limit": 100
        }
        user_query = (
            "Generate a detailed financial report based on my supermarket purchases. "
            "The report should include: (1) total spending per supermarket, "
            "(2) spending breakdown by product category, "
            "(3) monthly spending trends for each supermarket, and "
            "Highlight key insights, top spending areas, and any anomalies or patterns."
        )
        response = graph.invoke({"user_query": user_query}, config=config)
        full_report = response.get("full_report", "No report found.")
        st.session_state.full_report = response.get("full_report", "No report found.")
        st.subheader("📊 Full Report")
        st.markdown(full_report)


# graph = build_report_graph()
# if st.button("Generate Report"):
#     with st.spinner("Generating your financial report..."):
#         config = {
#             "configurable": {"thread_id": 42},
#             "recursion_limit": 100
#         }
#         user_query = (
#             "Generate a detailed financial report based on my supermarket purchases. "
#             "The report should include: (1) total spending per supermarket, "
#             "(2) spending breakdown by product category, "
#             "(3) monthly spending trends for each supermarket, and "
#             "Highlight key insights, top spending areas, and any anomalies or patterns."
#         )
#
#         try:
#             response = graph.invoke({"user_query": user_query}, config=config)
#             full_report = response.get("full_report", "No report found.")
#             st.subheader("📊 Full Report")
#             st.markdown(full_report)
#         except Exception as e:
#             st.error(f"❌ Failed to generate report: {e}")
# else:
#     st.info("Click the button to generate a detailed financial report.")




# from agents.report_workflow import build_report_graph
#
# graph = build_report_graph()
#
# generate_report = True
# if generate_report:
#     config = {"configurable": {"thread_id": 42}, "recursion_limit": 100}
#     response = graph.invoke({
#         "user_query": (
#             "Generate a detailed financial report based on my supermarket purchases. "
#             "The report should include: (1) total spending per supermarket, "
#             "(2) spending breakdown by product category, "
#             "(3) monthly spending trends for each supermarket, and "
#             "Highlight key insights, top spending areas, and any anomalies or patterns."
#         )
#     }, config=config)
#
#     print(response['full_report'])
# else:
#     print('please make generate report True')