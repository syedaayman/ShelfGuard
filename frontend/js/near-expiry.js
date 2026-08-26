function calculateRemainingTime(expiryDateStr) {
    const expiry = new Date(expiryDateStr.replace(' ', 'T')); 
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

async function loadNearExpiry() {
    const errorMsg = document.getElementById('error-msg');
    try {
        const res = await fetch('/api/near-expiry');
        if (!res.ok) throw new Error("API Error");
        const items = await res.json();
        
        const tbody = document.getElementById('near-expiry-tbody');
        tbody.innerHTML = '';
        
        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
            return;
        }
        
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.product_name} <br><small class="text-secondary">${item.batch_id}</small></td>
                <td>${item.expiry_date}</td>
                <td>${calculateRemainingTime(item.expiry_date)}</td>
                <td>${item.stock_quantity}</td>
                <td>${(item.current_discount * 100).toFixed(0)}%</td>
                <td>${getStatusBadge(item.status)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error(error);
        errorMsg.textContent = "Unable to load near-expiry data.";
        errorMsg.style.display = 'block';
    }
}

document.addEventListener('DOMContentLoaded', loadNearExpiry);
