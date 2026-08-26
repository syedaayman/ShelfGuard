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

async function loadDonations() {
    const errorMsg = document.getElementById('error-msg');
    try {
        const res = await fetch('/api/donations');
        if (!res.ok) throw new Error("API Error");
        const items = await res.json();
        
        const tbody = document.getElementById('donations-tbody');
        tbody.innerHTML = '';
        
        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
            return;
        }
        
        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <strong>${item.product_name}</strong><br>
                    <small class="text-secondary">Batch: ${item.batch_id} | Cat: ${item.category}</small>
                </td>
                <td>${calculateRemainingTime(item.expiry_date)}<br><small class="text-secondary">${item.expiry_date}</small></td>
                <td>${item.stock_quantity} units</td>
                <td>${getStatusBadge(item.status)}</td>
                <td>
                    <button class="btn btn-success" onclick="approveDonation('${item.batch_id}')">Approve Donation</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error(error);
        errorMsg.textContent = "Unable to load donation data.";
        errorMsg.style.display = 'block';
    }
}

function approveDonation(batchId) {
    alert(`Donation approved for batch: ${batchId}\n\n(Note: This is a frontend placeholder. Backend logic will be added in a future task.)`);
}

document.addEventListener('DOMContentLoaded', loadDonations);
