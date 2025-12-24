"""
LangChain Tools for Government Scheme Agent.
Provides bilingual search and eligibility checking capabilities.
"""
import json
import os
from langchain.tools import tool
from typing import Optional

# Load schemes data
def _load_schemes():
    """Load schemes from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, "..", "data", "schemes.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

SCHEMES = _load_schemes()


@tool
def search_schemes(query: str, language: str = "te") -> str:
    """
    Search for government schemes based on keyword or sector.
    Use this when user asks about available schemes or wants to find schemes.
    
    Args:
        query: Search keyword (Telugu or English - like "farmer", "రైతు", "health", "ఆరోగ్యం")
        language: Response language ('te' for Telugu, 'en' for English)
    
    Returns:
        List of matching schemes with details in requested language
    """
    query_lower = query.lower()
    results = []
    
    # Keywords for better search
    sector_keywords = {
        "agriculture": ["రైతు", "farmer", "agriculture", "కృషి", "farming", "రైతులు"],
        "health": ["ఆరోగ్యం", "health", "చికిత్స", "medical", "hospital", "వైద్యం"],
        "housing": ["ఇల్లు", "house", "housing", "నివాసం", "ఆవాసం"],
        "finance": ["బ్యాంక్", "bank", "money", "ఆర్థిక", "finance", "ఖాతా"],
        "insurance": ["బీమా", "insurance", "సురక్ష"],
        "energy": ["గ్యాస్", "gas", "LPG", "ఉజ్జ్వల", "energy"]
    }
    
    for scheme in SCHEMES:
        # Check direct name/description match
        name_field = f"name_{language}"
        desc_field = f"description_{language}"
        
        if (query_lower in scheme.get(name_field, "").lower() or 
            query_lower in scheme.get(desc_field, "").lower() or
            query_lower in scheme.get("name_te", "").lower() or
            query_lower in scheme.get("name_en", "").lower()):
            results.append(scheme)
            continue
        
        # Check sector match via keywords
        for sector, keywords in sector_keywords.items():
            if any(kw in query_lower for kw in keywords):
                if scheme["sector"] == sector:
                    results.append(scheme)
                    break
    
    if not results:
        return "కోరిన యోజనలు కనబడలేదు. దయచేసి వేరే పదాలతో వెతకండి." if language == "te" else "No schemes found. Please search with different keywords."
    
    # Format results
    if language == "te":
        response = f"నేను {len(results)} యోజనలను కనుగొన్నాను:\n\n"
        for i, scheme in enumerate(results, 1):
            response += f"{i}. **{scheme['name_te']}**\n"
            response += f"   వివరణ: {scheme['description_te']}\n"
            response += f"   లాభాలు: {scheme['benefits_te']}\n"
            response += f"   అవసరమైన పత్రాలు: {', '.join(scheme['documents_te'])}\n\n"
    else:
        response = f"I found {len(results)} schemes:\n\n"
        for i, scheme in enumerate(results, 1):
            response += f"{i}. **{scheme['name_en']}**\n"
            response += f"   Description: {scheme['description_en']}\n"
            response += f"   Benefits: {scheme['benefits_en']}\n"
            response += f"   Required documents: {', '.join(scheme['documents_en'])}\n\n"
    
    return response


@tool
def check_eligibility(scheme_name: str, age: int, annual_income: int,
                      occupation: Optional[str] = None,
                      category: Optional[str] = None,
                      language: str = "te") -> str:
    """
    Check if a user is eligible for a specific government scheme.
    Use this when user provides details and wants to know eligibility.
    
    Args:
        scheme_name: Name of the scheme (Telugu or English)
        age: User's age in years
        annual_income: User's annual income in rupees
        occupation: User's occupation (e.g., "farmer", "రైతు")
        category: User's category (e.g., "BPL", "EWS")
        language: Response language ('te' or 'en')
    
    Returns:
        Eligibility status and reason in requested language
    """
    # Find the scheme
    scheme = None
    for s in SCHEMES:
        if (scheme_name.lower() in s.get("name_te", "").lower() or
            scheme_name.lower() in s.get("name_en", "").lower() or
            scheme_name.lower() in s["id"].lower()):
            scheme = s
            break
    
    if not scheme:
        return f"'{scheme_name}' పేరుతో యోజన కనబడలేదు." if language == "te" else f"Scheme '{scheme_name}' not found."
    
    eligibility = scheme["eligibility"]
    issues = []
    
    # Check age
    if "min_age" in eligibility and age < eligibility["min_age"]:
        issues.append(f"వయస్సు {eligibility['min_age']} సంవత్సరాల కంటే తక్కువ" if language == "te" else f"Age below {eligibility['min_age']} years")
    if "max_age" in eligibility and age > eligibility["max_age"]:
        issues.append(f"వయస్సు {eligibility['max_age']} సంవత్సరాల కంటే ఎక్కువ" if language == "te" else f"Age above {eligibility['max_age']} years")
    
    # Check income
    if eligibility.get("income_limit") and annual_income > eligibility["income_limit"]:
        issues.append(f"ఆదాయం పరిమితి (₹{eligibility['income_limit']:,}) కంటే ఎక్కువ" if language == "te" else f"Income exceeds limit (₹{eligibility['income_limit']:,})")
    
    # Check occupation
    if "occupation" in eligibility:
        required_occ = eligibility["occupation"].lower()
        user_occ = (occupation or "").lower()
        is_farmer = ("farmer" in required_occ or "రైతు" in required_occ) and ("farmer" in user_occ or "రైతు" in user_occ)
        if not is_farmer and required_occ not in user_occ:
            issues.append("ఈ యోజన రైతులకు మాత్రమే" if language == "te" else "This scheme is only for farmers")
    
    # Check category
    if "category" in eligibility:
        valid_categories = eligibility["category"]
        if "all" not in valid_categories:
            if category and category.upper() not in [c.upper() for c in valid_categories]:
                cat_list = ", ".join(valid_categories)
                issues.append(f"వర్గం {cat_list} లో ఒకటి అయి ఉండాలి" if language == "te" else f"Category must be one of {cat_list}")
            elif not category:
                cat_list = ", ".join(valid_categories)
                issues.append(f"మీ వర్గం ({cat_list}) లో ఒకటి అయి ఉండాలి" if language == "te" else f"Your category should be one of ({cat_list})")
    
    # Generate response
    name_field = f"name_{language}"
    benefits_field = f"benefits_{language}"
    docs_field = f"documents_{language}"
    
    if issues:
        if language == "te":
            response = f"❌ మీరు **{scheme[name_field]}** కు అర్హులు కాదు.\n\n"
            response += "కారణాలు:\n"
            for issue in issues:
                response += f"• {issue}\n"
        else:
            response = f"❌ You are not eligible for **{scheme[name_field]}**.\n\n"
            response += "Reasons:\n"
            for issue in issues:
                response += f"• {issue}\n"
    else:
        if language == "te":
            response = f"✅ అభినందనలు! మీరు **{scheme[name_field]}** కు అర్హులు!\n\n"
            response += f"లాభాలు: {scheme[benefits_field]}\n"
            response += f"అవసరమైన పత్రాలు: {', '.join(scheme[docs_field])}\n"
            response += "\nదరఖాస్తు కోసం మీకు సమీపంలో ఉన్న CSC కేంద్రం లేదా ప్రభుత్వ కార్యాలయానికి వెళ్లండి."
        else:
            response = f"✅ Congratulations! You are eligible for **{scheme[name_field]}**!\n\n"
            response += f"Benefits: {scheme[benefits_field]}\n"
            response += f"Required documents: {', '.join(scheme[docs_field])}\n"
            response += "\nVisit your nearest CSC center or government office to apply."
    
    return response


@tool
def get_all_schemes(language: str = "te") -> str:
    """
    Get a list of all available government schemes.
    Use this when user wants to see all schemes.
    
    Args:
        language: Response language ('te' or 'en')
    
    Returns:
        List of all schemes in requested language
    """
    if language == "te":
        response = "అందుబాటులో ఉన్న ప్రభుత్వ యోజనలు:\n\n"
        for i, scheme in enumerate(SCHEMES, 1):
            response += f"{i}. **{scheme['name_te']}** ({scheme['sector']})\n"
            response += f"   {scheme['description_te'][:80]}...\n\n"
        response += "ఏదైనా యోజన యొక్క పూర్తి సమాచారం కోసం దాని పేరు చెప్పండి."
    else:
        response = "Available Government Schemes:\n\n"
        for i, scheme in enumerate(SCHEMES, 1):
            response += f"{i}. **{scheme['name_en']}** ({scheme['sector']})\n"
            response += f"   {scheme['description_en'][:80]}...\n\n"
        response += "Tell me the scheme name for complete information."
    
    return response


@tool
def compare_schemes(scheme1: str, scheme2: str, language: str = "te") -> str:
    """
    Compare two government schemes side by side.
    Use this when user wants to compare different schemes.
    
    Args:
        scheme1: First scheme name
        scheme2: Second scheme name
        language: Response language ('te' or 'en')
    
    Returns:
        Comparison table with benefits, eligibility, and documents
    """
    # Find schemes
    s1 = None
    s2 = None
    for s in SCHEMES:
        name_lower = scheme1.lower()
        if (name_lower in s.get("name_te", "").lower() or 
            name_lower in s.get("name_en", "").lower() or 
            name_lower in s["id"].lower()):
            s1 = s
        
        name_lower = scheme2.lower()
        if (name_lower in s.get("name_te", "").lower() or 
            name_lower in s.get("name_en", "").lower() or 
            name_lower in s["id"].lower()):
            s2 = s
    
    if not s1 or not s2:
        return "ఒకటి లేదా రెండు యోజనలు కనబడలేదు" if language == "te" else "One or both schemes not found"
    
    if language == "te":
        response = f"**యోజనల పోలిక:**\n\n"
        response += f"📋 **{s1['name_te']}** vs **{s2['name_te']}**\n\n"
        response += f"🎯 **లక్ష్యం:**\n"
        response += f"• యోజన 1: {s1['description_te']}\n"
        response += f"• యోజన 2: {s2['description_te']}\n\n"
        response += f"💰 **లాభాలు:**\n"
        response += f"• యోజన 1: {s1['benefits_te']}\n"
        response += f"• యోజన 2: {s2['benefits_te']}\n\n"
        response += f"📄 **అవసరమైన పత్రాలు:**\n"
        response += f"• యోజన 1: {', '.join(s1['documents_te'])}\n"
        response += f"• యోజన 2: {', '.join(s2['documents_te'])}\n"
    else:
        response = f"**Scheme Comparison:**\n\n"
        response += f"📋 **{s1['name_en']}** vs **{s2['name_en']}**\n\n"
        response += f"🎯 **Purpose:**\n"
        response += f"• Scheme 1: {s1['description_en']}\n"
        response += f"• Scheme 2: {s2['description_en']}\n\n"
        response += f"💰 **Benefits:**\n"
        response += f"• Scheme 1: {s1['benefits_en']}\n"
        response += f"• Scheme 2: {s2['benefits_en']}\n\n"
        response += f"📄 **Required Documents:**\n"
        response += f"• Scheme 1: {', '.join(s1['documents_en'])}\n"
        response += f"• Scheme 2: {', '.join(s2['documents_en'])}\n"
    
    return response


@tool
def calculate_benefits(scheme_name: str, family_size: int = 1, land_acres: float = 0, 
                       months: int = 12, language: str = "te") -> str:
    """
    Calculate estimated annual benefits from a scheme.
    Use this when user asks "how much will I get" or wants to know benefit amount.
    
    Args:
        scheme_name: Name of the scheme
        family_size: Number of family members (default: 1)
        land_acres: Agricultural land in acres (for farmer schemes, default: 0)
        months: Number of months (default: 12 for annual)
        language: Response language ('te' or 'en')
    
    Returns:
        Calculated benefit amount with breakdown
    """
    # Find scheme
    scheme = None
    for s in SCHEMES:
        if (scheme_name.lower() in s.get("name_te", "").lower() or
            scheme_name.lower() in s.get("name_en", "").lower() or
            scheme_name.lower() in s["id"].lower()):
            scheme = s
            break
    
    if not scheme:
        return f"'{scheme_name}' యోజన కనబడలేదు" if language == "te" else f"Scheme '{scheme_name}' not found"
    
    # Calculate based on scheme type
    scheme_id = scheme["id"]
    
    if scheme_id == "pm_kisan":
        annual = 6000
        total = annual * (months / 12)
        if language == "te":
            response = f"**PM కిసాన్ లాభాల లెక్కింపు:**\n\n"
            response += f"💰 వార్షిక మొత్తం: ₹{annual:,}\n"
            response += f"📅 {months} నెలల కోసం: ₹{total:,.0f}\n"
            response += f"💳 చెల్లింపు విధానం: 3 విడతలుగా (ప్రతి ₹2,000)\n"
        else:
            response = f"**PM Kisan Benefits Calculator:**\n\n"
            response += f"💰 Annual Amount: ₹{annual:,}\n"
            response += f"📅 For {months} months: ₹{total:,.0f}\n"
            response += f"💳 Payment Mode: 3 installments (₹2,000 each)\n"
    
    elif scheme_id == "pm_awas":
        amount = 120000
        if language == "te":
            response = f"**PM ఆవాస్ లాభాల లెక్కింపు:**\n\n"
            response += f"💰 మొత్తం సహాయం: ₹{amount:,}\n"
            response += f"🏠 కుటుంబ సభ్యులు: {family_size}\n"
            response += f"📋 గమనిక: ఇది ఒక్కసారి సహాయం\n"
        else:
            response = f"**PM Awas Benefits Calculator:**\n\n"
            response += f"💰 Total Assistance: ₹{amount:,}\n"
            response += f"🏠 Family Size: {family_size}\n"
            response += f"📋 Note: This is a one-time assistance\n"
    
    elif scheme_id == "ayushman_bharat":
        coverage = 500000
        if language == "te":
            response = f"**ఆయుష్మాన్ భారత్ లాభాల లెక్కింపు:**\n\n"
            response += f"💰 వార్షిక కవరేజ్: ₹{coverage:,}\n"
            response += f"👨‍👩‍👧‍👦 కుటుంబ సభ్యులు: {family_size}\n"
            response += f"🏥 ప్రతి కుటుంబానికి: ₹{coverage:,}\n"
            response += f"📋 గమనిక: ఆరోగ్య బీమా కవరేజ్\n"
        else:
            response = f"**Ayushman Bharat Benefits Calculator:**\n\n"
            response += f"💰 Annual Coverage: ₹{coverage:,}\n"
            response += f"👨‍👩‍👧‍👦 Family Members: {family_size}\n"
            response += f"🏥 Per Family: ₹{coverage:,}\n"
            response += f"📋 Note: Health insurance coverage\n"
    
    else:
        if language == "te":
            response = f"**{scheme['name_te']} లాభాలు:**\n\n"
            response += f"💰 {scheme['benefits_te']}\n"
            response += f"📋 ఖచ్చితమైన మొత్తం కోసం సంబంధిత కార్యాలయాన్ని సంప్రదించండి.\n"
        else:
            response = f"**{scheme['name_en']} Benefits:**\n\n"
            response += f"💰 {scheme['benefits_en']}\n"
            response += f"📋 Contact relevant office for exact amount.\n"
    
    return response


@tool
def get_application_steps(scheme_name: str, language: str = "te") -> str:
    """
    Get step-by-step application process for a scheme.
    Use this when user asks "how to apply" or "application process".
    
    Args:
        scheme_name: Name of the scheme
        language: Response language ('te' or 'en')
    
    Returns:
        Detailed application steps
    """
    # Find scheme
    scheme = None
    for s in SCHEMES:
        if (scheme_name.lower() in s.get("name_te", "").lower() or
            scheme_name.lower() in s.get("name_en", "").lower() or
            scheme_name.lower() in s["id"].lower()):
            scheme = s
            break
    
    if not scheme:
        return f"'{scheme_name}' యోజన కనబడలేదు" if language == "te" else f"Scheme '{scheme_name}' not found"
    
    if language == "te":
        response = f"**{scheme['name_te']} - దరఖాస్తు విధానం:**\n\n"
        response += "📝 **దశలు:**\n\n"
        response += "1️⃣ **అవసరమైన పత్రాలను సేకరించండి:**\n"
        for doc in scheme['documents_te']:
            response += f"   • {doc}\n"
        response += "\n2️⃣ **సమీప CSC సెంటర్ / ప్రభుత్వ కార్యాలయానికి వెళ్లండి**\n"
        response += "\n3️⃣ **దరఖాస్తు ఫారం పూరించండి**\n"
        response += "\n4️⃣ **పత్రాలను జమ చేయండి**\n"
        response += "\n5️⃣ **రసీదు తీసుకోండి**\n"
        response += "\n6️⃣ **మీ దరఖాస్తు స్థితిని ట్రాక్ చేయండి**\n"
        response += f"\n💡 **చిట్కా:** అన్ని అసలు పత్రాలతో పాటు ఫోటో కాపీలు తీసుకెళ్లండి.\n"
    else:
        response = f"**{scheme['name_en']} - Application Process:**\n\n"
        response += "📝 **Steps:**\n\n"
        response += "1️⃣ **Collect Required Documents:**\n"
        for doc in scheme['documents_en']:
            response += f"   • {doc}\n"
        response += "\n2️⃣ **Visit Nearest CSC Center / Government Office**\n"
        response += "\n3️⃣ **Fill Application Form**\n"
        response += "\n4️⃣ **Submit Documents**\n"
        response += "\n5️⃣ **Collect Receipt**\n"
        response += "\n6️⃣ **Track Your Application Status**\n"
        response += f"\n💡 **Tip:** Carry photocopies along with original documents.\n"
    
    return response


@tool
def get_schemes_by_sector(sector: str, language: str = "te") -> str:
    """
    Get all schemes in a specific sector (agriculture, health, housing, etc).
    Use this when user asks about schemes in a particular category/sector.
    
    Args:
        sector: Sector name (agriculture, health, housing, finance, insurance, energy)
        language: Response language ('te' or 'en')
    
    Returns:
        List of schemes in that sector
    """
    sector_map = {
        "agriculture": "agriculture",
        "రైతు": "agriculture",
        "కృషి": "agriculture",
        "health": "health",
        "ఆరోగ్యం": "health",
        "housing": "housing",
        "ఇల్లు": "housing",
        "finance": "finance",
        "బ్యాంక్": "finance",
        "insurance": "insurance",
        "బీమా": "insurance",
        "energy": "energy",
        "గ్యాస్": "energy"
    }
    
    target_sector = sector_map.get(sector.lower(), sector.lower())
    results = [s for s in SCHEMES if s["sector"] == target_sector]
    
    if not results:
        return f"'{sector}' విభాగంలో యోజనలు కనబడలేదు" if language == "te" else f"No schemes found in '{sector}' sector"
    
    if language == "te":
        response = f"**{sector} విభాగం యోజనలు:**\n\n"
        for i, scheme in enumerate(results, 1):
            response += f"{i}. **{scheme['name_te']}**\n"
            response += f"   {scheme['description_te']}\n"
            response += f"   లాభాలు: {scheme['benefits_te']}\n\n"
    else:
        response = f"**{sector.title()} Sector Schemes:**\n\n"
        for i, scheme in enumerate(results, 1):
            response += f"{i}. **{scheme['name_en']}**\n"
            response += f"   {scheme['description_en']}\n"
            response += f"   Benefits: {scheme['benefits_en']}\n\n"
    
    return response


# Test tools
if __name__ == "__main__":
    print("=== Testing Tools ===\n")
    
    print("1. Search for farmer schemes (Telugu):")
    print(search_schemes.invoke({"query": "రైతు", "language": "te"}))
    
    print("\n2. Check eligibility:")
    print(check_eligibility.invoke({
        "scheme_name": "PM Kisan",
        "age": 35,
        "annual_income": 150000,
        "occupation": "farmer",
        "language": "en"
    }))
    
    print("\n3. Get all schemes (English):")
    print(get_all_schemes.invoke({"language": "en"}))
    
    print("\n4. Compare schemes:")
    print(compare_schemes.invoke({"scheme1": "PM Kisan", "scheme2": "PM Awas", "language": "en"}))
    
    print("\n5. Calculate benefits:")
    print(calculate_benefits.invoke({"scheme_name": "PM Kisan", "months": 12, "language": "en"}))
    
    print("\n6. Get application steps:")
    print(get_application_steps.invoke({"scheme_name": "Ayushman", "language": "te"}))
