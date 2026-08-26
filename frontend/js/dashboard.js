function calculateRemainingTime(expiryDateStr) {
    const expiry = new Date(expiryDateStr.replace(' ', 'T')); // Handle sqlite format
    const now = new Date();
    const diffMs = expiry - now;
    
    if (diffMs <= 0) return "Expired";
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffDays > 0) return `${diffDays} days, ${diffHours} hrs`;
    if (diffHours > 0) return `${diffHours} hrs, ${diffMins} mins`;
    return `${diffMins} mins`;
}

function getStatusBadge(status) {
    if (status === 'EXPIRED') return `<span class="badge status-expired">EXPIRED</span>`;
    if (status === 'CRITICAL') return `<span class="badge status-critical">CRITICAL</span>`;
    if (status === 'WARNING') return `<span class="badge status-warning">WARNING</span>`;
    if (status === 'SAFE') return `<span class="badge status-safe">SAFE</span>`;
    return `<span class="badge">${status || 'UNKNOWN'}</span>`;
}

async function loadDashboard() {
    const errorMsg = document.getElementById('error-msg');
    try {
        // Load Stats
        const statsRes = await fetch('/api/stats');
        if (!statsRes.ok) throw new Error("API Error");
        const stats = await statsRes.json();
        
        document.getElementById('stat-products').textContent = stats.total_products || '0';
        document.getElementById('stat-stock').textContent = stats.total_stock || '0';
        document.getElementById('stat-near').textContent = stats.near_expiry || '0';
        document.getElementById('stat-critical').textContent = stats.critical || '0';
        document.getElementById('stat-expired').textContent = stats.expired || '0';
        
        // Load Near Expiry Table (limit 5 for dashboard)
        const nearRes = await fetch('/api/near-expiry');
        const nearItems = await nearRes.json();
        
        const tbody = document.getElementById('near-expiry-tbody');
        tbody.innerHTML = '';
        
        if (nearItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No data available</td></tr>';
        } else {
            nearItems.slice(0, 5).forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${item.product_name}</td>
                    <td>${item.category}</td>
                    <td>${item.stock_quantity}</td>
                    <td>${item.expiry_date}</td>
                    <td>${calculateRemainingTime(item.expiry_date)}</td>
                    <td>${getStatusBadge(item.status)}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error(error);
        errorMsg.textContent = "Unable to connect to the backend.";
        errorMsg.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', loadDashboard);
