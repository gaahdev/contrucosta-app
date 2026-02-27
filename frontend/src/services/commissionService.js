/**
 * Serviço de Cálculo de Comissões por Valor Entregue
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const commissionService = {
  /**
   * Lança uma ocorrência para um motorista/ajudante
   */
  async logOccurrence(data) {
    const response = await fetch(`${BACKEND_URL}/api/occurrences`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        employee_id: data.employee_id,
        employee_name: data.employee_name,
        occurrence_type: data.occurrence_type,
        description: data.description,
      }),
    });

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.detail || 'Erro ao lançar ocorrência');
    }
    return responseData;
  },

  /**
   * Calcula a comissão baseada no valor entregue e ocorrências
   */
  async calculateCommission(data) {
    const response = await fetch(`${BACKEND_URL}/api/commission/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        employee_id: data.employee_id,
        total_delivered_value: data.total_delivered_value,
        month: data.month,
        year: data.year,
      }),
    });

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.detail || 'Erro ao calcular comissão');
    }
    return responseData;
  },

  /**
   * Obtém todas as ocorrências de um mês
   */
  async getOccurrences(month, year) {
    const response = await fetch(
      `${BACKEND_URL}/api/occurrences?month=${month}&year=${year}`
    );

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error('Erro ao obter ocorrências');
    }
    return responseData;
  },

  /**
   * Obtém ocorrências de um employee específico
   */
  async getEmployeeOccurrences(employeeId, month, year) {
    const response = await fetch(
      `${BACKEND_URL}/api/occurrences/employee/${employeeId}?month=${month}&year=${year}`
    );

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error('Erro ao obter ocorrências do funcionário');
    }
    return responseData;
  },

  /**
   * Lança uma comissão
   */
  async postCommission(data) {
    const response = await fetch(`${BACKEND_URL}/api/commission/post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        employee_id: data.employee_id,
        employee_name: data.employee_name,
        total_delivered_value: data.total_delivered_value,
        percentage: data.percentage,
        commission_amount: data.commission_amount,
        month: data.month,
        year: data.year,
        occurrence_count: data.occurrence_count,
        tier: data.tier,
      }),
    });

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error(responseData.detail || 'Erro ao lançar comissão');
    }
    return responseData;
  },

  /**
   * Obtém histórico de comissões
   */
  async getCommissions(month, year) {
    const response = await fetch(
      `${BACKEND_URL}/api/commission/history?month=${month}&year=${year}`
    );

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error('Erro ao obter histórico');
    }
    return responseData;
  },

  /**
   * Obtém estatísticas
   */
  async getStatistics(month, year) {
    const response = await fetch(
      `${BACKEND_URL}/api/commission/statistics?month=${month}&year=${year}`
    );

    const responseData = await response.json();
    if (!response.ok) {
      throw new Error('Erro ao obter estatísticas');
    }
    return responseData;
  },
};

export default commissionService;
