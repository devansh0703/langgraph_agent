import pandas as pd
from typing import TypedDict, List, Dict, Any, Union
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI # For Gemini
import google.generativeai as genai
# Changed import from langchain_core.pydantic_v1 to pydantic directly
from pydantic import BaseModel, Field # For structured LLM output parsing

import os
import json # For JSON parsing from LLM
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from db_manager import db_manager # Import the database manager

load_dotenv() # Load environment variables

# --- Configuration ---
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash-latest")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in .env.")

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.0)

# Define product categories for smarter cross-sell/upsell logic
PRODUCT_CATEGORIES = {
    "Drills": "Power Tools & Accessories",
    "Drill Bits": "Power Tools & Accessories",
    "Generators": "Power Tools & Equipment",
    "Backup Batteries": "Power Tools & Equipment",
    "Protective Gloves": "Safety & Apparel",
    "Safety Gear": "Safety & Apparel",
    "Workflow Automation": "Software/Services",
    "Collaboration Suite": "Software/Services",
    "API Integrations": "Software/Services",
    "Advanced Analytics": "Software/Services",
}

def get_product_category(product_name: str) -> str:
    """Returns the category for a given product name, defaulting to 'Other'."""
    return PRODUCT_CATEGORIES.get(product_name, "Other")

# --- LangGraph State Definition ---
class AgentState(TypedDict):
    """
    Represents the state of the LangGraph agent pipeline.
    This dictionary accumulates data as it passes between agents.
    """
    customer_id: str
    customer_profile: Dict[str, Any]
    customer_purchase_history: List[Dict[str, Any]]
    frequent_products: List[str]
    missing_opportunities_products: List[str]
    related_product_suggestions: List[Dict[str, Any]]
    scored_opportunities: List[Dict[str, Any]]
    research_report: str
    recommendations_structured: List[Dict[str, Any]]
    error: Union[str, None] # To handle errors gracefully in the pipeline

# --- Sub-Agents (Nodes in LangGraph) ---

def customer_context_agent(state: AgentState) -> AgentState:
    """
    Extracts the customer's profile and purchase history from the database. (Rule-based)
    """
    print("--- Customer Context Agent ---")
    customer_id = state['customer_id']

    try:
        query = f'SELECT * FROM customer_purchases WHERE "Customer ID" = %s'
        customer_data_df = db_manager.fetch_data_as_df(query, (customer_id,))
    except Exception as e:
        return {**state, "error": f"Database error fetching customer data: {e}"}

    if customer_data_df.empty:
        print(f"Customer ID {customer_id} not found in DB.")
        return {**state, "error": f"Customer ID {customer_id} not found."}

    first_row = customer_data_df.iloc[0]
    customer_profile = {
        "customer_name": first_row['Customer Name'],
        "industry": first_row['Industry'],
        "annual_revenue_usd": float(first_row['Annual Revenue (USD)']),
        "number_of_employees": int(first_row['Number of Employees']),
        "location": first_row['Location'],
        "customer_priority_rating": str(first_row['Customer Priority Rating']),
        "account_type": str(first_row['Account Type'])
    }

    customer_purchase_history = customer_data_df[[
        'Product', 'Quantity', 'Unit Price (USD)', 'Total Price (USD)', 'Purchase Date'
    ]].to_dict(orient='records')

    print(f"Profile for {customer_profile['customer_name']} (ID: {customer_id}) loaded.")
    return {
        **state,
        "customer_profile": customer_profile,
        "customer_purchase_history": customer_purchase_history,
        "error": None
    }

def purchase_pattern_analysis_agent(state: AgentState) -> AgentState:
    """
    Identifies frequent purchases for the customer and products commonly bought
    by similar industry peers but missing for the current customer. (Rule-based, for factual data)
    """
    print("--- Purchase Pattern Analysis Agent ---")
    if state.get("error"):
        return state

    customer_id = state['customer_id']
    customer_purchase_history = state['customer_purchase_history']
    customer_profile = state['customer_profile']

    purchased_products = [p['Product'] for p in customer_purchase_history]
    frequent_products = list(set(purchased_products)) 

    target_industry = customer_profile['industry']
    
    try:
        query = f'SELECT DISTINCT "Product" FROM customer_purchases WHERE "Industry" = %s AND "Customer ID" != %s'
        industry_peer_products_df = db_manager.fetch_data_as_df(query, (target_industry, customer_id))
        all_peer_products = set(industry_peer_products_df['Product'].tolist())
    except Exception as e:
        return {**state, "error": f"Database error fetching industry peer data: {e}"}

    customer_products_set = set(frequent_products)
    missing_opportunities_products = list(all_peer_products - customer_products_set)

    print(f"Frequent products for {customer_id}: {frequent_products}")
    print(f"Missing opportunities (from peers): {missing_opportunities_products}")

    return {
        **state,
        "frequent_products": frequent_products,
        "missing_opportunities_products": missing_opportunities_products
    }

