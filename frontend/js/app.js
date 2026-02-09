// API Configuration
// Change this to your Railway backend URL after deployment
const API_BASE_URL = window.PAYGATE_API_URL || 'http://localhost:8001/api/v1';

// Auth State
let currentUser = null;
let authToken = localStorage.getItem('authToken');

// Generate unique idempotency key
function generateIdempotencyKey() {
    return 'idem_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
});

// Check Authentication
function checkAuth() {
    const token = localStorage.getItem('authToken');
    const user = localStorage.getItem('currentUser');

    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);
        updateUIForLoggedInUser();
    } else {
        updateUIForLoggedOutUser();
    }
}

// Update UI based on auth state
function updateUIForLoggedInUser() {
    const authLinks = document.getElementById('auth-links');
    const userLinks = document.getElementById('user-links');

    if (authLinks) authLinks.style.display = 'none';
    if (userLinks) {
        userLinks.style.display = 'flex';
        const userEmail = document.getElementById('nav-user-email');
        if (userEmail) userEmail.textContent = currentUser.email;
    }

    // Update dashboard if on dashboard page
    if (document.getElementById('dashboard-content')) {
        loadDashboard();
    }

    // Update admin page if on admin page
    if (document.getElementById('admin-content')) {
        if (currentUser.role === 'admin') {
            loadAdminData();
        } else {
            window.location.href = 'dashboard.html';
        }
    }
}

function updateUIForLoggedOutUser() {
    const authLinks = document.getElementById('auth-links');
    const userLinks = document.getElementById('user-links');

    if (authLinks) authLinks.style.display = 'flex';
    if (userLinks) userLinks.style.display = 'none';

    // Redirect to login if on protected page
    const protectedPages = ['dashboard.html', 'admin.html'];
    const currentPage = window.location.pathname.split('/').pop();
    if (protectedPages.includes(currentPage)) {
        window.location.href = 'index.html';
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Login Form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Register Form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }

    // Payment Form
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', handlePayment);
    }

    // Logout Button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    // Toggle Auth Forms
    const showRegister = document.getElementById('show-register');
    const showLogin = document.getElementById('show-login');

    if (showRegister) {
        showRegister.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('login-box').style.display = 'none';
            document.getElementById('register-box').style.display = 'block';
        });
    }

    if (showLogin) {
        showLogin.addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('register-box').style.display = 'none';
            document.getElementById('login-box').style.display = 'block';
        });
    }
}

// API Helper
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Handle Login
async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const alert = document.getElementById('login-alert');

    try {
        showAlert(alert, 'Logging in...', 'info');

        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        // Store auth data
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));

        showAlert(alert, 'Login successful! Redirecting...', 'success');

        setTimeout(() => {
            window.location.href = currentUser.role === 'admin' ? 'admin.html' : 'dashboard.html';
        }, 1000);

    } catch (error) {
        showAlert(alert, error.message, 'error');
    }
}

// Handle Register
async function handleRegister(e) {
    e.preventDefault();

    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const fullName = document.getElementById('register-name').value;
    const alert = document.getElementById('register-alert');

    try {
        showAlert(alert, 'Creating account...', 'info');

        await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ email, password, full_name: fullName })
        });

        showAlert(alert, 'Account created! Please login.', 'success');

        setTimeout(() => {
            document.getElementById('register-box').style.display = 'none';
            document.getElementById('login-box').style.display = 'block';
            document.getElementById('login-email').value = email;
        }, 1500);

    } catch (error) {
        showAlert(alert, error.message, 'error');
    }
}

// Handle Logout
function handleLogout(e) {
    e.preventDefault();

    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');

    window.location.href = 'index.html';
}

// Handle Payment
async function handlePayment(e) {
    e.preventDefault();

    const amount = parseInt(document.getElementById('payment-amount').value) * 100; // Convert to kobo
    const currency = document.getElementById('payment-currency').value || 'NGN';
    const alert = document.getElementById('payment-alert');

    // Generate idempotency key to prevent duplicate payments
    const idempotencyKey = generateIdempotencyKey();

    try {
        showAlert(alert, 'Initializing payment...', 'info');

        const data = await apiRequest('/payments/initialize', {
            method: 'POST',
            headers: {
                'X-Idempotency-Key': idempotencyKey
            },
            body: JSON.stringify({ amount, currency })
        });

        showAlert(alert, 'Payment initialized! Redirecting to payment page...', 'success');

        // Show modal with payment info
        showPaymentModal(data);

        // Refresh payment history after a delay
        setTimeout(() => {
            loadPaymentHistory();
        }, 2000);

    } catch (error) {
        showAlert(alert, error.message, 'error');
    }
}

// Show Payment Modal
function showPaymentModal(data) {
    const modal = document.getElementById('payment-modal');
    const modalContent = document.getElementById('modal-payment-info');

    if (modal && modalContent) {
        modalContent.innerHTML = `
            <p><strong>Reference:</strong> ${data.reference}</p>
            <p><strong>Amount:</strong> ${(data.amount / 100).toLocaleString()} ${data.currency}</p>
            <p><strong>Status:</strong> Payment Initialized</p>
            <p style="margin-top: 1rem;">
                <a href="${data.authorization_url}" target="_blank" class="btn btn-primary" style="display: inline-block; width: auto; padding: 0.8rem 2rem;">
                    Complete Payment
                </a>
            </p>
            <p style="margin-top: 1rem; font-size: 0.9rem; color: #aaa;">
                (Mock Mode: Click "Verify Payment" below to simulate successful payment)
            </p>
        `;

        // Store reference for verification
        modal.dataset.reference = data.reference;
        modal.style.display = 'flex';
    }
}

