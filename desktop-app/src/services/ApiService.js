// desktop-app/src/services/ApiService.js

const API_BASE_URL = 'http://127.0.0.1:5000';

/**
 * @param {string} 
 * @returns {Promise<object>} 
 */
export const sendCommandToBackend = async (command) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/process-command`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ command: command }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    return responseData;

  } catch (error) {
    console.error("Gagal berkomunikasi dengan backend:", error);
    return {
      status: 'error',
      message: 'Tidak dapat terhubung ke server AI. Pastikan backend sudah berjalan.',
    };
  }
};
