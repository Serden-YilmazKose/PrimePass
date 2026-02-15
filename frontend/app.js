let currentUser = null;

// Helper to get token from localStorage
function getToken() {
    return localStorage.getItem('token');
}

function setAuthHeader() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Show message (reuse the existing message div)
function showMessage(text, isError = false) {
    const msgDiv = document.getElementById('message');
    msgDiv.textContent = text;
    msgDiv.style.color = isError ? 'red' : 'green';
    setTimeout(() => {
        msgDiv.textContent = '';
        msgDiv.style.color = ''; // reset
    }, 5000);
}

// UI update after login
function updateAuthUI() {
    const token = getToken();
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            document.getElementById('displayUsername').textContent = payload.username;
            document.getElementById('auth').querySelector('input,button').style.display = 'none';
            document.getElementById('userInfo').style.display = 'block';
            currentUser = payload;
            loadRecommendations();
        } catch (e) {
            logout();
        }
    } else {
        document.getElementById('auth').querySelector('input,button').style.display = 'inline-block';
        document.getElementById('userInfo').style.display = 'none';
        document.getElementById('recommendations').style.display = 'none';
        currentUser = null;
    }
}

// Login
document.getElementById('loginBtn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
        const response = await fetch('/api/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.token);
            updateAuthUI();
            loadEvents();
        } else {
            document.getElementById('authMessage').textContent = data.error || 'Login failed';
        }
    } catch (error) {
        document.getElementById('authMessage').textContent = 'Network error. Please try again.';
    }
});

// Register
document.getElementById('registerBtn').addEventListener('click', async () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
        const response = await fetch('/api/users/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.token);
            updateAuthUI();
            loadEvents();
        } else {
            document.getElementById('authMessage').textContent = data.error || 'Registration failed';
        }
    } catch (error) {
        document.getElementById('authMessage').textContent = 'Network error. Please try again.';
    }
});

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
    logout();
});

function logout() {
    localStorage.removeItem('token');
    updateAuthUI();
    loadEvents();
}

// Load events with error handling
async function loadEvents() {
    const container = document.getElementById('events');
    container.innerHTML = '<p>Loading events...</p>'; // Show loading indicator

    try {
        const response = await fetch('/api/events');
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        const events = await response.json();
        container.innerHTML = ''; // Clear loading message

        if (events.length === 0) {
            container.innerHTML = '<p>No events available at the moment.</p>';
            return;
        }

        events.forEach(event => {
            const div = document.createElement('div');
            div.className = 'event';

            let actionHtml = '';
            if (currentUser) {
                actionHtml = `
                    <input type="number" min="1" value="1" id="qty-${event.id}">
                    <button data-event-id="${event.id}" class="reserve-btn">
                        Reserve
                    </button>
                `;
            } else {
                actionHtml = '<p><em>Login to reserve tickets</em></p>';
            }

            div.innerHTML = `
                <div class="event-title">${event.name}</div>
                <div class="event-info">
                    Date: ${event.date}<br>
                    Tickets left: ${event.available}
                </div>
                ${actionHtml}
            `;

            container.appendChild(div);
        });

        attachReserveHandlers();
    } catch (error) {
        console.error('Failed to load events:', error);
        container.innerHTML = '<p style="color: red;">Failed to load events. Please refresh the page or try again later.</p>';
        showMessage('Error loading events. Check your connection.', true);
    }
}

// Attach reserve button handlers
function attachReserveHandlers() {
    document.querySelectorAll('.reserve-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const eventId = button.getAttribute('data-event-id');
            const qtyInput = document.getElementById(`qty-${eventId}`);
            const quantity = parseInt(qtyInput.value, 10);

            try {
                // Reserve tickets
                const reserveResponse = await fetch(`/api/events/${eventId}/reserve`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...setAuthHeader()
                    },
                    body: JSON.stringify({ quantity })
                });

                const reserveResult = await reserveResponse.json();
                if (!reserveResponse.ok) {
                    showMessage(reserveResult.error || 'Reservation failed', true);
                    return;
                }

                // Purchase (confirm reservation)
                const purchaseResponse = await fetch('/api/events/purchase', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...setAuthHeader()
                    },
                    body: JSON.stringify({
                        reservation_id: reserveResult.reservation_id,
                        payment_token: 'mock'
                    })
                });

                const purchaseResult = await purchaseResponse.json();
                if (purchaseResponse.ok) {
                    showMessage('Purchase successful!');
                    loadEvents(); // refresh availability
                } else {
                    showMessage(purchaseResult.error || 'Purchase failed', true);
                }
            } catch (error) {
                console.error('Purchase error:', error);
                showMessage('Network error during purchase. Please try again.', true);
            }
        });
    });
}

// Load recommendations
async function loadRecommendations() {
    if (!currentUser) return;
    try {
        const response = await fetch(`/api/recommendations?user_id=${currentUser.user_id}`);
        if (response.ok) {
            const recIds = await response.json();
            if (recIds.length > 0) {
                // Fetch details for these events (could be cached)
                const eventsRes = await fetch('/api/events');
                if (eventsRes.ok) {
                    const allEvents = await eventsRes.json();
                    const recEvents = allEvents.filter(e => recIds.includes(e.id));
                    displayRecommendations(recEvents);
                } else {
                    document.getElementById('recommendations').style.display = 'none';
                }
            } else {
                document.getElementById('recommendations').style.display = 'none';
            }
        } else {
            document.getElementById('recommendations').style.display = 'none';
        }
    } catch (e) {
        console.warn('Recommendations unavailable:', e);
        document.getElementById('recommendations').style.display = 'none';
    }
}

function displayRecommendations(events) {
    const recDiv = document.getElementById('recList');
    recDiv.innerHTML = '';
    events.forEach(event => {
        const span = document.createElement('span');
        span.className = 'rec-item';
        span.textContent = event.name;
        recDiv.appendChild(span);
    });
    document.getElementById('recommendations').style.display = 'block';
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    loadEvents();
});