# Pydantic model for LLM Product Affinity output
class ProductSuggestion(BaseModel):
    product: str = Field(description="Name of the suggested product.")
    rationale: str = Field(description="Reason for suggesting this product, explaining its complementary nature.")

class ProductAffinitySuggestions(BaseModel):
    suggestions: List[ProductSuggestion] = Field(description="List of suggested complementary products.")


def product_affinity_agent(state: AgentState) -> AgentState:
    """
    Suggests related products using LLM-based reasoning about complementarity. (LLM-driven)
    """
    print("--- Product Affinity Agent (LLM-Driven) ---")
    if state.get("error"):
        return state

    customer_purchased_products = state['frequent_products']
    customer_industry = state['customer_profile']['industry']

    if not customer_purchased_products:
        print("No frequent products found for customer, skipping LLM affinity suggestions.")
        return {**state, "related_product_suggestions": []}

    # Ensure to pass format_instructions to the prompt template
    parser = JsonOutputParser(pydantic_object=ProductAffinitySuggestions)
    format_instructions = parser.get_format_instructions()

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert product analyst. Given a customer's frequently purchased products and their industry, "
                "suggest 3-5 highly complementary or related products that the customer might benefit from, "
                "even if they haven't been directly co-purchased by others. Focus on logical relationships, common industry needs, "
                "or product ecosystem expansion.\n"
                "Provide a clear rationale for each suggestion.\n"
                "The suggestions must be new products not already purchased by the customer.\n"
                "Output your response in JSON format according to the following schema:\n{format_instructions}"
            ),
            (
                "human",
                "Customer's industry: {customer_industry}\n"
                "Customer's frequently purchased products: {frequent_products}\n"
                "Products already owned by the customer (DO NOT suggest these): {frequent_products}\n\n"
                "Provide product suggestions and their rationales."
            ),
        ]
    )

    # Pass format_instructions to the prompt's .invoke or .format method
    chain = prompt_template.partial(format_instructions=format_instructions) | llm | parser

    try:
        llm_response = chain.invoke({
            "customer_industry": customer_industry,
            "frequent_products": ", ".join(customer_purchased_products)
        })
        related_product_suggestions_raw = llm_response.get('suggestions', [])
        
        # Filter out any suggestions that the customer already owns (LLM might hallucinate)
        existing_products_set = set(customer_purchased_products)
        related_product_suggestions = [
            s for s in related_product_suggestions_raw if s['product'] not in existing_products_set
        ]

        print(f"LLM-generated related product suggestions: {related_product_suggestions}")
    except Exception as e:
        print(f"Error generating product affinity suggestions with LLM: {e}")
        related_product_suggestions = [] # Default to empty list on error

    return {
        **state,
        "related_product_suggestions": related_product_suggestions
    }

# Pydantic model for LLM Opportunity Scoring output
class ScoredOpportunity(BaseModel):
    product: str = Field(description="Name of the recommended product.")
    type: str = Field(description="Type of opportunity (Cross-Sell or Upsell).")
    score: int = Field(description="Score (1-10) indicating the potential impact/relevance, 10 being highest.", ge=1, le=10)
    rationale: str = Field(description="Detailed reason for this recommendation, combining all relevant insights.")

class ScoredOpportunitiesList(BaseModel):
    opportunities: List[ScoredOpportunity] = Field(description="List of scored cross-sell and upsell opportunities.")


