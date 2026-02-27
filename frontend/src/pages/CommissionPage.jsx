import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import OccurrenceLogger from '../components/OccurrenceLogger';
import CommissionCalculator from '../components/CommissionCalculator';
import { Alert, AlertDescription } from '../components/ui/alert';
import { AlertTriangle } from 'lucide-react';

/**
 * Página de Gerenciamento de Comissões (Novo Sistema)
 * Válido a partir do próximo mês
 */
export const CommissionPage = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleOccurrenceLogged = () => {
    // Atualizar dados quando uma ocorrência for lançada
    setRefreshKey((prev) => prev + 1);
  };

  const handleCommissionPosted = () => {
    // Atualizar dados quando uma comissão for lançada
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Cabeçalho */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">🎯 Sistema de Comissões (Novo)</h1>
          <p className="text-gray-600">
            Gerenciamento de comissões por valor entregue com sistema de ocorrências
          </p>
        </div>

        {/* Alerta de Aviso */}
        <Alert className="mb-6 border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            <strong>⚠️ ATENÇÃO:</strong> Este novo sistema de comissão será implementado
            apenas a partir do próximo mês. O sistema antigo por nota continua ativo no
            momento.
          </AlertDescription>
        </Alert>

        {/* Grid de Componentes */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Coluna 1: Lançar Ocorrências */}
          <div key={`occurrence-${refreshKey}`}>
            <OccurrenceLogger onOccurrenceLogged={handleOccurrenceLogged} />
          </div>

          {/* Coluna 2: Calcular Comissão */}
          <div key={`commission-${refreshKey}`}>
            <CommissionCalculator onCommissionPosted={handleCommissionPosted} />
          </div>
        </div>

        {/* Cards Informativos */}
        <div className="grid md:grid-cols-3 gap-4">
          {/* Como Funciona */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">📋 Como Funciona</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-700 space-y-2">
              <p>
                <strong>1. Lançar Ocorrências:</strong> Registre atrasos, danos ou
                problemas usando o número da nota.
              </p>
              <p>
                <strong>2. Calcular Base:</strong> 1% do valor de mercadorias entregue
                no mês.
              </p>
              <p>
                <strong>3. Ajuste Final:</strong> O percentual varia conforme ocorrências
                do funcionário.
              </p>
            </CardContent>
          </Card>

          {/* Percentuais */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">📊 Percentuais</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <div className="flex justify-between items-center pb-2 border-b">
                <span>🟢 Menos ocorrências:</span>
                <strong className="text-green-600">1.0%</strong>
              </div>
              <div className="flex justify-between items-center pb-2 border-b">
                <span>🟡 Ocorrências medianas:</span>
                <strong className="text-yellow-600">0.9%</strong>
              </div>
              <div className="flex justify-between items-center">
                <span>🔴 Mais ocorrências:</span>
                <strong className="text-red-600">0.8%</strong>
              </div>
            </CardContent>
          </Card>

          {/* Notificações */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">🔔 Notificações</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-gray-700 space-y-2">
              <p>
                ✅ Quando uma comissão for lançada, o funcionário será notificado em
                tempo real.
              </p>
              <p>
                📱 Notificações aparecem em:
                <ul className="list-disc list-inside mt-1">
                  <li>Web</li>
                  <li>Windows (EXE)</li>
                  <li>Android (APK)</li>
                </ul>
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Notas Importantes */}
        <Card className="mt-6 border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-lg text-blue-900">ℹ️ Notas Importantes</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-blue-800 space-y-2">
            <p>
              • Este sistema foi desenvolvido parasubstituir o antigo sistema por nota
            </p>
            <p>• Será ativado apenas a partir do próximo mês (data: TBD)</p>
            <p>• Agora o cálculo é feito automaticamente baseado em ocorrências</p>
            <p>• Todos os dados são sincronizados entre Web, Windows e Android</p>
            <p>
              • O sistema antigo continuará disponível até a migração completa
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CommissionPage;
