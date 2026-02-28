import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { LogOut, Users, DollarSign } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

const TRUCK_TYPES = ['BKO', 'PYW', 'NYC', 'GKY', 'GSD', 'AUA'];
const TRUCK_RATES = {
  BKO: 3.50,
  PYW: 3.50,
  NYC: 3.50,
  GKY: 7.50,
  GSD: 7.50,
  AUA: 10.00
};

function AdminDashboard({ user, token, onLogout }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [commissionDialogOpen, setCommissionDialogOpen] = useState(false);
  const [occurrenceDialogOpen, setOccurrenceDialogOpen] = useState(false);
  const [commissionData, setCommissionData] = useState({ value: '', truck_type: 'BKO' });
  const [occurrenceData, setOccurrenceData] = useState({ type: 'delay', description: '', truck_type: 'BKO' });
  const [loadingCommission, setLoadingCommission] = useState(false);

  const navigate = useNavigate();

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });
      setUsers(response.data);
      console.log('✅ Usuários carregados do backend');
    } catch (error) {
      console.error('Erro ao carregar usuários:', error.message);
      setUsers([]);
      toast.error(error.response?.data?.detail || 'Falha ao carregar usuários');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      await fetchUsers();
      setLoading(false);
    };
    loadData();
  }, []);



  const handleLaunchCommission = async () => {
    if (!selectedUser || !commissionData.value || parseFloat(commissionData.value) <= 0) {
      toast.error('❌ Preencha um valor válido');
      return;
    }

    setLoadingCommission(true);
    try {
      const payload = {
        employee_id: selectedUser.user.id,
        truck_type: commissionData.truck_type,
        value: parseFloat(commissionData.value)
      };
      await axios.post(`${API}/deliveries`, payload, { timeout: 5000 });

      toast.success(`✅ Entrega registrada! R$ ${parseFloat(commissionData.value).toFixed(2)} - ${commissionData.truck_type}`);
      setCommissionDialogOpen(false);
      setCommissionData({ value: '', truck_type: 'BKO' });
      await fetchUsers();
    } catch (err) {
      toast.error('❌ Erro: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingCommission(false);
    }
  };

  const handleRegisterOccurrence = async () => {
    if (!selectedUser || !occurrenceData.description.trim()) {
      toast.error('❌ Preencha a descrição');
      return;
    }

    setLoadingCommission(true);
    try {
      const payload = {
        employee_id: selectedUser.user.id,
        employee_name: selectedUser.user.name,
        occurrence_type: occurrenceData.type,
        description: occurrenceData.description,
        truck_type: occurrenceData.truck_type
      };
      await axios.post(`${API}/occurrences`, payload, { timeout: 5000 });

      toast.success(`✅ Ocorrência registrada! ${occurrenceData.truck_type}`);
      setOccurrenceDialogOpen(false);
      setOccurrenceData({ type: 'delay', description: '', truck_type: 'BKO' });
      await fetchUsers();
    } catch (err) {
      toast.error('❌ Erro: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingCommission(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #660000 0%, #0b0b0b 100%)' }}>
        <video
          src="/loading.mp4"
          autoPlay
          loop
          muted
          playsInline
          className="w-64 h-64 object-contain rounded-md shadow-lg"
        />
      </div>
    );
  }

  const totalUsers = users.length;
  const totalCommission = users.reduce((sum, u) => sum + u.total_commission, 0);
  const totalDeliveries = users.reduce((sum, u) => sum + u.total_deliveries, 0);
  const totalTodayDelivered = users.reduce((sum, u) => sum + (u.today_delivered_value || 0), 0);

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
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk' }}>Admin Panel</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Avatar>
                  <AvatarFallback className="bg-red-600 text-white">
                    {user.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <p className="text-sm font-semibold text-white" data-testid="admin-name">{user.name}</p>
                  <p className="text-xs text-white/80" data-testid="admin-role">Administrator</p>
                </div>
              </div>
              <Button
                onClick={onLogout}
                data-testid="admin-logout-button"
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
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="shadow-xl" data-testid="admin-total-users-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold">Total Users</CardTitle>
                <Users className="w-5 h-5 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-blue-600" data-testid="admin-total-users">{totalUsers}</div>
                <p className="text-sm text-muted-foreground mt-1">Drivers & Helpers</p>
              </CardContent>
            </Card>

            <Card className="shadow-xl" data-testid="admin-total-deliveries-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold">Total Deliveries</CardTitle>
                <img src="/logo.jpg" alt="logo" className="w-5 h-5 object-contain" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-red-600" data-testid="admin-total-deliveries">{totalDeliveries}</div>
                <p className="text-sm text-muted-foreground mt-1">All trucks</p>
                <p className="text-xs text-muted-foreground mt-1">Hoje: R$ {totalTodayDelivered.toFixed(2)}</p>
              </CardContent>
            </Card>

            <Card className="shadow-xl" data-testid="admin-total-commission-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-lg font-semibold">Total Commission</CardTitle>
                <DollarSign className="w-5 h-5 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-green-600" data-testid="admin-total-commission">R$ {totalCommission.toFixed(2)}</div>
                <p className="text-sm text-muted-foreground mt-1">All users</p>
              </CardContent>
            </Card>
          </div>

          {/* Users Table */}
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl" style={{ fontFamily: 'Space Grotesk' }}>Users & Commissions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full" data-testid="users-table">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-4 font-semibold">Name</th>
                      <th className="text-left py-3 px-4 font-semibold">Role</th>
                      <th className="text-left py-3 px-4 font-semibold">Day</th>
                      <th className="text-right py-3 px-4 font-semibold whitespace-nowrap">📦 Valor Entregue</th>
                      <th className="text-right py-3 px-4 font-semibold whitespace-nowrap">💰 Valor a Receber</th>
                      <th className="text-center py-3 px-4 font-semibold whitespace-nowrap">🚛 Caminhões</th>
                      <th className="text-center py-3 px-4 font-semibold whitespace-nowrap">⚠️ Ocorrências</th>
                      <th className="text-center py-3 px-4 font-semibold whitespace-nowrap">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((userData) => (
                      <tr key={userData.user.id} className="border-b hover:bg-muted/50" data-testid={`user-row-${userData.user.username}`}>
                        <td className="py-3 px-4" data-testid={`user-name-${userData.user.username}`}>{userData.user.name}</td>
                        <td className="py-3 px-4 capitalize" data-testid={`user-role-${userData.user.username}`}>{userData.user.role}</td>
                        <td className="py-3 px-4 text-sm">{userData.user.assigned_day || '-'}</td>
                        <td className="py-3 px-4 text-right text-blue-600 font-semibold">
                          <div>R$ {userData.total_delivered_value ? userData.total_delivered_value.toFixed(2) : '0.00'}</div>
                          <div className="text-xs text-muted-foreground font-normal">
                            Hoje: R$ {userData.today_delivered_value ? userData.today_delivered_value.toFixed(2) : '0.00'}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-right text-green-600 font-semibold">
                          <div>R$ {userData.value_to_receive ? userData.value_to_receive.toFixed(2) : '0.00'}</div>
                          <div className="text-xs text-muted-foreground font-normal">
                            {userData.statistics?.percentage?.toFixed(1) || '1.0'}%
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex flex-wrap gap-1 justify-center">
                            {userData.by_truck && Object.entries(userData.by_truck).map(([truck, data]) => (
                              <span key={truck} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded" title={`${truck}: R$ ${data.total_value.toFixed(2)}`}>
                                {truck}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className="inline-block bg-yellow-100 text-yellow-800 px-3 py-1 rounded text-sm font-semibold">
                            {userData.statistics?.occurrence_count || 0}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex gap-1 items-center justify-center">
                            {/* Lançar Comissão */}
                            <Dialog open={commissionDialogOpen && selectedUser?.user.id === userData.user.id} onOpenChange={(open) => {
                              setCommissionDialogOpen(open);
                              if (!open) setSelectedUser(null);
                            }}>
                              <DialogTrigger asChild>
                                <Button
                                  size="sm"
                                  onClick={() => { setSelectedUser(userData); setCommissionData({ value: '', truck_type: 'BKO' }); }}
                                  className="bg-green-600 hover:bg-green-700 px-2 py-1 h-8 text-xs"
                                  title="Lançar Comissão"
                                >
                                  💰
                                </Button>
                              </DialogTrigger>
                              <DialogContent data-testid="launch-commission-dialog">
                                <DialogHeader>
                                  <DialogTitle>Lançar Entrega - {selectedUser?.user.name}</DialogTitle>
                                  <DialogDescription>
                                    Registre o valor entregue e selecione o caminhão
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 mt-4">
                                  <div className="space-y-2">
                                    <Label>Caminhão</Label>
                                    <Select value={commissionData.truck_type} onValueChange={(value) => setCommissionData({ ...commissionData, truck_type: value })}>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Selecione o caminhão" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {TRUCK_TYPES.map(truck => (
                                          <SelectItem key={truck} value={truck}>
                                            {truck}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Valor Entregue (R$)</Label>
                                    <Input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      placeholder="ex: 5000.00"
                                      value={commissionData.value}
                                      onChange={(e) => setCommissionData({ ...commissionData, value: e.target.value })}
                                    />
                                  </div>
                                  <Button
                                    onClick={handleLaunchCommission}
                                    disabled={loadingCommission}
                                    className="w-full bg-green-600 hover:bg-green-700"
                                  >
                                    {loadingCommission ? '⏳ Registrando...' : '✅ REGISTRAR ENTREGA'}
                                  </Button>
                                </div>
                              </DialogContent>
                            </Dialog>

                            {/* Registrar Ocorrência */}
                            <Dialog open={occurrenceDialogOpen && selectedUser?.user.id === userData.user.id} onOpenChange={(open) => {
                              setOccurrenceDialogOpen(open);
                              if (!open) setSelectedUser(null);
                            }}>
                              <DialogTrigger asChild>
                                <Button
                                  size="sm"
                                  onClick={() => { setSelectedUser(userData); setOccurrenceData({ type: 'delay', description: '', truck_type: 'BKO' }); }}
                                  className="bg-orange-600 hover:bg-orange-700 px-2 py-1 h-8 text-xs"
                                  title="Registrar Ocorrência"
                                >
                                  ⚠️
                                </Button>
                              </DialogTrigger>
                              <DialogContent data-testid="register-occurrence-dialog">
                                <DialogHeader>
                                  <DialogTitle>Registrar Ocorrência - {selectedUser?.user.name}</DialogTitle>
                                  <DialogDescription>
                                    Registre atrasos, danos ou outros problemas
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 mt-4">
                                  <div className="space-y-2">
                                    <Label>Caminhão</Label>
                                    <Select value={occurrenceData.truck_type} onValueChange={(value) => setOccurrenceData({ ...occurrenceData, truck_type: value })}>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Selecione o caminhão" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {TRUCK_TYPES.map(truck => (
                                          <SelectItem key={truck} value={truck}>
                                            {truck}
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Tipo de Ocorrência</Label>
                                    <Select value={occurrenceData.type} onValueChange={(value) => setOccurrenceData({ ...occurrenceData, type: value })}>
                                      <SelectTrigger>
                                        <SelectValue placeholder="Selecione o tipo" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="delay">🕐 Atraso</SelectItem>
                                        <SelectItem value="damage">💥 Dano</SelectItem>
                                        <SelectItem value="accident">🚗 Acidente</SelectItem>
                                        <SelectItem value="missing_goods">📦 Falta de Mercadoria</SelectItem>
                                        <SelectItem value="other">❓ Outro</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div className="space-y-2">
                                    <Label>Descrição</Label>
                                    <Input
                                      placeholder="ex: Atraso de 2 horas na entrega"
                                      value={occurrenceData.description}
                                      onChange={(e) => setOccurrenceData({ ...occurrenceData, description: e.target.value })}
                                    />
                                  </div>
                                  <Button
                                    onClick={handleRegisterOccurrence}
                                    disabled={loadingCommission}
                                    className="w-full bg-orange-600 hover:bg-orange-700"
                                  >
                                    {loadingCommission ? '⏳ Registrando...' : '✅ REGISTRAR'}
                                  </Button>
                                </div>
                              </DialogContent>
                            </Dialog>

                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {users.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground" data-testid="no-users-message">
                    No users registered yet
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default AdminDashboard;