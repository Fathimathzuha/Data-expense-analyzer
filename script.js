/* script.js */
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const csvFile = document.getElementById('csvFile');
    const loadingOverlay = document.getElementById('loadingOverlay');
    let trendChart = null;
    let categoryChart = null;

    // File Upload Handling
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'text/csv') {
            processFile(file);
        } else {
            showNotification('Please upload a CSV file', 'error');
        }
    });

    csvFile.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) processFile(file);
    });

    function processFile(file) {
        showLoading(true);
        const reader = new FileReader();

        reader.onload = function(e) {
            const text = e.target.result;
            const transactions = parseCSV(text);
            updateDashboard(transactions);
            showLoading(false);
            showNotification('Data processed successfully!', 'success');
        };

        reader.onerror = function() {
            showLoading(false);
            showNotification('Error reading file', 'error');
        };

        reader.readAsText(file);
    }

    function parseCSV(csv) {
        const lines = csv.split('\n');
        const transactions = [];
        
        for(let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if(line) {
                const [date, amount, description] = line.split(',');
                transactions.push({
                    date: new Date(date),
                    amount: parseFloat(amount),
                    description: description,
                    category: categorizeExpense(description)
                });
            }
        }
        return transactions;
    }

    function categorizeExpense(description) {
        const categories = {
            'groceries': ['grocery', 'food', 'supermarket'],
            'transportation': ['gas', 'uber', 'lyft', 'train', 'bus'],
            'utilities': ['electricity', 'water', 'internet', 'phone'],
            'entertainment': ['movie', 'game', 'netflix', 'spotify'],
            'shopping': ['amazon', 'walmart', 'target'],
            'dining': ['restaurant', 'cafe', 'coffee'],
            'healthcare': ['doctor', 'medicine', 'pharmacy']
        };

        description = description.toLowerCase();
        for(const [category, keywords] of Object.entries(categories)) {
            if(keywords.some(keyword => description.includes(keyword))) {
                return category;
            }
        }
        return 'other';
    }

    function updateDashboard(transactions) {
        updateSummaryCards(transactions);
        updateCharts(transactions);
        generateInsights(transactions);
    }

    function updateSummaryCards(transactions) {
        const totalExpenses = transactions.reduce((sum, t) => sum + t.amount, 0);
        const monthCount = getMonthCount(transactions);
        const avgMonthly = totalExpenses / monthCount;

        const categoryTotals = transactions.reduce((acc, t) => {
            acc[t.category] = (acc[t.category] || 0) + t.amount;
            return acc;
        }, {});

        const topCategory = Object.entries(categoryTotals)
            .sort((a, b) => b[1] - a[1])[0][0];
    }
});