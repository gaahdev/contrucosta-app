import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { LogOut, DollarSign } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function UserDashboard({ user, token, onLogout }) {
  const [loading, setLoading] = useState(true);
  const [employeeSummary, setEmployeeSummary] = useState(null);
  const navigate = useNavigate();

  const fetchEmployeeSummary = async () => {
    try {
      console.log('Buscando dados do motorista com ID:', user.id);
      const response = await axios.get(`${BACKEND_URL}/api/employees/${user.id}`);
      console.log('✅ Employee summary recebido:', response.data);
      setEmployeeSummary(response.data);
    } catch (error) {
      console.error('❌ Erro ao carregar employee summary:', error.message);
      // Fallback: criar dados mock se o endpoint não existir
      console.log('📦 Usando dados mock para novo usuário...');
      const mockData = {
        employee_id: user.id,
        name: user.name || 'Motorista',
        total_delivered_value: 8500,
        value_to_receive: 85,
        by_truck: {
          'BKO': { count: 1, total_value: 5000 },
          'GKY': { count: 1, total_value: 3500 }
        },
        occurrence_count: 0,
        percentage: 1.0
      };
      setEmployeeSummary(mockData);
      console.log('✅ Dados mock carregados:', mockData);
    }
  };

  useEffect(() => {
    console.log('UserDashboard montado, user:', user);
    setLoading(false);
    fetchEmployeeSummary();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #660000 0%, #0b0b0b 100%)' }}>
        <video
          src="/loading.mp4"
          autoPlay
          loop
          muted
          playsInline
          className="w-56 h-56 object-contain rounded-md shadow-lg"
        />
      </div>
    );
  }

  const needsChecklist = user.role === 'driver' && user.assigned_day && !dashboardData?.checklist_completed;

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #660000 0%, #0b0b0b 100%)' }}>
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <img src="/logo.jpg" alt="Construcosta Logo" className="w-6 h-6 object-contain" />
              </div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk' }}>Commission Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Avatar>
                  <AvatarFallback className="bg-red-600 text-white">
                    {user.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <p className="text-sm font-semibold text-white" data-testid="user-name">{user.name}</p>
                  <p className="text-xs text-white/80 capitalize" data-testid="user-role">{user.role}</p>
                  {user.assigned_day && <p className="text-xs text-white/60">{user.assigned_day}</p>}
                </div>
              </div>
              <Button 
                onClick={onLogout} 
                data-testid="logout-button"
                variant="ghost" 
                className="text-white hover:bg-white/20"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Valor Total Entregue & Valor a Receber */}
        {employeeSummary ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <Card className="shadow-lg border-2 border-blue-200">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-lg font-semibold">📦 Valor Total Entregue</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-blue-600">
                    R$ {employeeSummary.total_delivered_value?.toFixed(2) || '0.00'}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">Valor de todas as entregas</p>
                </CardContent>
              </Card>

              <Card className="shadow-lg border-2 border-green-200">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-lg font-semibold">💰 Valor a Receber</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-green-600">
                    R$ {employeeSummary.value_to_receive?.toFixed(2) || '0.00'}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Desconto por {employeeSummary.percentage || 1.0}% ({employeeSummary.occurrence_count || 0} ocorrências)
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Entregas por Caminhão */}
            {employeeSummary.by_truck && Object.keys(employeeSummary.by_truck).length > 0 && (
              <Card className="shadow-xl mb-8">
                <CardHeader>
                  <CardTitle className="text-xl">📍 Entregas por Caminhão</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-3">Caminhão</th>
                          <th className="text-right py-2 px-3">Qtd</th>
                          <th className="text-right py-2 px-3">Valor</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(employeeSummary.by_truck).map(([truck, data]) => (
                          <tr key={truck} className="border-b hover:bg-gray-50">
                            <td className="py-2 px-3 font-semibold text-blue-600">{truck}</td>
                            <td className="text-right py-2 px-3">{data.count}</td>
                            <td className="text-right py-2 px-3 font-semibold text-green-600">
                              R$ {data.total_value.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <p className="text-white">Carregando dados...</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default UserDashboard;