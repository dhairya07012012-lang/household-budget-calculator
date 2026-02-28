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
if 'user_name' not in st.session_state:
    st.session_state.user_name = ''
if 'setup_done' not in st.session_state:
    st.session_state.setup_done = False
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'income' not in st.session_state:
    st.session_state.income = 0
if 'savings_goal' not in st.session_state:
    st.session_state.savings_goal = 0
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'calc_display' not in st.session_state:
    st.session_state.calc_display = '0'
if 'calc_first' not in st.session_state:
    st.session_state.calc_first = None
if 'calc_operator' not in st.session_state:
    st.session_state.calc_operator = None
if 'calc_new' not in st.session_state:
    st.session_state.calc_new = True

# ==================== CATEGORIES ====================
CATEGORIES = {
    '🏠 Housing': ['Rent', 'Mortgage', 'Property Tax', 'Insurance', 'Maintenance'],
    '⚡ Utilities': ['Electricity', 'Water', 'Gas', 'Internet', 'Phone'],
    '🍔 Food': ['Groceries', 'Dining Out', 'Coffee', 'Snacks'],
    '🥛 Dairy & Essentials': ['Milk', 'Bread', 'Eggs', 'Butter', 'Rice', 'Oil'],
    '🚗 Transportation': ['Fuel', 'Car Payment', 'Insurance', 'Maintenance', 'Public Transport'],
    '💳 Loans & Debts': ['Credit Card', 'Personal Loan', 'Student Loan', 'EMI'],
    '🎬 Entertainment': ['Movies', 'Streaming', 'Games', 'Hobbies'],
    '👕 Shopping': ['Clothes', 'Electronics', 'Home Goods', 'Personal Care'],
    '🏥 Healthcare': ['Insurance', 'Medications', 'Doctor', 'Gym'],
    '👶 Kids': ['School Fees', 'Supplies', 'Toys', 'Activities'],
    '📚 Education': ['Courses', 'Books', 'Tuition'],
    '💼 Other': ['Gifts', 'Donations', 'Travel', 'Misc']
}

