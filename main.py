import pandas as pd
from typing import TypedDict, List, Dict, Any, Union
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI # For Gemini
import google.generativeai as genai

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
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
    Extracts the customer's profile and purchase history from the database.
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

    # Extract unique customer profile details (assuming they are consistent across rows for a customer)
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

    # Get full purchase history for the customer (relevant columns only)
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
    by similar industry peers but missing for the current customer.
    """
    print("--- Purchase Pattern Analysis Agent ---")
    if state.get("error"):
        return state

    customer_id = state['customer_id']
    customer_purchase_history = state['customer_purchase_history']
    customer_profile = state['customer_profile']

    # 1. Identify frequent products for this customer
    purchased_products = [p['Product'] for p in customer_purchase_history]
    frequent_products = list(set(purchased_products)) # Unique products purchased

    # 2. Identify missing opportunities from industry peers
    target_industry = customer_profile['industry']
    
    try:
        # Fetch all products from customers in the same industry (excluding current customer)
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

def product_affinity_agent(state: AgentState) -> AgentState:
    """
    Suggests related products based on co-occurrence patterns across all customer purchases in the database.
    """
    print("--- Product Affinity Agent ---")
    if state.get("error"):
        return state

    customer_purchased_products = set(state['frequent_products'])

    try:
        # Fetch all purchase data to build co-occurrence
        all_purchases_df = db_manager.fetch_data_as_df('SELECT "Customer ID", "Product" FROM customer_purchases')
    except Exception as e:
        return {**state, "error": f"Database error fetching all purchases for affinity: {e}"}

    product_co_occurrences: Dict[str, Dict[str, int]] = {}
    
    for _, group in all_purchases_df.groupby('Customer ID'):
        products_in_group = list(group['Product'].unique())
        for i, p1 in enumerate(products_in_group):
            if p1 not in product_co_occurrences:
                product_co_occurrences[p1] = {}
            for j, p2 in enumerate(products_in_group):
                if i != j:
                    product_co_occurrences[p1][p2] = product_co_occurrences[p1].get(p2, 0) + 1

    related_product_suggestions = []
    for purchased_product in customer_purchased_products:
        if purchased_product in product_co_occurrences:
            sorted_co_occurrences = sorted(
                product_co_occurrences[purchased_product].items(),
                key=lambda item: item[1],
                reverse=True
            )
            for related_product, count in sorted_co_occurrences:
                if related_product not in customer_purchased_products:
                    related_product_suggestions.append({
                        "product": related_product,
                        "suggested_for": purchased_product,
                        "rationale": f"Frequently co-purchased with '{purchased_product}' ({count} times by other customers).",
                        "co_occurrence_count": count
                    })
    
    unique_suggestions = {}
    for suggestion in related_product_suggestions:
        prod_name = suggestion['product']
        if prod_name not in unique_suggestions or suggestion['co_occurrence_count'] > unique_suggestions[prod_name]['co_occurrence_count']:
            unique_suggestions[prod_name] = suggestion
    
    related_product_suggestions = list(unique_suggestions.values())

    print(f"Related product suggestions: {related_product_suggestions}")

    return {
        **state,
        "related_product_suggestions": related_product_suggestions
    }

def opportunity_scoring_agent(state: AgentState) -> AgentState:
    """
    Scores potential cross-sell and upsell opportunities by combining insights
    from missing products (peers buy) and product affinity analysis.
    """
    print("--- Opportunity Scoring Agent ---")
    if state.get("error"):
        return state

    customer_profile = state['customer_profile']
    frequent_products = state['frequent_products']
    missing_opportunities_products = state['missing_opportunities_products']
    related_product_suggestions = state['related_product_suggestions']

    customer_purchased_categories = {get_product_category(p) for p in frequent_products}

    potential_products = {} # Product name -> {score, rationale, type}

    # 1. Opportunities from missing products (peers buy, customer doesn't)
    for product in missing_opportunities_products:
        current_score_data = potential_products.get(product, {"score": 0, "rationale": ""})
        current_score = current_score_data["score"]
        current_rationale_parts = [r for r in current_score_data["rationale"].split(". ") if r]

        score = 0.7 # Baseline for being a missing product
        product_category = get_product_category(product)
        
        if product_category in customer_purchased_categories:
            op_type = "Upsell"
            score += 0.1 # Slight boost for direct category relevance
            current_rationale_parts.append(f"Customer already purchases items in the '{product_category}' category, suggesting an upsell.")
        else:
            op_type = "Cross-Sell"
            current_rationale_parts.append(f"Product is in a new category ('{product_category}'), indicating a cross-sell opportunity.")
            
        current_rationale_parts.append(f"Many peers in '{customer_profile['industry']}' industry purchase '{product}'.")

        for aff_sugg in related_product_suggestions:
            if aff_sugg['product'] == product:
                score += 0.2 # Significant boost if it's both missing and related
                current_rationale_parts.append(aff_sugg['rationale'])
                break

        if product not in potential_products or score > current_score:
            potential_products[product] = {
                "product": product,
                "type": op_type,
                "score": score,
                "rationale": ". ".join(filter(None, current_rationale_parts)).strip()
            }
        
    # 2. Opportunities purely from product affinity
    for suggestion in related_product_suggestions:
        product = suggestion['product']
        if product not in frequent_products:
            current_score_data = potential_products.get(product, {"score": 0, "rationale": ""})
            current_score = current_score_data["score"]
            current_rationale_parts = [r for r in current_score_data["rationale"].split(". ") if r]

            score = 0.6 # Baseline for affinity
            product_category = get_product_category(product)

            if product_category in customer_purchased_categories:
                op_type = "Upsell"
                current_rationale_parts.append(f"Customer already purchases items in the '{product_category}' category, suggesting an upsell.")
            else:
                op_type = "Cross-Sell"
                current_rationale_parts.append(f"Product is in a new category ('{product_category}'), indicating a cross-sell opportunity.")


            current_rationale_parts.append(suggestion['rationale'])
            score += min(suggestion['co_occurrence_count'] * 0.005, 0.2) # Boost based on co-occurrence, capped.

            if product not in potential_products or score > current_score:
                 potential_products[product] = {
                    "product": product,
                    "type": op_type,
                    "score": score,
                    "rationale": ". ".join(filter(None, current_rationale_parts)).strip()
                }

    scored_opportunities = sorted(potential_products.values(), key=lambda x: x['score'], reverse=True)

    print(f"Scored opportunities: {scored_opportunities}")

    return {
        **state,
        "scored_opportunities": scored_opportunities
    }

def recommendation_report_agent(state: AgentState) -> AgentState:
    """
    Generates a natural-language research report and structured recommendations
    based on all gathered insights using the LLM.
    """
    print("--- Recommendation Report Agent ---")
    if state.get("error"):
        return state

    customer_profile = state['customer_profile']
    frequent_products = state['frequent_products']
    missing_opportunities_products = state['missing_opportunities_products']
    related_product_suggestions = state['related_product_suggestions']
    scored_opportunities = state['scored_opportunities']

    top_recommendations_structured = []
    unique_rec_products = set()
    for opp in scored_opportunities:
        if opp['product'] not in unique_rec_products:
            top_recommendations_structured.append({
                "product": opp['product'],
                "type": opp['type'],
                "reason": opp['rationale']
            })
            unique_rec_products.add(opp['product'])
        if len(top_recommendations_structured) >= 5:
            break

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
            affinity_summaries.append(f"{s['product']} (often co-purchased with {s['suggested_for']})")
        data_analysis_str += f"- Product affinity analysis suggests complementary items: {'; '.join(affinity_summaries)}.\n"
    else:
        data_analysis_str += "- No specific product affinities identified across the customer base.\n"

    if scored_opportunities:
        data_analysis_str += "\nDetailed insights from scored opportunities:\n"
        for i, opp in enumerate(scored_opportunities[:5]): # Show top 5 for detailed analysis section
            data_analysis_str += f"  - {opp['product']} ({opp['type']}) - Score: {opp['score']:.2f}. Rationale: {opp['rationale']}\n"
    else:
        data_analysis_str += "\n  No specific cross-sell/upsell opportunities identified based on current data."

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
                "research report and actionable recommendations based on provided customer data. "
                "The report must be professional, insightful, and strictly follow the specified structure. "
                "Focus on identifying clear cross-sell (selling new products/services to existing customers) "
                "and upsell (encouraging customers to buy more expensive, premium, or additional features of products they already own) opportunities.\n"
                "Ensure the 'Data Analysis' section clearly articulates findings from purchase patterns, "
                "peer benchmarking, and product affinity analysis.\n"
                "The 'Recommendations' section should be a concise, numbered list of actionable suggestions, "
                "directly referencing the type (Cross-Sell or Upsell) and a brief reason.\n"
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
        # DEBUG PRINTS to confirm content before returning
        print(f"DEBUG: Report content length before return: {len(full_report)}")
        print(f"DEBUG: Recommendations count before return: {len(top_recommendations_structured)}")
    except Exception as e:
        full_report = f"Error generating report with LLM: {e}"
        print(full_report)
        return {**state, "error": full_report}

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
        
        # --- CRITICAL CHANGE HERE: Use invoke instead of astream ---
        final_state_value = app_workflow.invoke(inputs)
        # -----------------------------------------------------------
        
        # The 'invoke' method returns the final state directly, so no need for collected_states or END extraction
        # We don't need `if END in final_state_value: final_state_value = final_state_value[END]` anymore
        
        # DEBUG: Print the final state captured by FastAPI
        print(f"DEBUG: Final state received by FastAPI: {final_state_value}")

        if final_state_value.get("error"):
            if "not found" in final_state_value["error"]:
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
