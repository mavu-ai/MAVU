const API_BASE_URL = 'https://api.mavu.app';

export const paymeApi = {
  async initPayment(amount = 1100) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/payme/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          amount: amount * 100,
          return_url: `${window.location.origin}/payment-result`,
        }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to initialize payment');
      }

      return await response.json();
    } catch (error) {
      console.error('Payment init error:', error);
      throw error;
    }
  },

  async getTransactionStatus(transactionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/payme/status/${transactionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get transaction status');
      }

      return await response.json();
    } catch (error) {
      console.error('Transaction status error:', error);
      throw error;
    }
  },
};

export default paymeApi;