// Verify Payment
async function verifyPayment() {
    const modal = document.getElementById('payment-modal');
    const reference = modal.dataset.reference;
    const alert = document.getElementById('payment-alert');

    try {
        const data = await apiRequest(`/payments/verify/${reference}`);

        showAlert(alert, `Payment verified: ${data.payment_status}`, 'success');
        closeModal();
        loadPaymentHistory();
        loadDashboard();

    } catch (error) {
        showAlert(alert, error.message, 'error');
    }
}

// Close Modal
function closeModal() {
    const modal = document.getElementById('payment-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Load Dashboard
async function loadDashboard() {
    try {
        // Load user info
        const userInfo = document.getElementById('user-email-display');
        const userRole = document.getElementById('user-role-badge');

        if (userInfo) userInfo.textContent = currentUser.email;
        if (userRole) userRole.textContent = currentUser.role;

        // Load payment history
        await loadPaymentHistory();

    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

// Load Payment History
async function loadPaymentHistory() {
    const tableBody = document.getElementById('payments-table-body');
    const totalPayments = document.getElementById('total-payments');
    const successfulPayments = document.getElementById('successful-payments');

    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';

        const data = await apiRequest('/payments/history?limit=50');

        // Update stats
        if (totalPayments) totalPayments.textContent = data.total;
        if (successfulPayments) {
            const successful = data.payments.filter(p => p.status === 'success').length;
            successfulPayments.textContent = successful;
        }

        // Update table
        if (data.payments.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">No payments yet</td></tr>';
            return;
        }

        tableBody.innerHTML = data.payments.map(payment => `
            <tr>
                <td>${payment.reference}</td>
                <td>${(payment.amount / 100).toLocaleString()} ${payment.currency}</td>
                <td><span class="status status-${payment.status}">${payment.status}</span></td>
                <td>${new Date(payment.created_at).toLocaleString()}</td>
                <td>
                    ${payment.status === 'pending' ?
                        `<button onclick="verifyPaymentById('${payment.reference}')" class="btn btn-primary" style="width: auto; padding: 0.3rem 0.8rem; font-size: 0.8rem;">Verify</button>`
                        : '-'}
                </td>
            </tr>
        `).join('');

    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="5" class="loading">Error: ${error.message}</td></tr>`;
    }
}

// Verify payment by ID
async function verifyPaymentById(reference) {
    const alert = document.getElementById('payment-alert');

    try {
        showAlert(alert, 'Verifying payment...', 'info');

        const data = await apiRequest(`/payments/verify/${reference}`);

        showAlert(alert, `Payment ${reference}: ${data.payment_status}`, 'success');
        loadPaymentHistory();
        loadDashboard();

    } catch (error) {
        showAlert(alert, error.message, 'error');
    }
}

// Load Admin Data
async function loadAdminData() {
    await loadAdminUsers();
    await loadAdminTransactions();
}

// Load Admin Users
async function loadAdminUsers() {
    const tableBody = document.getElementById('users-table-body');
    const totalUsers = document.getElementById('total-users');

    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';

        const data = await apiRequest('/admin/users?limit=50');

        if (totalUsers) totalUsers.textContent = data.total;

        if (data.users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="5" class="loading">No users yet</td></tr>';
            return;
        }

        tableBody.innerHTML = data.users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.email}</td>
                <td>${user.full_name}</td>
                <td><span class="status status-${user.role === 'admin' ? 'success' : 'pending'}">${user.role}</span></td>
                <td>${new Date(user.created_at).toLocaleString()}</td>
            </tr>
        `).join('');

    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="5" class="loading">Error: ${error.message}</td></tr>`;
    }
}

// Load Admin Transactions
async function loadAdminTransactions() {
    const tableBody = document.getElementById('admin-transactions-table-body');
    const totalTransactions = document.getElementById('total-transactions');

    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="6" class="loading">Loading...</td></tr>';

        const data = await apiRequest('/admin/transactions?limit=50');

        if (totalTransactions) totalTransactions.textContent = data.total;

        if (data.transactions.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="loading">No transactions yet</td></tr>';
            return;
        }

        tableBody.innerHTML = data.transactions.map(txn => `
            <tr>
                <td>${txn.reference}</td>
                <td>${txn.user_email}</td>
                <td>${(txn.amount / 100).toLocaleString()} ${txn.currency}</td>
                <td><span class="status status-${txn.status}">${txn.status}</span></td>
                <td>${new Date(txn.created_at).toLocaleString()}</td>
                <td>${txn.verified_at ? new Date(txn.verified_at).toLocaleString() : '-'}</td>
            </tr>
        `).join('');

    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="6" class="loading">Error: ${error.message}</td></tr>`;
    }
}

// Show Alert
function showAlert(element, message, type) {
    if (!element) return;

    element.textContent = message;
    element.className = `alert alert-${type}`;
    element.style.display = 'block';

    if (type !== 'info') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
}
