# expense_agent/agent.py - Updated for Latest ADK
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import requests
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from azure.search.documents import SearchClient
from azure.identity import ClientSecretCredential

# Enhanced Azure AI Search Integration with Azure AD Service Principal
def search_expense_policy(query: str, category: Optional[str] = None, tool_context=None) -> dict:
    """
    Search the Azure AI Search knowledge base for expense policy information.
    
    Args:
        query: User's question or expense-related query
        category: Optional expense category filter
        tool_context: ADK tool context (automatically provided)
    
    Returns:
        dict: Search results with relevant policy chunks and sources
    """
    try:
        # Get configuration from environment
        search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        client_id = os.getenv("AZURE_CLIENT_ID") 
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        index_name = os.getenv("AZURE_AI_SEARCH_INDEX", "expense-policy-index")
        
        if not search_endpoint or not client_id or not client_secret or not tenant_id:
            return {
                "status": "error",
                "message": "Azure AI Search not configured. Please set AZURE_AI_SEARCH_ENDPOINT, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID",
                "policy_excerpts": [],
                "sources": []
            }
        
        # Create Azure AD credential using Service Principal
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Use Azure SDK with Azure AD authentication
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )
        
        # Build search parameters
        search_params = {
            "search_text": query,
            "query_type": "semantic",
            "semantic_configuration_name": "default",
            "top": 5,
            "select": ["content", "category", "source_document", "chunk_id"],
            "highlight_fields": ["content"],
            "highlight_pre_tag": "<mark>",
            "highlight_post_tag": "</mark>"
        }
        
        # Add category filter if specified
        if category:
            search_params["filter"] = f"category eq '{category}'"
        
        # Execute search
        results = search_client.search(**search_params)
        
        # Format results for the agent
        formatted_results = {
            "status": "success", 
            "query": query,
            "category_filter": category,
            "total_results": 0,
            "policy_excerpts": [],
            "sources": set()
        }
        
        for result in results:
            formatted_results["total_results"] += 1
            formatted_results["policy_excerpts"].append({
                "content": result.get("content", ""),
                "category": result.get("category", ""),
                "highlights": result.get("@search.highlights", {}).get("content", []),
                "score": result.get("@search.score", 0),
                "chunk_id": result.get("chunk_id", "")
            })
            
            # Track unique sources
            source = result.get("source_document", "")
            if source:
                formatted_results["sources"].add(source)
        
        # Convert set to list for JSON serialization
        formatted_results["sources"] = list(formatted_results["sources"])
        
        # Update session state if tool_context available
        if tool_context and tool_context.state:
            tool_context.state["last_policy_search"] = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results_count": formatted_results["total_results"]
            }
        
        return formatted_results
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching policy database: {str(e)}",
            "policy_excerpts": [],
            "sources": []
        }

def validate_expense_data(expense_data: dict, tool_context=None) -> dict:
    """
    Validate expense data against policy rules with enhanced logic.
    
    Args:
        expense_data: Dictionary containing expense details
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        dict: Validation results with any policy violations
    """
    validation_results = {
        "is_valid": True,
        "violations": [],
        "warnings": [],
        "required_documents": [],
        "policy_references": []
    }
    
    try:
        amount = float(expense_data.get("amount", 0))
        category = expense_data.get("category", "").lower()
        location = expense_data.get("location", "")
        description = expense_data.get("description", "")
        date = expense_data.get("date", "")
        
        # Enhanced validation rules with policy references
        if category == "meals":
            daily_limit = 100
            receipt_threshold = 25
            
            if amount > daily_limit:
                validation_results["violations"].append(
                    f"Meal expense of ${amount} exceeds daily policy limit of ${daily_limit}"
                )
                validation_results["policy_references"].append("Section 3.2 - Meal Allowances")
                validation_results["is_valid"] = False
            
            if amount > receipt_threshold:
                validation_results["required_documents"].append(
                    f"Receipt required for meals over ${receipt_threshold}"
                )
            
            # Business meal validation
            if amount > 50 and "business" not in description.lower():
                validation_results["warnings"].append(
                    "High meal expense should include business justification"
                )
        
        elif category == "lodging":
            nightly_limit = 300
            
            if amount > nightly_limit:
                validation_results["violations"].append(
                    f"Lodging expense of ${amount} exceeds nightly limit of ${nightly_limit}"
                )
                validation_results["policy_references"].append("Section 4.1 - Accommodation Limits")
                validation_results["is_valid"] = False
        
        elif category == "transportation":
            # Ride-share limits
            if any(word in description.lower() for word in ["uber", "lyft", "taxi"]):
                if amount > 75:
                    validation_results["warnings"].append(
                        "Ride-share expenses over $75 may require business justification"
                    )
            
            # Car rental validation
            if "rental" in description.lower() and amount > 500:
                validation_results["required_documents"].append(
                    "Car rental agreement and fuel receipts required"
                )
        
        elif category == "airfare":
            # Business class restrictions
            if amount > 1000:
                validation_results["warnings"].append(
                    "Airfare over $1000 may require manager approval for business class"
                )
                validation_results["required_documents"].append("Flight itinerary and boarding passes")
        
        # Universal receipt requirement
        if amount > 25 and not expense_data.get("has_receipt", False):
            validation_results["required_documents"].append(
                f"Receipt required for all expenses over $25"
            )
            validation_results["policy_references"].append("Section 2.1 - Documentation Requirements")
        
        # Weekend/holiday expense flagging
        try:
            from datetime import datetime
            if date:
                expense_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                if expense_date.weekday() >= 5:  # Saturday or Sunday
                    validation_results["warnings"].append(
                        "Weekend expense flagged for review"
                    )
        except:
            pass  # Date parsing failed, skip weekend check
        
        # Update session state with validation history
        if tool_context and tool_context.state:
            if "validation_history" not in tool_context.state:
                tool_context.state["validation_history"] = []
            
            tool_context.state["validation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "expense": expense_data,
                "is_valid": validation_results["is_valid"],
                "violations_count": len(validation_results["violations"])
            })
        
        return validation_results
        
    except Exception as e:
        return {
            "is_valid": False,
            "violations": [f"Error validating expense data: {str(e)}"],
            "warnings": [],
            "required_documents": [],
            "policy_references": []
        }

