function getStatusBadge(status) {
    if (status === 'EXPIRED') return `<span class="badge status-expired">EXPIRED</span>`;
    if (status === 'CRITICAL') return `<span class="badge status-critical">CRITICAL</span>`;
    if (status === 'WARNING') return `<span class="badge status-warning">WARNING</span>`;
    if (status === 'SAFE') return `<span class="badge status-safe">SAFE</span>`;
    return `<span class="badge">${status || 'UNKNOWN'}</span>`;
}

let allInventory = [];

async function loadInventory() {
    const errorMsg = document.getElementById('error-msg');
    try {
        const res = await fetch('/api/inventory');
        if (!res.ok) throw new Error("API Error");
        allInventory = await res.json();
        
        renderTable(allInventory);
    } catch (error) {
        console.error(error);
        errorMsg.textContent = "Unable to load inventory data.";
        errorMsg.style.display = 'block';
    }
}

function renderTable(data) {
    const tbody = document.getElementById('inventory-tbody');
    tbody.innerHTML = '';
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9">No data available</td></tr>';
        return;
    }
    
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.batch_id}</td>
            <td>${item.product_name}</td>
            <td>${item.category}</td>
            <td>${item.stock_quantity}</td>
            <td>$${item.current_price.toFixed(2)}</td>
            <td>${(item.current_discount * 100).toFixed(0)}%</td>
            <td>${(item.demand_score * 10).toFixed(1)}/10</td>
            <td>${item.expiry_date}</td>
            <td>${getStatusBadge(item.status)}</td>
        `;
        tbody.appendChild(tr);
    });
}

document.getElementById('search-bar').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allInventory.filter(item => 
        item.product_name.toLowerCase().includes(term) || 
        item.category.toLowerCase().includes(term)
    );
    renderTable(filtered);
});

document.addEventListener('DOMContentLoaded', loadInventory);
