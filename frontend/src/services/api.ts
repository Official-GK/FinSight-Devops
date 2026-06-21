const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000';

export const api = {
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return await res.json();
    } catch (e) {
      console.error("Health check failed", e);
      return null;
    }
  },

  async getDashboardSummary() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/dashboard/summary`);
      return await res.json();
    } catch (e) {
      console.error("Dashboard summary fetch failed", e);
      return null;
    }
  },

  async getDashboardAnalytics() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/dashboard/analytics`);
      return await res.json();
    } catch (e) {
      console.error("Dashboard analytics fetch failed", e);
      return null;
    }
  },

  async analyzeTransaction(amount: number, type: string, currency: string = 'USD') {
    const res = await fetch(`${API_BASE}/api/v1/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        amount,
        transaction_type: type,
        currency,
        metadata: {
          source: 'dashboard-simulator'
        }
      }),
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      if (res.status === 422 && data.detail && Array.isArray(data.detail)) {
        throw new Error(data.detail[0].msg);
      } else if (data.detail && typeof data.detail === 'string') {
        throw new Error(data.detail);
      } else if (data.detail && data.detail.message) {
        throw new Error(data.detail.message);
      } else {
        throw new Error('Failed to analyze transaction.');
      }
    }
    
    return data;
  }
};