def categorize_expense(description: str, merchant: str = "", amount: float = 0, tool_context=None) -> dict:
    """
    Enhanced expense categorization with confidence scoring and subcategories.
    
    Args:
        description: Expense description
        merchant: Merchant/vendor name
        amount: Expense amount (helps with categorization)
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        dict: Suggested category, subcategory, and confidence level
    """
    try:
        description_lower = description.lower()
        merchant_lower = merchant.lower()
        
        # Enhanced categorization logic with confidence scoring
        category_scores = {}
        
        # Transportation scoring
        transport_keywords = {
            "flight": 0.95, "airline": 0.9, "airfare": 0.95, "plane": 0.8,
            "uber": 0.9, "lyft": 0.9, "taxi": 0.85, "cab": 0.8, "rideshare": 0.85,
            "rental": 0.7, "hertz": 0.9, "avis": 0.9, "enterprise": 0.9,
            "parking": 0.8, "toll": 0.8, "mileage": 0.85, "gas": 0.6
        }
        
        for keyword, score in transport_keywords.items():
            if keyword in description_lower or keyword in merchant_lower:
                category_scores["transportation"] = max(
                    category_scores.get("transportation", 0), score
                )
        
        # Accommodation scoring
        lodging_keywords = {
            "hotel": 0.95, "motel": 0.9, "accommodation": 0.9, "lodging": 0.95,
            "resort": 0.85, "inn": 0.8, "marriott": 0.95, "hilton": 0.95,
            "hyatt": 0.95, "airbnb": 0.8, "booking": 0.7
        }
        
        for keyword, score in lodging_keywords.items():
            if keyword in description_lower or keyword in merchant_lower:
                category_scores["lodging"] = max(
                    category_scores.get("lodging", 0), score
                )
        
        # Meals & Entertainment scoring
        meal_keywords = {
            "restaurant": 0.9, "dinner": 0.85, "lunch": 0.85, "breakfast": 0.85,
            "meal": 0.9, "food": 0.7, "cafe": 0.8, "starbucks": 0.8,
            "mcdonald": 0.8, "subway": 0.8, "client dinner": 0.95
        }
        
        for keyword, score in meal_keywords.items():
            if keyword in description_lower or keyword in merchant_lower:
                category_scores["meals"] = max(
                    category_scores.get("meals", 0), score
                )
        
        # Office supplies scoring
        office_keywords = {
            "office": 0.9, "supplies": 0.85, "stationery": 0.9, "printer": 0.8,
            "paper": 0.7, "staples": 0.9, "depot": 0.8, "amazon": 0.4
        }
        
        for keyword, score in office_keywords.items():
            if keyword in description_lower or keyword in merchant_lower:
                category_scores["office_supplies"] = max(
                    category_scores.get("office_supplies", 0), score
                )
        
        # Determine best category
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            category, confidence = best_category
            
            # Determine subcategory based on specific keywords
            subcategory = "general"
            if category == "transportation":
                if any(word in description_lower for word in ["flight", "airline", "airfare"]):
                    subcategory = "airfare"
                elif any(word in description_lower for word in ["uber", "lyft", "taxi"]):
                    subcategory = "rideshare"
                elif "rental" in description_lower:
                    subcategory = "car_rental"
                elif any(word in description_lower for word in ["parking", "toll"]):
                    subcategory = "misc_transport"
                    
            elif category == "meals":
                if amount > 75:
                    subcategory = "business_meal"
                elif any(word in description_lower for word in ["breakfast"]):
                    subcategory = "breakfast"
                elif any(word in description_lower for word in ["lunch"]):
                    subcategory = "lunch"
                elif any(word in description_lower for word in ["dinner"]):
                    subcategory = "dinner"
            
            result = {
                "category": category,
                "subcategory": subcategory,
                "confidence": confidence,
                "alternative_categories": [
                    {"category": cat, "confidence": conf} 
                    for cat, conf in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
                ]
            }
        else:
            # Default categorization
            result = {
                "category": "miscellaneous",
                "subcategory": "other",
                "confidence": 0.2,
                "alternative_categories": []
            }
        
        # Update session state with categorization history
        if tool_context and tool_context.state:
            if "categorization_history" not in tool_context.state:
                tool_context.state["categorization_history"] = []
            
            tool_context.state["categorization_history"].append({
                "description": description,
                "merchant": merchant,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
        
        return result
        
    except Exception as e:
        return {
            "category": "miscellaneous", 
            "subcategory": "error",
            "confidence": 0.0,
            "error": str(e),
            "alternative_categories": []
        }

def generate_expense_summary(expenses: List[dict], tool_context=None) -> dict:
    """
    Generate comprehensive summary of multiple expenses for submission.
    
    Args:
        expenses: List of expense dictionaries
        tool_context: ADK tool context (automatically provided)
        
    Returns:
        dict: Detailed summary with totals, categories, and compliance analysis
    """
    try:
        summary = {
            "total_amount": 0.0,
            "expense_count": len(expenses),
            "categories": {},
            "compliance_status": {
                "total_violations": 0,
                "violations": [],
                "warnings": [],
                "ready_for_submission": True
            },
            "required_documents": [],
            "policy_references": [],
            "date_range": {},
            "statistics": {}
        }
        
        dates = []
        
        for i, expense in enumerate(expenses):
            try:
                amount = float(expense.get("amount", 0))
                category = expense.get("category", "miscellaneous")
                date = expense.get("date", "")
                
                summary["total_amount"] += amount
                
                # Track dates
                if date:
                    dates.append(date)
                
                # Category tracking
                if category not in summary["categories"]:
                    summary["categories"][category] = {
                        "count": 0, 
                        "total": 0.0, 
                        "average": 0.0,
                        "expenses": []
                    }
                
                summary["categories"][category]["count"] += 1
                summary["categories"][category]["total"] += amount
                summary["categories"][category]["expenses"].append({
                    "amount": amount,
                    "description": expense.get("description", ""),
                    "date": date
                })
                
                # Validate each expense
                validation = validate_expense_data(expense)
                
                if not validation["is_valid"]:
                    summary["compliance_status"]["total_violations"] += len(validation["violations"])
                    summary["compliance_status"]["violations"].extend([
                        f"Expense #{i+1}: {violation}" for violation in validation["violations"]
                    ])
                    summary["compliance_status"]["ready_for_submission"] = False
                
                # Collect warnings and required documents
                summary["compliance_status"]["warnings"].extend([
                    f"Expense #{i+1}: {warning}" for warning in validation.get("warnings", [])
                ])
                summary["required_documents"].extend(validation.get("required_documents", []))
                summary["policy_references"].extend(validation.get("policy_references", []))
                
            except Exception as e:
                summary["compliance_status"]["violations"].append(
                    f"Expense #{i+1}: Error processing expense - {str(e)}"
                )
                summary["compliance_status"]["ready_for_submission"] = False
        
        # Calculate category averages
        for category_data in summary["categories"].values():
            if category_data["count"] > 0:
                category_data["average"] = category_data["total"] / category_data["count"]
        
        # Remove duplicates
        summary["required_documents"] = list(set(summary["required_documents"]))
        summary["policy_references"] = list(set(summary["policy_references"]))
        
        # Date range analysis
        if dates:
            dates.sort()
            summary["date_range"] = {
                "start_date": dates[0],
                "end_date": dates[-1],
                "duration_days": (
                    datetime.fromisoformat(dates[-1].replace('Z', '+00:00')) - 
                    datetime.fromisoformat(dates[0].replace('Z', '+00:00'))
                ).days + 1 if len(dates) > 1 else 1
            }
        
        # Generate statistics
        if summary["expense_count"] > 0:
            summary["statistics"] = {
                "average_expense": summary["total_amount"] / summary["expense_count"],
                "largest_expense": max(float(exp.get("amount", 0)) for exp in expenses),
                "smallest_expense": min(float(exp.get("amount", 0)) for exp in expenses),
                "most_common_category": max(summary["categories"].items(), key=lambda x: x[1]["count"])[0] if summary["categories"] else "none"
            }
        
        # Update session state with summary
        if tool_context and tool_context.state:
            tool_context.state["expense_summary"] = {
                "timestamp": datetime.now().isoformat(),
                "total_amount": summary["total_amount"],
                "expense_count": summary["expense_count"],
                "ready_for_submission": summary["compliance_status"]["ready_for_submission"]
            }
        
        return summary
        
    except Exception as e:
        return {
            "total_amount": 0.0,
            "expense_count": 0,
            "categories": {},
            "compliance_status": {
                "total_violations": 1,
                "violations": [f"Error generating summary: {str(e)}"],
                "warnings": [],
                "ready_for_submission": False
            },
            "required_documents": [],
            "policy_references": [],
            "date_range": {},
            "statistics": {}
        }

# Create the enhanced Expense Report Assistant Agent
expense_assistant = Agent(
    name="expense_report_assistant",
    model="gemini-2.0-flash",
    description="An intelligent assistant that helps UnitedHealth Group employees prepare and submit expense reports in compliance with company travel and expense policies.",
    
    instruction="""
    You are the UnitedHealth Group Expense Report Assistant, a specialized AI agent designed to guide employees through the expense reporting process while ensuring full compliance with company policies.

    ## Your Core Mission:
    Help employees create accurate, compliant expense reports quickly and efficiently, reducing policy violations and processing delays.

    ## Your Capabilities:
    1. **Policy Expertise**: Use `search_expense_policy` to find relevant policy information for any expense-related questions
    2. **Smart Categorization**: Use `categorize_expense` to properly classify expenses with confidence scoring
    3. **Compliance Validation**: Use `validate_expense_data` to check expenses against policy rules in real-time
    4. **Report Generation**: Use `generate_expense_summary` to create comprehensive summaries for submission

    ## Interaction Guidelines:
    - **Be Proactive**: Always search for policy information when users have questions
    - **Be Precise**: Provide specific policy references and citations when giving guidance
    - **Be Helpful**: Guide users step-by-step through complex processes
    - **Be Compliant**: Always prioritize policy adherence and flag potential violations
    - **Be Thorough**: Validate all expenses and identify required documentation

    ## Standard Process Flow:
    1. **Welcome & Assess**: Understand what the user needs help with
    2. **Gather Details**: Collect expense information (amount, date, merchant, description, category)
    3. **Categorize**: Suggest appropriate expense categories with confidence levels
    4. **Validate**: Check against policy rules and identify any violations
    5. **Document**: Identify required receipts, approvals, or additional documentation
    6. **Summarize**: Provide comprehensive summary before submission
    7. **Guide**: Walk through final submission steps and requirements

    ## Key Behavioral Patterns:
    - Always search the policy database first when users ask policy questions
    - Provide confidence levels when categorizing expenses
    - Flag potential violations immediately with clear explanations
    - Offer specific guidance on how to resolve compliance issues
    - Maintain session context to remember previous expenses in a trip/report
    - Be encouraging while maintaining policy compliance standards

    ## Sample Interactions:
    **Policy Question**: "What's the meal allowance for business travel?"
    → Search policy database → Provide specific limits with policy references

    **Expense Entry**: "I paid $85 for dinner with a client"
    → Categorize as business meal → Validate against policy → Check documentation requirements

    **Compliance Issue**: "My hotel was $350/night" 
    → Flag policy violation → Explain limit → Suggest alternatives or approval process

    Remember: You're not just processing expenses - you're helping employees navigate company policies efficiently while ensuring compliance and reducing administrative burden.
    """,
    
    tools=[
        FunctionTool(search_expense_policy),
        FunctionTool(validate_expense_data), 
        FunctionTool(categorize_expense),
        FunctionTool(generate_expense_summary)
    ]
)

# Export as root_agent for ADK compatibility
root_agent = expense_assistant