import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { toast } from 'sonner';
import commissionService from '../services/commissionService';

/**
 * Componente Simples de Comissão
 * Interface minimalista: preenche 3 campos e lança
 */
export const CommissionCalculator = ({ onCommissionPosted }) => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    employeeId: '',
    employeeName: '',
    totalDeliveredValue: '',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleLaunch = async (e) => {
    e.preventDefault();

    // Validação simples
    if (!formData.employeeId.trim()) {
      toast.error('❌ Preencha o ID');
      return;
    }
    if (!formData.employeeName.trim()) {
      toast.error('❌ Preencha o Nome');
      return;
    }
    if (!formData.totalDeliveredValue || parseFloat(formData.totalDeliveredValue) <= 0) {
      toast.error('❌ Preencha o Valor corretamente');
      return;
    }

    setLoading(true);

    try {
      // Calcula comissão
      const calculation = await commissionService.calculateCommission({
        employee_id: formData.employeeId,
        total_delivered_value: parseFloat(formData.totalDeliveredValue),
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
      });

      // Lança comissão
      await commissionService.postCommission({
        employee_id: formData.employeeId,
        employee_name: formData.employeeName,
        month: new Date().getMonth() + 1,
        year: new Date().getFullYear(),
        total_delivered_value: parseFloat(formData.totalDeliveredValue),
        percentage: calculation.percentage,
        commission_amount: calculation.commission_amount,
        occurrence_count: calculation.occurrence_count,
        tier: calculation.tier,
      });

      // Sucesso
      toast.success(`✅ Comissão de R$ ${calculation.commission_amount?.toFixed(2)} lançada!`);
      
      // Limpa formulário
      setFormData({
        employeeId: '',
        employeeName: '',
        totalDeliveredValue: '',
      });

      onCommissionPosted?.();
    } catch (err) {
      toast.error('❌ Erro: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="bg-blue-600 text-white">
        <CardTitle>💰 Lançar Comissão</CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <form onSubmit={handleLaunch} className="space-y-4">
          <div>
            <Label className="text-sm font-medium">ID do Funcionário</Label>
            <Input
              name="employeeId"
              placeholder="ex: 507f1f77bcf86cd799439011"
              value={formData.employeeId}
              onChange={handleInputChange}
              disabled={loading}
            />
          </div>

          <div>
            <Label className="text-sm font-medium">Nome do Funcionário</Label>
            <Input
              name="employeeName"
              placeholder="ex: João Silva"
              value={formData.employeeName}
              onChange={handleInputChange}
              disabled={loading}
            />
          </div>

          <div>
            <Label className="text-sm font-medium">Valor Entregue (R$)</Label>
            <Input
              name="totalDeliveredValue"
              type="number"
              placeholder="ex: 10500"
              step="0.01"
              min="0"
              value={formData.totalDeliveredValue}
              onChange={handleInputChange}
              disabled={loading}
            />
          </div>

          <Button 
            type="submit" 
            disabled={loading}
            className="w-full bg-green-600 hover:bg-green-700 h-10"
          >
            {loading ? '⏳ Lançando...' : '✅ LANÇAR'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default CommissionCalculator;