def opportunity_scoring_agent(state: AgentState) -> AgentState:
    """
    Scores potential cross-sell and upsell opportunities using LLM-based reasoning and prioritization. (LLM-driven)
    """
    print("--- Opportunity Scoring Agent (LLM-Driven) ---")
    if state.get("error"):
        return state

    customer_profile = state['customer_profile']
    frequent_products = state['frequent_products']
    missing_opportunities_products = state['missing_opportunities_products']
    related_product_suggestions = state['related_product_suggestions']

    # Prepare input for LLM
    customer_info = json.dumps(customer_profile, indent=2)
    current_products_str = ", ".join(frequent_products) if frequent_products else "None"
    missing_from_peers_str = ", ".join(missing_opportunities_products) if missing_opportunities_products else "None"
    affinity_suggestions_str = json.dumps(related_product_suggestions, indent=2) if related_product_suggestions else "None"

    # Ensure to pass format_instructions to the prompt template
    parser = JsonOutputParser(pydantic_object=ScoredOpportunitiesList)
    format_instructions = parser.get_format_instructions()

    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert sales strategist. Analyze the provided customer data and identified opportunities "
                "to pinpoint the top 5 most impactful cross-sell and upsell recommendations. "
                "For each recommendation, clearly state the product, whether it's a 'Cross-Sell' or 'Upsell' opportunity, "
                "assign a 'score' from 1 to 10 (10 being the highest potential/relevance), "
                "and provide a concise yet comprehensive 'rationale' that summarizes ALL relevant insights "
                "(e.g., existing purchases, peer behavior, product affinity, logical fit, etc.).\n"
                "Prioritize recommendations that offer the most value to the customer and significant growth for the business.\n"
                "Exclude any products the customer already frequently purchases.\n"
                "Output your response strictly in JSON format according to the following schema:\n{format_instructions}"
            ),
            (
                "human",
                "Customer Profile:\n{customer_info}\n\n"
                "Customer's Frequently Purchased Products: {current_products_str}\n\n"
                "Products Purchased by Industry Peers (Missing for this customer):\n{missing_from_peers_str}\n\n"
                "AI-Generated Related Product Suggestions:\n{affinity_suggestions_str}\n\n"
                "Generate the top 5 scored cross-sell and upsell opportunities."
            ),
        ]
    )

    # Pass format_instructions to the prompt's .invoke or .format method
    chain = prompt_template.partial(format_instructions=format_instructions) | llm | parser

    try:
        llm_response = chain.invoke({
            "customer_info": customer_info,
            "current_products_str": current_products_str,
            "missing_from_peers_str": missing_from_peers_str,
            "affinity_suggestions_str": affinity_suggestions_str
        })
        scored_opportunities_raw = llm_response.get('opportunities', [])

        # Filter out any recommendations for products the customer already owns (LLM might hallucinate)
        existing_products_set = set(frequent_products)
        scored_opportunities = [
            opp for opp in scored_opportunities_raw if opp['product'] not in existing_products_set
        ]

        # Sort by score (highest first)
        scored_opportunities = sorted(scored_opportunities, key=lambda x: x.get('score', 0), reverse=True)

        print(f"LLM-scored opportunities: {scored_opportunities}")
    except Exception as e:
        print(f"Error generating scored opportunities with LLM: {e}")
        # Capture the LLM error in the state to propagate it
        return {**state, "error": f"Error in Opportunity Scoring Agent: {e}"}

    return {
        **state,
        "scored_opportunities": scored_opportunities
    }

