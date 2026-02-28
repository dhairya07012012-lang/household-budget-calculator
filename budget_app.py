import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import io

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Household Budget Calculator",
    page_icon="💰",
    layout="wide"
)

# ==================== SESSION STATE ====================
def init_state():
    defaults = {
        'user_name': '',
        'setup_done': False,
        'expenses': [],
        'income': 0,
        'savings_goal': 0,
        'api_key': ''
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ==================== EXPENSE CATEGORIES ====================
CATEGORIES = {
    '🏠 Housing': ['Rent', 'Mortgage', 'Property Tax', 'Home Insurance', 'Maintenance'],
    '⚡ Utilities': ['Electricity', 'Water', 'Gas', 'Internet', 'Phone', 'Trash'],
    '🍔 Food': ['Groceries', 'Dining Out', 'Coffee', 'Snacks', 'Fast Food'],
    '🥛 Dairy & Essentials': ['Milk', 'Bread', 'Eggs', 'Butter', 'Cheese', 'Rice', 'Oil'],
    '🚗 Transportation': ['Car Payment', 'Fuel', 'Insurance', 'Maintenance', 'Public Transport', 'Parking'],
    '💳 Loans & Debts': ['Credit Card', 'Personal Loan', 'Student Loan', 'Car Loan', 'EMI'],
    '🎬 Entertainment': ['Movies', 'Streaming', 'Games', 'Hobbies', 'Outings', 'Sports'],
    '👕 Shopping': ['Clothes', 'Electronics', 'Home Goods', 'Personal Care', 'Cosmetics'],
    '🏥 Healthcare': ['Insurance', 'Medications', 'Doctor Visits', 'Gym', 'Vitamins'],
    '👶 Kids': ['School Fees', 'Supplies', 'Toys', 'Clothes', 'Activities', 'Tuition'],
    '📚 Education': ['Courses', 'Books', 'Tuition', 'Online Learning', 'Coaching'],
    '💼 Other': ['Gifts', 'Donations', 'Pet Care', 'Travel', 'Miscellaneous']
}

# ==================== CSS ====================
st.markdown("""
<style>
    .stApp {
        background: #f5f7fa;
    }
    
    #MainMenu, footer {
        visibility: hidden;
    }
    
    .welcome-container {
        text-align: center;
        padding: 3rem;
        max-width: 500px;
        margin: 5rem auto;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    
    .welcome-icon {
        font-size: 5rem;
        margin-bottom: 1rem;
    }
    
    .welcome-title {
        font-size: 2rem;
        font-weight: 700;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .welcome-subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    
    .main-header {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #333;
        margin: 1rem 0;
    }
    
    .greeting {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #5e72e4;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.3rem;
    }
    
    .positive {
        color: #2dce89 !important;
    }
    
    .negative {
        color: #f5365c !important;
    }
    
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #333;
        margin: 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #5e72e4;
    }
    
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    
    .calc-display {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        font-size: 2rem;
        font-family: monospace;
        text-align: right;
        margin-bottom: 1rem;
        border: 2px solid #e9ecef;
    }
    
    .calc-button {
        font-size: 1.2rem;
        padding: 1rem;
        margin: 2px;
        border-radius: 10px;
        border: none;
        cursor: pointer;
    }
    
    .pie-chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNCTIONS ====================
def add_expense(category, subcategory, amount, date, note=''):
    expense = {
        'date': date.strftime('%Y-%m-%d'),
        'category': category,
        'subcategory': subcategory,
        'amount': float(amount),
        'note': note
    }
    st.session_state.expenses.append(expense)

def get_total_expenses():
    return sum(exp['amount'] for exp in st.session_state.expenses)

def get_expenses_by_category():
    if not st.session_state.expenses:
        return {}
    df = pd.DataFrame(st.session_state.expenses)
    return df.groupby('category')['amount'].sum().to_dict()

def get_ai_advice(api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        category_breakdown = get_expenses_by_category()
        total_expenses = get_total_expenses()
        expense_details = "\n".join([f"- {cat}: ₹{amt:,.2f}" for cat, amt in category_breakdown.items()])
        
        prompt = f"""I am {st.session_state.user_name}. I need financial advice for my household budget:

Monthly Income: ₹{st.session_state.income:,.2f}
Total Expenses: ₹{total_expenses:,.2f}
Net Savings: ₹{st.session_state.income - total_expenses:,.2f}

Expense Breakdown:
{expense_details}

Please provide:
1. Budget health assessment (2-3 sentences)
2. Top 3 areas where I can save money
3. Specific actionable recommendations
4. Emergency fund suggestion

Keep it concise and practical for an Indian household. Address me by my name."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful financial advisor specializing in household budgeting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== WELCOME PAGE ====================
def show_welcome():
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-icon">💰</div>
        <div class="welcome-title">Household Budget Calculator</div>
        <div class="welcome-subtitle">Track, Analyze & Save Money Smartly</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.form("welcome_form"):
            name = st.text_input(
                "👤 What's your name?",
                placeholder="Enter your name..."
            )
            
            income = st.number_input(
                "💵 Monthly Income (₹)",
                min_value=0,
                value=50000,
                step=1000
            )
            
            savings = st.number_input(
                "🎯 Monthly Savings Goal (₹)",
                min_value=0,
                value=10000,
                step=500
            )
            
            submitted = st.form_submit_button(
                "🚀 Start Budgeting",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                if name and name.strip():
                    st.session_state.user_name = name.strip()
                    st.session_state.income = income
                    st.session_state.savings_goal = savings
                    st.session_state.setup_done = True
                    st.rerun()
                else:
                    st.error("Please enter your name")

# ==================== MAIN DASHBOARD ====================
def show_dashboard():
    now = datetime.now()
    total_expenses = get_total_expenses()
    remaining = st.session_state.income - total_expenses
    
    # Header with greeting
    hour = now.hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    
    st.markdown(f'<h1 class="main-header">💰 Household Budget Calculator</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="greeting">{greeting}, {st.session_state.user_name}! 👋</p>', unsafe_allow_html=True)
    
    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.markdown(f"📅 {now.strftime('%d %B %Y')}")
        
        st.markdown("---")
        
        # Quick Stats
        st.markdown("### 📊 Quick Stats")
        st.metric("Income", f"₹{st.session_state.income:,}")
        st.metric("Spent", f"₹{total_expenses:,.0f}")
        st.metric("Left", f"₹{remaining:,.0f}")
        
        st.markdown("---")
        
        # Settings
        st.markdown("### ⚙️ Settings")
        
        new_income = st.number_input(
            "Monthly Income",
            value=st.session_state.income,
            step=1000
        )
        if new_income != st.session_state.income:
            st.session_state.income = new_income
        
        new_goal = st.number_input(
            "Savings Goal",
            value=st.session_state.savings_goal,
            step=500
        )
        if new_goal != st.session_state.savings_goal:
            st.session_state.savings_goal = new_goal
        
        st.markdown("---")
        
        # API Key
        st.markdown("### 🤖 AI Advisor")
        api_key = st.text_input(
            "OpenAI API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-..."
        )
        st.session_state.api_key = api_key
        
        if api_key:
            st.success("✅ AI Ready")
        else:
            st.info("Optional")
        
        st.markdown("[Get Key →](https://platform.openai.com/api-keys)")
        
        st.markdown("---")
        
        # Data Management
        st.markdown("### 💾 Data")
        
        # Export
        if st.session_state.expenses:
            data = {
                'user': st.session_state.user_name,
                'income': st.session_state.income,
                'savings_goal': st.session_state.savings_goal,
                'expenses': st.session_state.expenses
            }
            st.download_button(
                "📥 Export",
                json.dumps(data, indent=2),
                f"budget_{st.session_state.user_name}_{now.strftime('%Y%m%d')}.json",
                use_container_width=True
            )
        
        # Import
        uploaded = st.file_uploader("📤 Import", type=['json'], label_visibility="collapsed")
        if uploaded:
            try:
                data = json.load(uploaded)
                st.session_state.user_name = data.get('user', 'User')
                st.session_state.income = data.get('income', 0)
                st.session_state.savings_goal = data.get('savings_goal', 0)
                st.session_state.expenses = data.get('expenses', [])
                st.success("✅ Imported!")
                st.rerun()
            except:
                st.error("Invalid file")
        
        st.markdown("---")
        
        # Logout
        if st.button("🚪 Change User", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.user_name = ''
            st.session_state.expenses = []
            st.rerun()
        
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.expenses = []
            st.success("Cleared!")
            st.rerun()
    
    # ==================== SUMMARY CARDS ====================
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">₹{st.session_state.income:,}</div>
            <div class="metric-label">💵 Monthly Income</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">₹{total_expenses:,.0f}</div>
            <div class="metric-label">💸 Total Spent</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = "positive" if remaining >= 0 else "negative"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value {color}">₹{remaining:,.0f}</div>
            <div class="metric-label">💰 Remaining</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        progress = (remaining / st.session_state.savings_goal * 100) if st.session_state.savings_goal > 0 else 0
        icon = "✅" if remaining >= st.session_state.savings_goal else "⏳"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{icon} {min(progress, 100):.0f}%</div>
            <div class="metric-label">🎯 Savings Goal</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== PIE CHART (PROMINENT) ====================
    st.markdown('<div class="section-title">📊 Your Spending Overview</div>', unsafe_allow_html=True)
    
    category_data = get_expenses_by_category()
    
    if category_data:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="pie-chart-container">', unsafe_allow_html=True)
            
            fig = px.pie(
                values=list(category_data.values()),
                names=list(category_data.keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(
                textposition='outside',
                textinfo='percent+label',
                textfont_size=12
            )
            fig.update_layout(
                height=450,
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5),
                margin=dict(t=20, b=20, l=20, r=20),
                title={
                    'text': f"💰 {st.session_state.user_name}'s Expenses Breakdown",
                    'y': 0.98,
                    'x': 0.5,
                    'xanchor': 'center'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📋 Category Summary")
            
            sorted_cats = dict(sorted(category_data.items(), key=lambda x: x[1], reverse=True))
            
            for cat, amount in sorted_cats.items():
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                st.markdown(f"**{cat}**")
                st.progress(min(percentage / 100, 1.0))
                st.caption(f"₹{amount:,.0f} ({percentage:.1f}%)")
                st.markdown("")
    else:
        st.info(f"👋 Hi {st.session_state.user_name}! Add your first expense to see the spending chart.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== TABS ====================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add Expense",
        "📋 Expenses List",
        "🧮 Calculator",
        "🤖 AI Advisor",
        "📈 Reports"
    ])
    
    # ==================== TAB 1: ADD EXPENSE ====================
    with tab1:
        st.markdown('<div class="section-title">➕ Add New Expense</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("expense_form", clear_on_submit=True):
                row1_col1, row1_col2 = st.columns(2)
                
                with row1_col1:
                    category = st.selectbox("Category *", list(CATEGORIES.keys()))
                
                with row1_col2:
                    subcategory = st.selectbox("Item *", CATEGORIES[category])
                
                row2_col1, row2_col2 = st.columns(2)
                
                with row2_col1:
                    amount = st.number_input("Amount (₹) *", min_value=0.0, step=10.0, format="%.2f")
                
                with row2_col2:
                    date = st.date_input("Date *", datetime.now())
                
                note = st.text_input("Note (Optional)", placeholder="Any additional details...")
                
                submitted = st.form_submit_button("💾 Add Expense", type="primary", use_container_width=True)
                
                if submitted:
                    if amount > 0:
                        add_expense(category, subcategory, amount, date, note)
                        st.success(f"✅ Added: {subcategory} - ₹{amount:,.2f}")
                        st.rerun()
                    else:
                        st.error("Amount must be greater than 0")
        
        with col2:
            st.markdown("### 💡 Common Prices")
            
            st.info("""
            **Daily Essentials:**
            - 🥛 Milk: ₹25-60/liter
            - 🍞 Bread: ₹30-50
            - 🥚 Eggs: ₹6-8 each
            
            **Utilities (Monthly):**
            - ⚡ Electricity: ₹500-3000
            - 📱 Phone: ₹199-999
            - 🌐 Internet: ₹500-1500
            
            **Transport:**
            - ⛽ Petrol: ₹100/liter
            - 🚌 Metro: ₹20-60
            """)
    
    # ==================== TAB 2: EXPENSES LIST ====================
    with tab2:
        st.markdown('<div class="section-title">📋 All Expenses</div>', unsafe_allow_html=True)
        
        if not st.session_state.expenses:
            st.info("No expenses yet. Add your first expense!")
        else:
            # Filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_cat = st.selectbox("Category", ["All"] + list(CATEGORIES.keys()), key="filter_cat")
            
            with col2:
                sort_option = st.selectbox("Sort by", ["Date (New)", "Date (Old)", "Amount ↑", "Amount ↓"])
            
            with col3:
                df = pd.DataFrame(st.session_state.expenses)
                df['date'] = pd.to_datetime(df['date'])
                months = ["All"] + sorted(df['date'].dt.strftime('%Y-%m').unique().tolist(), reverse=True)
                filter_month = st.selectbox("Month", months)
            
            # Filter & Sort
            filtered = df.copy()
            
            if filter_cat != "All":
                filtered = filtered[filtered['category'] == filter_cat]
            
            if filter_month != "All":
                filtered = filtered[filtered['date'].dt.strftime('%Y-%m') == filter_month]
            
            if sort_option == "Date (New)":
                filtered = filtered.sort_values('date', ascending=False)
            elif sort_option == "Date (Old)":
                filtered = filtered.sort_values('date', ascending=True)
            elif sort_option == "Amount ↑":
                filtered = filtered.sort_values('amount', ascending=True)
            else:
                filtered = filtered.sort_values('amount', ascending=False)
            
            # Display
            st.caption(f"Showing {len(filtered)} of {len(df)} expenses")
            
            display_df = filtered.copy()
            display_df['date'] = display_df['date'].dt.strftime('%
