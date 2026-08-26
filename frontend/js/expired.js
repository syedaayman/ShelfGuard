function calculateTimeSinceExpiry(expiryDateStr) {
    const expiry = new Date(expiryDateStr.replace(' ', 'T')); 
    const now = new Date();
    const diffMs = now - expiry;
    
    if (diffMs <= 0) return "Just now";
    
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffDays > 0) return `${diffDays} days, ${diffHours} hrs ago`;
    if (diffHours > 0) return `${diffHours} hrs, ${diffMins} mins ago`;
    return `${diffMins} mins ago`;
}

function getStatusBadge(status) {
    if (status === 'EXPIRED') return `<span class="badge status-expired">EXPIRED</span>`;
    if (status === 'CRITICAL') return `<span class="badge status-critical">CRITICAL</span>`;
    if (status === 'WARNING') return `<span class="badge status-warning">WARNING</span>`;
    if (status === 'SAFE') return `<span class="badge status-safe">SAFE</span>`;
    return `<span class="badge">${status || 'UNKNOWN'}</span>`;
}

async function loadExpired() {
    const errorMsg = document.getElementById('error-msg');
    try {
        const res = await fetch('/api/expired');
        if (!res.ok) throw new Error("API Error");
        const items = await res.json();
        
        const tbody = document.getElementById('expired-tbody');
        tbody.innerHTML = '';
        
        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No expired products</td></tr>';
            return;
        }
        
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.product_name} <br><small class="text-secondary">Batch: ${item.batch_id} | Cat: ${item.category}</small></td>
                <td>${item.expiry_date}</td>
                <td><span style="color: #dc3545; font-weight: 500;">${calculateTimeSinceExpiry(item.expiry_date)}</span></td>
                <td>${item.stock_quantity}</td>
                <td>${(item.current_discount * 100).toFixed(0)}%</td>
                <td>${getStatusBadge(item.status)}</td>
                <td><button class="btn btn-secondary" onclick="discardProduct('${item.batch_id}')">Discard</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error(error);
        errorMsg.textContent = "Unable to load expired data.";
        errorMsg.style.display = 'block';
    }
}

function discardProduct(batchId) {
    alert(`Discard product action triggered for batch: ${batchId}\n\n(Note: This is a frontend placeholder. Backend logic will be added in a future task.)`);
}

document.addEventListener('DOMContentLoaded', loadExpired);