def recommendation_report_agent(state: AgentState) -> AgentState:
    """
    Generates a natural-language research report and structured recommendations
    based on all gathered insights, now including AI-driven affinity and scoring. (LLM-driven)
    """
    print("--- Recommendation Report Agent (LLM-Driven) ---")
    if state.get("error"):
        return state

    customer_profile = state['customer_profile']
    frequent_products = state['frequent_products']
    missing_opportunities_products = state['missing_opportunities_products']
    related_product_suggestions = state['related_product_suggestions'] # Now from LLM
    scored_opportunities = state['scored_opportunities'] # Now from LLM, with scores/rationales

    top_recommendations_structured = []
    # Take top 5 from LLM-scored opportunities (already sorted)
    # Ensure scored_opportunities is not empty before attempting to slice
    if scored_opportunities:
        for opp in scored_opportunities[:5]:
            top_recommendations_structured.append({
                "product": opp['product'],
                "type": opp['type'],
                "reason": opp['rationale'] # Use LLM-generated rationale
            })

    customer_overview_str = (
        f"- Industry: {customer_profile.get('industry', 'N/A')}\n"
        f"- Annual Revenue: ${customer_profile.get('annual_revenue_usd', 0):,.0f}\n"
        f"- Number of Employees: {customer_profile.get('number_of_employees', 'N/A')}\n"
        f"- Location: {customer_profile.get('location', 'N/A')}\n"
        f"- Customer Priority: {customer_profile.get('customer_priority_rating', 'N/A')}\n"
        f"- Account Type: {customer_profile.get('account_type', 'N/A')}\n"
        f"- Recent Purchases: {', '.join(frequent_products) if frequent_products else 'None'}"
    )

    data_analysis_str = (
        "Based on purchasing patterns:\n"
        f"- The customer frequently purchases: {', '.join(frequent_products) if frequent_products else 'No frequent products identified.'}.\n"
    )
    if missing_opportunities_products:
        data_analysis_str += f"- Benchmarking against industry peers in '{customer_profile['industry']}' reveals products like: {', '.join(missing_opportunities_products)} are commonly purchased by similar companies, representing potential missing opportunities for this customer.\n"
    else:
        data_analysis_str += "- No significant missing product opportunities identified from industry peers.\n"
    
    if related_product_suggestions:
        affinity_summaries = []
        for s in related_product_suggestions:
            affinity_summaries.append(f"{s['product']} (AI-suggested as complementary: {s['rationale']})")
        data_analysis_str += f"- AI-driven product affinity analysis suggests complementary items: {'; '.join(affinity_summaries)}.\n"
    else:
        data_analysis_str += "- No specific product affinities identified through AI analysis.\n"

    if scored_opportunities:
        data_analysis_str += "\nDetailed insights from AI-scored opportunities:\n"
        for i, opp in enumerate(scored_opportunities[:5]): # Show top 5 for detailed analysis section
            data_analysis_str += f"  - {opp['product']} (Type: {opp['type']}, Score: {opp['score']}/10). Rationale: {opp['rationale']}\n"
    else:
        data_analysis_str += "\n  No specific cross-sell/upsell opportunities identified based on current AI analysis."

    recommendations_str = ""
    if top_recommendations_structured:
        for i, rec in enumerate(top_recommendations_structured):
            recommendations_str += f"{i+1}. {rec['product']} (Type: {rec['type']}). Rationale: {rec['reason']}\n"
    else:
        recommendations_str = "No specific recommendations could be generated at this time."

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert sales and marketing analyst. Generate a comprehensive "
                "research report and actionable recommendations based on provided customer data and AI analysis. "
                "The report must be professional, insightful, and strictly follow the specified structure. "
                "Focus on identifying clear cross-sell (selling new products/services to existing customers) "
                "and upsell (encouraging customers to buy more expensive, premium, or additional features of products they already own) opportunities.\n"
                "Ensure the 'Data Analysis' section clearly articulates findings from purchase patterns, "
                "peer benchmarking, and the **AI-driven product affinity and opportunity scoring results**.\n"
                "The 'Recommendations' section should be a concise, numbered list of actionable suggestions, "
                "directly referencing the type (Cross-Sell or Upsell) and the **AI-generated rationale**.\n"
                "The 'Conclusion' should summarize the potential impact and be forward-looking.\n\n"
                "Report Structure to follow:\n"
                "Research Report: Cross-Sell and Upsell Opportunities for {customer_name}\n\n"
                "Introduction:\n"
                "This report analyzes recent purchasing behavior of {customer_name} and benchmarks against "
                "industry peers to identify cross-sell and upsell opportunities.\n\n"
                "Customer Overview:\n"
                "{customer_overview_data}\n\n"
                "Data Analysis:\n"
                "{data_analysis_insights}\n\n"
                "Recommendations:\n"
                "{recommendations_list}\n\n"
                "Conclusion:\n"
                "Targeted cross-sell and upsell campaigns focusing on these products can significantly "
                "increase revenue and customer satisfaction. Implementing these recommendations will "
                "strengthen the customer relationship and drive business growth."
            ),
            (
                "human",
                "Generate the full research report string for customer ID {customer_id} using the following data:\n\n"
                "Customer Name: {customer_name}\n"
                "Customer Overview Data:\n{customer_overview_data}\n\n"
                "Data Analysis Insights:\n{data_analysis_insights}\n\n"
                "Recommendations for Report:\n{recommendations_list}\n\n"
            ),
        ]
    ).partial(
        customer_id=state['customer_id'],
        customer_name=customer_profile.get('customer_name', 'Unknown Customer'),
        customer_overview_data=customer_overview_str,
        data_analysis_insights=data_analysis_str,
        recommendations_list=recommendations_str
    )

    try:
        chain = prompt | llm | StrOutputParser()
        full_report = chain.invoke({})
    except Exception as e:
        full_report = f"Error generating report with LLM: {e}"
        print(full_report)
        # Propagate the error for the API to catch
        return {**state, "error": f"Error in Recommendation Report Agent: {e}"}

    print("Report generated successfully.")
    return {
        **state,
        "research_report": full_report,
        "recommendations_structured": top_recommendations_structured
    }