# ==================== CSS ====================
st.markdown("""
<style>
    #MainMenu, footer {visibility: hidden;}
    
    .welcome-box {
        text-align: center;
        padding: 2rem;
        max-width: 450px;
        margin: 3rem auto;
        background: white;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .main-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #333;
        margin: 1rem 0;
    }
    
    .greeting {
        text-align: center;
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #5e72e4;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #666;
    }
    
    .section-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #333;
        margin: 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #5e72e4;
    }
    
    .calc-display {
        background: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        font-size: 1.8rem;
        font-family: monospace;
        text-align: right;
        margin-bottom: 1rem;
        border: 2px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FUNCTIONS ====================
def add_expense(cat, subcat, amt, date, note):
    st.session_state.expenses.append({
        'date': date.strftime('%Y-%m-%d'),
        'category': cat,
        'subcategory': subcat,
        'amount': float(amt),
        'note': note
    })

def get_total():
    return sum(e['amount'] for e in st.session_state.expenses)

def get_by_category():
    if not st.session_state.expenses:
        return {}
    df = pd.DataFrame(st.session_state.expenses)
    return df.groupby('category')['amount'].sum().to_dict()

def get_ai_advice(api_key):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        cats = get_by_category()
        total = get_total()
        details = "\n".join([f"- {c}: Rs.{a:,.0f}" for c, a in cats.items()])
        
        prompt = f"""I am {st.session_state.user_name}. Budget advice needed:

Income: Rs.{st.session_state.income:,}
Expenses: Rs.{total:,.0f}
Savings: Rs.{st.session_state.income - total:,.0f}

Breakdown:
{details}

Give:
1. Health assessment (2 sentences)
2. Top 3 saving tips
3. Recommendations
Keep concise for Indian household."""

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a budget advisor."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# ==================== CALCULATOR FUNCTIONS ====================
def calc_click(val):
    if st.session_state.calc_new:
        st.session_state.calc_display = val
        st.session_state.calc_new = False
    else:
        if st.session_state.calc_display == '0':
            st.session_state.calc_display = val
        else:
            st.session_state.calc_display += val

def calc_op(op):
    st.session_state.calc_first = float(st.session_state.calc_display.replace(',', ''))
    st.session_state.calc_operator = op
    st.session_state.calc_new = True

def calc_equals():
    if st.session_state.calc_first is not None:
        try:
            second = float(st.session_state.calc_display.replace(',', ''))
            first = st.session_state.calc_first
            op = st.session_state.calc_operator
            
            if op == '+':
                result = first + second
            elif op == '-':
                result = first - second
            elif op == '*':
                result = first * second
            elif op == '/':
                result = first / second if second != 0 else 0
            else:
                result = second
            
            st.session_state.calc_display = f"{result:,.2f}"
        except:
            st.session_state.calc_display = "Error"
        
        st.session_state.calc_first = None
        st.session_state.calc_operator = None
        st.session_state.calc_new = True

def calc_clear():
    st.session_state.calc_display = '0'
    st.session_state.calc_first = None
    st.session_state.calc_operator = None
    st.session_state.calc_new = True

# ==================== WELCOME PAGE ====================
def show_welcome():
    st.markdown("""
    <div class="welcome-box">
        <div style="font-size: 4rem;">💰</div>
        <h1 style="margin: 0.5rem 0;">Household Budget</h1>
        <p style="color: #666;">Track & Save Money Smartly</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("welcome"):
            name = st.text_input("👤 Your Name", placeholder="Enter name...")
            income = st.number_input("💵 Monthly Income (₹)", min_value=0, value=50000, step=1000)
            savings = st.number_input("🎯 Savings Goal (₹)", min_value=0, value=10000, step=500)
            
            if st.form_submit_button("🚀 Start Budgeting", use_container_width=True, type="primary"):
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
    total = get_total()
    remaining = st.session_state.income - total
    
    # Header
    hour = now.hour
    greet = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 18 else "Good Evening"
    
    st.markdown(f'<h1 class="main-title">💰 Household Budget Calculator</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="greeting">{greet}, {st.session_state.user_name}! 👋</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.user_name}")
        st.caption(f"📅 {now.strftime('%d %b %Y')}")
        
        st.markdown("---")
        
        st.markdown("### 📊 Summary")
        st.metric("Income", f"₹{st.session_state.income:,}")
        st.metric("Spent", f"₹{total:,.0f}")
        st.metric("Left", f"₹{remaining:,.0f}")
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Settings")
        
        new_income = st.number_input("Income", value=st.session_state.income, step=1000, key="s_inc")
        if new_income != st.session_state.income:
            st.session_state.income = new_income
        
        new_goal = st.number_input("Goal", value=st.session_state.savings_goal, step=500, key="s_goal")
        if new_goal != st.session_state.savings_goal:
            st.session_state.savings_goal = new_goal
        
        st.markdown("---")
        
        st.markdown("### 🤖 AI")
        api = st.text_input("API Key", value=st.session_state.api_key, type="password", key="s_api")
        st.session_state.api_key = api
        st.markdown("[Get Key](https://platform.openai.com/api-keys)")
        
        st.markdown("---")
        
        st.markdown("### 💾 Data")
        
        if st.session_state.expenses:
            data = json.dumps({
                'user': st.session_state.user_name,
                'income': st.session_state.income,
                'goal': st.session_state.savings_goal,
                'expenses': st.session_state.expenses
            }, indent=2)
            st.download_button("📥 Export", data, "budget.json", use_container_width=True)
        
        up = st.file_uploader("📤 Import", type=['json'], key="imp")
        if up:
            try:
                d = json.load(up)
                st.session_state.user_name = d.get('user', 'User')
                st.session_state.income = d.get('income', 0)
                st.session_state.savings_goal = d.get('goal', 0)
                st.session_state.expenses = d.get('expenses', [])
                st.success("✅ Loaded!")
                st.rerun()
            except:
                st.error("Invalid")
        
        st.markdown("---")
        
        if st.button("🚪 Change User", use_container_width=True):
            st.session_state.setup_done = False
            st.session_state.user_name = ''
            st.session_state.expenses = []
            st.rerun()
        
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.expenses = []
            st.rerun()
    
    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">₹{st.session_state.income:,}</div><div class="metric-label">💵 Income</div></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">₹{total:,.0f}</div><div class="metric-label">💸 Spent</div></div>', unsafe_allow_html=True)
    
    with col3:
        color = "color: #28a745;" if remaining >= 0 else "color: #dc3545;"
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="{color}">₹{remaining:,.0f}</div><div class="metric-label">💰 Left</div></div>', unsafe_allow_html=True)
    
    with col4:
        prog = min(100, (remaining / st.session_state.savings_goal * 100)) if st.session_state.savings_goal > 0 else 0
        icon = "✅" if remaining >= st.session_state.savings_goal else "⏳"
        st.markdown(f'<div class="metric-card"><div class="metric-value">{icon} {prog:.0f}%</div><div class="metric-label">🎯 Goal</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== PIE CHART ====================
    st.markdown('<div class="section-title">📊 Spending Overview</div>', unsafe_allow_html=True)
    
    cats = get_by_category()
    
    if cats:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.pie(
                values=list(cats.values()),
                names=list(cats.keys()),
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='outside', textinfo='percent+label')
            fig.update_layout(
                height=400,
                showlegend=True,
                title=f"{st.session_state.user_name}'s Expenses"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📋 Summary")
            sorted_cats = dict(sorted(cats.items(), key=lambda x: x[1], reverse=True))
            for cat, amt in sorted_cats.items():
                pct = (amt / total * 100) if total > 0 else 0
                st.markdown(f"**{cat}**")
                st.progress(min(pct / 100, 1.0))
                st.caption(f"₹{amt:,.0f} ({pct:.1f}%)")
    else:
        st.info(f"👋 Hi {st.session_state.user_name}! Add expenses to see the chart.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==================== TABS ====================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add Expense",
        "📋 Expense List",
        "🧮 Calculator",
        "🤖 AI Advisor",
        "📈 Reports"
    ])
    
    # TAB 1: ADD EXPENSE
    with tab1:
        st.markdown('<div class="section-title">➕ Add Expense</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.form("add_exp", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    cat = st.selectbox("Category", list(CATEGORIES.keys()))
                with c2:
                    subcat = st.selectbox("Item", CATEGORIES[cat])
                
                c3, c4 = st.columns(2)
                with c3:
                    amt = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
                with c4:
                    date = st.date_input("Date", datetime.now())
                
                note = st.text_input("Note (optional)")
                
                if st.form_submit_button("💾 Add", type="primary", use_container_width=True):
                    if amt > 0:
                        add_expense(cat, subcat, amt, date, note)
                        st.success(f"✅ Added: {subcat} - ₹{amt:,.0f}")
                        st.rerun()
                    else:
                        st.error("Enter amount > 0")
        
        with col2:
            st.markdown("### 💡 Prices")
            st.info("""
            🥛 Milk: ₹25-60/L
            🍞 Bread: ₹30-50
            🥚 Eggs: ₹6-8/pc
            ⚡ Electric: ₹500-3000
            📱 Phone: ₹199-999
            ⛽ Petrol: ₹100/L
            """)
    
    # TAB 2: EXPENSE LIST
    with tab2:
        st.markdown('<div class="section-title">📋 Expenses</div>', unsafe_allow_html=True)
        
        if not st.session_state.expenses:
            st.info("No expenses yet")
        else:
            df = pd.DataFrame(st.session_state.expenses)
            df['date'] = pd.to_datetime(df['date'])
            
            c1, c2 = st.columns(2)
            with c1:
                filt_cat = st.selectbox("Category", ["All"] + list(CATEGORIES.keys()), key="filt")
            with c2:
                sort_opt = st.selectbox("Sort", ["Date ↓", "Date ↑", "Amount ↓", "Amount ↑"])
            
            filt = df.copy()
            if filt_cat != "All":
                filt = filt[filt['category'] == filt_cat]
            
            if sort_opt == "Date ↓":
                filt = filt.sort_values('date', ascending=False)
            elif sort_opt == "Date ↑":
                filt = filt.sort_values('date', ascending=True)
            elif sort_opt == "Amount ↓":
                filt = filt.sort_values('amount', ascending=False)
            else:
                filt = filt.sort_values('amount', ascending=True)
            
            st.caption(f"Showing {len(filt)} of {len(df)}")
            
            disp = filt.copy()
            disp['date'] = disp['date'].dt.strftime('%d %b %Y')
            disp['amount'] = disp['amount'].apply(lambda x: f"₹{x:,.0f}")
            disp = disp[['date', 'category', 'subcategory', 'amount', 'note']]
            disp.columns = ['Date', 'Category', 'Item', 'Amount', 'Note']
            
            st.dataframe(disp, use_container_width=True, hide_index=True)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total", f"₹{filt['amount'].sum():,.0f}")
            with c2:
                st.metric("Count", len(filt))
            with c3:
                avg = filt['amount'].mean() if len(filt) > 0 else 0
                st.metric("Avg", f"₹{avg:,.0f}")
    
    # TAB 3: CALCULATOR
    with tab3:
        st.markdown('<div class="section-title">🧮 Calculator</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display
            st.markdown(f'<div class="calc-display">{st.session_state.calc_display}</div>', unsafe_allow_html=True)
            
            # Buttons
            r1 = st.columns(4)
            r2 = st.columns(4)
            r3 = st.columns(4)
            r4 = st.columns(4)
            r5 = st.columns(4)
            
            # Row 1
            with r1[0]:
                if st.button("C", use_container_width=True):
                    calc_clear()
                    st.rerun()
            with r1[1]:
                if st.button("±", use_container_width=True):
                    try:
                        val = float(st.session_state.calc_display.replace(',', ''))
                        st.session_state.calc_display = f"{-val:,.2f}"
                        st.rerun()
                    except:
                        pass
            with r1[2]:
                if st.button("%", use_container_width=True):
                    try:
                        val = float(st.session_state.calc_display.replace(',', ''))
                        st.session_state.calc_display = f"{val/100:,.4f}"
                        st.rerun()
                    except:
                        pass
            with r1[3]:
                if st.button("÷", use_container_width=True):
                    calc_op('/')
                    st.rerun()
            
            # Row 2
            with r2[0]:
                if st.button("7", use_container_width=True):
                    calc_click('7')
                    st.rerun()
            with r2[1]:
                if st.button("8", use_container_width=True):
                    calc_click('8')
                    st.rerun()
            with r2[2]:
                if st.button("9", use_container_width=True):
                    calc_click('9')
                    st.rerun()
            with r2[3]:
                if st.button("×", use_container_width=True):
                    calc_op('*')
                    st.rerun()
            
            # Row 3
            with r3[0]:
                if st.button("4", use_container_width=True):
                    calc_click('4')
                    st.rerun()
            with r3[1]:
                if st.button("5", use_container_width
