from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import numpy as np
from collections import defaultdict
import re

app = Flask(__name__)
CORS(app)

def categorize_expense(description):
    """Categorize expenses based on keywords in the description."""
    categories = {
        'groceries': ['grocery', 'food', 'supermarket', 'walmart', 'target', 'costco', 'trader', 'whole foods'],
        'transportation': ['gas', 'uber', 'lyft', 'train', 'bus', 'metro', 'parking', 'fuel'],
        'utilities': ['electricity', 'water', 'internet', 'phone', 'utility', 'gas bill', 'power'],
        'entertainment': ['movie', 'game', 'netflix', 'spotify', 'hulu', 'disney+', 'theatre', 'concert'],
        'shopping': ['amazon', 'ebay', 'store', 'mall', 'shop', 'retail'],
        'dining': ['restaurant', 'cafe', 'coffee', 'doordash', 'grubhub', 'uber eats', 'takeout'],
        'healthcare': ['doctor', 'medicine', 'pharmacy', 'medical', 'healthcare', 'dental', 'clinic'],
        'housing': ['rent', 'mortgage', 'maintenance', 'repair', 'furniture', 'home'],
        'education': ['tuition', 'book', 'course', 'school', 'college', 'university'],
        'insurance': ['insurance', 'coverage', 'premium']
    }
    
    description = description.lower()
    for category, keywords in categories.items():
        if any(keyword in description for keyword in keywords):
            return category
    return 'other'

def analyze_transactions(df):
    """Analyze transaction data and generate insights."""
    # Convert date strings to datetime objects
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    # Calculate basic statistics
    total_expenses = df['amount'].sum()
    monthly_expenses = df.groupby('month')['amount'].sum()
    avg_monthly = monthly_expenses.mean()
    
    # Calculate category totals
    category_totals = df.groupby('category')['amount'].sum().to_dict()
    top_category = max(category_totals.items(), key=lambda x: x[1])[0]
    
    # Generate monthly trend data
    monthly_trend = (df.groupby('month')['amount']
                    .sum()
                    .reset_index())
    monthly_trend['month'] = monthly_trend['month'].astype(str)
    
    # Calculate category percentages
    total_spend = df['amount'].sum()
    category_percentages = {cat: (amt/total_spend)*100 
                          for cat, amt in category_totals.items()}
    
    # Generate insights
    insights = generate_insights(df, monthly_expenses, category_totals)
    
    return {
        'summary': {
            'total_expenses': round(total_expenses, 2),
            'average_monthly': round(avg_monthly, 2),
            'top_category': top_category
        },
        'monthly_trend': monthly_trend.to_dict(orient='records'),
        'category_distribution': [
            {'category': cat, 'amount': amt, 'percentage': category_percentages[cat]}
            for cat, amt in category_totals.items()
        ],
        'insights': insights
    }

def generate_insights(df, monthly_expenses, category_totals):
    """Generate meaningful insights from the transaction data."""
    insights = []
    
    # Trend analysis
    if len(monthly_expenses) > 1:
        last_month = monthly_expenses.iloc[-1]
        prev_month = monthly_expenses.iloc[-2]
        change = ((last_month - prev_month) / prev_month) * 100
        
        if abs(change) > 10:
            direction = "increased" if change > 0 else "decreased"
            insights.append(
                f"Your spending has {direction} by {abs(change):.1f}% compared to last month."
            )
    
    # Category analysis
    total_spend = sum(category_totals.values())
    for category, amount in category_totals.items():
        percentage = (amount / total_spend) * 100
        if percentage > 30:
            insights.append(
                f"Your {category} expenses make up {percentage:.1f}% of your total spending. "
                "Consider if this aligns with your budget goals."
            )
    
    # Detect unusual transactions
    mean_transaction = df['amount'].mean()
    std_transaction = df['amount'].std()
    unusual_transactions = df[df['amount'] > (mean_transaction + 2*std_transaction)]
    
    if not unusual_transactions.empty:
        insights.append(
            f"Found {len(unusual_transactions)} unusually large transactions. "
            "Review these for accuracy."
        )
    
    # Monthly pattern analysis
    if len(monthly_expenses) >= 3:
        three_month_avg = monthly_expenses.tail(3).mean()
        if monthly_expenses.iloc[-1] > three_month_avg * 1.2:
            insights.append(
                "Your latest month's spending was significantly higher than your 3-month average."
            )
    
    return insights

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Handle file upload and return analysis results."""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # Read CSV file
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = {'date', 'amount', 'description'}
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV must contain date, amount, and description columns'}), 400
        
        # Clean and preprocess data
        df['category'] = df['description'].apply(categorize_expense)
        
        # Perform analysis
        analysis_results = analyze_transactions(df)
        
        return jsonify(analysis_results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True)