# --- Build the LangGraph Workflow ---
workflow = StateGraph(AgentState)

# Define nodes for each sub-agent
workflow.add_node("customer_context", customer_context_agent)
workflow.add_node("purchase_pattern_analysis", purchase_pattern_analysis_agent)
workflow.add_node("product_affinity_agent", product_affinity_agent)
workflow.add_node("opportunity_scoring_agent", opportunity_scoring_agent)
workflow.add_node("recommendation_report_agent", recommendation_report_agent)

# Set the entry point of the graph
workflow.set_entry_point("customer_context")

# Define conditional edges from customer_context: if error, go to END, else continue
workflow.add_conditional_edges(
    "customer_context",
    lambda state: "end" if state.get("error") else "continue",
    {"continue": "purchase_pattern_analysis", "end": END}
)

# Define regular edges between subsequent agents
workflow.add_edge("purchase_pattern_analysis", "product_affinity_agent")
workflow.add_edge("product_affinity_agent", "opportunity_scoring_agent")
workflow.add_edge("opportunity_scoring_agent", "recommendation_report_agent")
# Add a conditional edge from opportunity_scoring_agent to check for errors
workflow.add_conditional_edges(
    "opportunity_scoring_agent",
    lambda state: "end" if state.get("error") and "Error in Opportunity Scoring Agent" in state.get("error", "") else "continue",
    {"continue": "recommendation_report_agent", "end": END}
)
workflow.add_edge("recommendation_report_agent", END)


# Compile the graph
app_workflow = workflow.compile() # Renamed to avoid conflict with FastAPI 'app'

# --- API with FastAPI ---
api_app = FastAPI(
    title="Cross-Sell/Upsell Recommendation Agent API",
    description="API for generating cross-sell/upsell recommendations and research reports using LangGraph and Gemini.",
    version="1.0.0"
)

# Pydantic model for the API response structure
class RecommendationResponse(BaseModel):
    customer_id: str
    research_report: str
    recommendations: List[Dict[str, Any]]
    error: Union[str, None] = None

@api_app.get("/recommendation/{customer_id}", response_model=RecommendationResponse)
async def get_recommendation(customer_id: str):
    """
    Runs the agent pipeline to generate a research report and cross-sell/upsell
    recommendations for a given customer ID.
    """
    # Ensure DB connection is active before starting the pipeline
    try:
        db_manager._connect_on_demand()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database service unavailable: {e}")

    try:
        inputs = {"customer_id": customer_id}
        
        # Use invoke instead of astream to get the final accumulated state
        final_state_value = app_workflow.invoke(inputs)
        
        if final_state_value.get("error"):
            # Check if the error is from the pipeline
            if "Error in Opportunity Scoring Agent" in final_state_value["error"] or \
               "Error in Recommendation Report Agent" in final_state_value["error"]:
                # If LLM related error, return 500 but include the error message
                return RecommendationResponse(
                    customer_id=customer_id,
                    research_report="Report generation failed due to an internal AI error.",
                    recommendations=[],
                    error=final_state_value["error"]
                )
            elif "not found" in final_state_value["error"]:
                raise HTTPException(status_code=404, detail=final_state_value["error"])
            else:
                raise HTTPException(status_code=500, detail=final_state_value["error"])

        return RecommendationResponse(
            customer_id=customer_id,
            research_report=final_state_value.get("research_report", "Report not generated due to an internal error."),
            recommendations=final_state_value.get("recommendations_structured", []),
            error=final_state_value.get("error")
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"An unexpected error occurred during pipeline execution: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
