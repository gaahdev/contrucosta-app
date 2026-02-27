import React, { useState } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { AlertCircle } from 'lucide-react';
import commissionService from '../services/commissionService';

/**
 * Componente para lançar ocorrências
 * Sistema novo: A partir do próximo mês
 */
export const OccurrenceLogger = ({ onOccurrenceLogged }) => {
  const [formData, setFormData] = useState({
    noteNumber: '',
    employeeId: '',
    employeeType: 'driver', // 'driver' ou 'helper'
    occurrenceType: 'delay', // 'delay', 'damage', 'other'
    description: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await commissionService.logOccurrence(formData);
      setSuccess(true);
      setFormData({
        noteNumber: '',
        employeeId: '',
        employeeType: 'driver',
        occurrenceType: 'delay',
        description: '',
      });

      // Notificar componente pai
      if (onOccurrenceLogged) {
        onOccurrenceLogged();
      }

      // Limpar mensagem de sucesso após 3 segundos
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError('Erro ao lançar ocorrência: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Lançar Ocorrência</CardTitle>
        <CardDescription>
          Sistema novo (válido a partir do próximo mês)
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Número da Nota */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Número da Nota *
            </label>
            <Input
              type="text"
              name="noteNumber"
              value={formData.noteNumber}
              onChange={handleInputChange}
              placeholder="Ex: 12345"
              required
            />
          </div>

          {/* ID do Funcionário */}
          <div>
            <label className="block text-sm font-medium mb-1">
              ID do Funcionário *
            </label>
            <Input
              type="text"
              name="employeeId"
              value={formData.employeeId}
              onChange={handleInputChange}
              placeholder="Ex: EMP001"
              required
            />
          </div>

          {/* Tipo de Funcionário */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Tipo de Funcionário *
            </label>
            <select
              name="employeeType"
              value={formData.employeeType}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="driver">Motorista</option>
              <option value="helper">Ajudante</option>
            </select>
          </div>

          {/* Tipo de Ocorrência */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Tipo de Ocorrência *
            </label>
            <select
              name="occurrenceType"
              value={formData.occurrenceType}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="delay">Atraso na Entrega</option>
              <option value="damage">Dano em Mercadoria</option>
              <option value="other">Outro</option>
            </select>
          </div>

          {/* Descrição */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Descrição
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Descreva a ocorrência..."
              className="w-full px-3 py-2 border rounded-md"
              rows="3"
            />
          </div>

          {/* Mensagens */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-100 text-red-800 rounded-md">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 bg-green-100 text-green-800 rounded-md">
              ✅ Ocorrência lançada com sucesso!
            </div>
          )}

          {/* Botão Submit */}
          <Button
            type="submit"
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Processando...' : 'Lançar Ocorrência'}
          </Button>
        </form>

        {/* Info Box */}
        <div className="mt-4 p-3 bg-blue-50 rounded-md text-sm">
          <p className="font-semibold mb-2">📊 Sistema de Comissão (Novo):</p>
          <ul className="space-y-1 text-xs">
            <li>• Base: 1% do valor entregue no mês</li>
            <li>• Mais ocorrências: 0.8%</li>
            <li>• Ocorrências medianas: 0.9%</li>
            <li>• Menos ocorrências: 1%</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default OccurrenceLogger;
