// Antigravity Alpha Dashboard Controller - Pro Edition

document.addEventListener('DOMContentLoaded', () => {
    console.log('Metabolic Dashboard Initialized.');

    const marketGrid = document.getElementById('market-grid');
    const aiInsight = document.getElementById('ai-insight');
    const metabolicLog = document.getElementById('metabolic-log');
    const statusBadge = document.querySelector('.status-badge');

    const updateLog = (message) => {
        const entry = document.createElement('div');
        entry.innerHTML = `[${new Date().toLocaleTimeString()}] ${message}`;
        metabolicLog.prepend(entry);
    };

    const parseMarketReport = (report) => {
        // Simple parser for the market report string
        const lines = report.split('\n');
        const cards = [];
        lines.forEach(line => {
            if (line.startsWith('- ')) {
                const parts = line.substring(2).split(': ');
                if (parts.length === 2) {
                    const name = parts[0];
                    const priceBody = parts[1].split(' (');
                    const price = priceBody[0];
                    const change = priceBody[1] ? priceBody[1].replace(')', '') : '';
                    cards.push({ name, price, change });
                }
            }
        });
        return cards;
    };

    const renderDashboard = (data) => {
        if (!data) return;

        // Render Market Cards
        const marketCards = parseMarketReport(data.market_report);
        marketGrid.innerHTML = '';
        marketCards.forEach(card => {
            const cardEl = document.createElement('div');
            cardEl.className = 'card';
            const isPositive = card.change.includes('+');
            cardEl.innerHTML = `
                <h3>${card.name}</h3>
                <div class="price">${card.price}</div>
                <div class="change ${isPositive ? 'positive' : 'negative'}">${card.change}</div>
            `;
            marketGrid.appendChild(cardEl);
        });

        // Render AI Insight
        aiInsight.innerText = data.ai_insight || "No insight available.";

        // Update Metadata
        statusBadge.innerText = `Metabolism: Active (Entropy: ${data.entropy})`;
        updateLog(`<span style="color: #00f2ff;">PULSE: Data synced from GitHub state. Last update: ${new Date(data.last_update).toLocaleString()}</span>`);
    };

    // Fetch data from the exported JSON
    const fetchData = async () => {
        try {
            const response = await fetch('data.json?t=' + Date.now());
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            renderDashboard(data);
        } catch (error) {
            console.error('Fetch error:', error);
            updateLog('<span style="color: #ff007a;">ERROR: Failed to sync with metabolic state.</span>');
        }
    };

    fetchData();
    // Refresh every 5 minutes if left open
    setInterval(fetchData, 300000);
});
