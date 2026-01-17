import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { LogOut, DollarSign, Package, ClipboardCheck, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TRUCK_RATES = {
  BKO: 3.50,
  PYW: 3.50,
  NYC: 3.50,
  GKY: 7.50,
  GSD: 7.50,
  AUA: 10.00
};

// Helper function to check if today is the assigned day
const is_assigned_day_today = (assignedDay) => {
  const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const today = new Date().getDay();
  const todayName = days[today];
  return todayName === assignedDay;
};

function UserDashboard({ user, token, onLogout }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checklistOpen, setChecklistOpen] = useState(false);
  const [checklistTemplate, setChecklistTemplate] = useState(null);
  const [checklistData, setChecklistData] = useState({});
  const [submittingChecklist, setSubmittingChecklist] = useState(false);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/user/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
      
      // Auto-open checklist if not completed and user is a driver
      if (user.role === 'driver' && !response.data.checklist_completed) {
        fetchChecklistTemplate();
      }
    } catch (error) {
      toast.error('Failed to load dashboard');
      if (error.response?.status === 401) {
        onLogout();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchChecklistTemplate = async () => {
    try {
      const response = await axios.get(`${API}/checklist/template`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChecklistTemplate(response.data);
      
      // Initialize checklist data
      const initialData = {};
      Object.entries(response.data.categories).forEach(([category, items]) => {
        initialData[category] = {};
        items.forEach(item => {
          initialData[category][item] = '';
        });
      });
      setChecklistData(initialData);
      
      // Fetch current checklist if exists
      const currentResponse = await axios.get(`${API}/checklist/current`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (currentResponse.data.items && Object.keys(currentResponse.data.items).length > 0) {
        setChecklistData(currentResponse.data.items);
      }
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Você só pode preencher o checklist no seu dia atribuído: ' + user.assigned_day);
      } else {
        console.error('Failed to load checklist template', error);
      }
    }
  };

  const handleChecklistSubmit = async () => {
    // Validate all fields are filled
    for (const [category, items] of Object.entries(checklistData)) {
      for (const [item, value] of Object.entries(items)) {
        if (!value || value.trim() === '') {
          toast.error(`Por favor, preencha: ${item}`);
          return;
        }
      }
    }

    setSubmittingChecklist(true);
    try {
      await axios.post(
        `${API}/checklist/submit`,
        { items: checklistData },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Checklist enviado com sucesso!');
      setChecklistOpen(false);
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Falha ao enviar checklist');
    } finally {
      setSubmittingChecklist(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
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
        {/* Checklist Alert */}
        {needsChecklist && (
          <Card className="mb-6 border-orange-300 bg-orange-50" data-testid="checklist-alert">
            <CardContent className="pt-6">
              <div className="flex items-start space-x-4">
                <AlertCircle className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="font-bold text-lg text-orange-900 mb-1">Checklist Pendente</h3>
                  <p className="text-orange-800 mb-3">
                    ⚠️ Você precisa completar o checklist semanal antes de visualizar suas comissões.
                    <br />
                    <span className="font-semibold">Seu dia atribuído: {user.assigned_day}</span>
                    <br />
                    <span className="text-sm">
                      {is_assigned_day_today(user.assigned_day) 
                        ? '✅ Hoje é seu dia! Você pode preencher o checklist agora.' 
                        : `⏳ Você deve preencher o checklist apenas em ${user.assigned_day}. Após passar seu dia sem preencher, as comissões permanecerão bloqueadas até você completar o checklist.`}
                    </span>
                  </p>
                  <Button 
                    onClick={() => setChecklistOpen(true)}
                    data-testid="open-checklist-button"
                    className="bg-orange-600 hover:bg-orange-700"
                  >
                    <ClipboardCheck className="w-4 h-4 mr-2" />
                    {is_assigned_day_today(user.assigned_day) ? 'Completar Checklist Agora' : 'Ver Checklist'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Summary Cards - Blurred if checklist not completed */}
        <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 mb-8 ${needsChecklist ? 'opacity-50 pointer-events-none blur-sm' : ''}`}>
              <Card className="shadow-xl" data-testid="total-deliveries-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold">Total Deliveries</CardTitle>
              <Package className="w-5 h-5 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-red-600" data-testid="total-deliveries-count">
                {needsChecklist ? '---' : (dashboardData?.total_deliveries || 0)}
              </div>
              <p className="text-sm text-muted-foreground mt-1">Across all trucks</p>
            </CardContent>
          </Card>

          <Card className="shadow-xl" data-testid="total-commission-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold">Total Commission</CardTitle>
              <DollarSign className="w-5 h-5 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-green-600" data-testid="total-commission-amount">
                {needsChecklist ? 'R$ ---' : `R$ ${dashboardData?.total_commission?.toFixed(2) || '0.00'}`}
              </div>
              <p className="text-sm text-muted-foreground mt-1">Total earned</p>
            </CardContent>
          </Card>
        </div>

        {/* Delivery Breakdown - Blurred if checklist not completed */}
        <Card className={`shadow-xl ${needsChecklist ? 'opacity-50 pointer-events-none blur-sm' : ''}`}>
          <CardHeader>
            <CardTitle className="text-xl" style={{ fontFamily: 'Space Grotesk' }}>Delivery Breakdown by Truck</CardTitle>
          </CardHeader>
          <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(TRUCK_RATES).map(([truck, rate]) => {
                const count = needsChecklist ? 0 : (dashboardData?.deliveries?.[truck] || 0);
                const commission = count * rate;
                return (
                  <div 
                    key={truck} 
                    className="p-4 rounded-lg bg-gradient-to-br from-red-50 to-red-100 border border-red-200"
                    data-testid={`truck-card-${truck}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-lg" style={{ fontFamily: 'Space Grotesk' }}>{truck}</h3>
                      <img src="/logo.jpg" alt="logo" className="w-5 h-5 object-contain" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Rate: R$ {rate.toFixed(2)}</p>
                      <p className="text-2xl font-bold text-red-600" data-testid={`truck-${truck}-deliveries`}>
                        {needsChecklist ? '---' : count}
                      </p>
                      <p className="text-sm font-semibold text-green-600" data-testid={`truck-${truck}-commission`}>
                        {needsChecklist ? 'R$ ---' : `R$ ${commission.toFixed(2)}`}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </main>

      {/* Checklist Dialog */}
      <Dialog open={checklistOpen} onOpenChange={setChecklistOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto" data-testid="checklist-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl" style={{ fontFamily: 'Space Grotesk' }}>Checklist Semanal</DialogTitle>
            <DialogDescription>
              Complete todos os itens do checklist para visualizar suas comissões
            </DialogDescription>
          </DialogHeader>
          
          {checklistTemplate && (
            <div className="space-y-6 mt-4">
              {Object.entries(checklistTemplate.categories).map(([category, items]) => (
                <div key={category} className="border rounded-lg p-4 bg-muted/30">
                  <h3 className="font-bold text-lg mb-3" style={{ fontFamily: 'Space Grotesk' }}>{category}</h3>
                  <div className="space-y-3">
                    {items.map((item) => (
                      <div key={item} className="space-y-1">
                        <Label className="text-sm capitalize">{item}</Label>
                        <Input
                          value={checklistData[category]?.[item] || ''}
                          onChange={(e) => setChecklistData({
                            ...checklistData,
                            [category]: {
                              ...checklistData[category],
                              [item]: e.target.value
                            }
                          })}
                          placeholder="Digite sua resposta"
                          data-testid={`checklist-${category}-${item}`}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              
              <Button 
                onClick={handleChecklistSubmit}
                data-testid="submit-checklist-button"
                className="w-full h-12 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-700 hover:to-red-600"
                disabled={submittingChecklist}
              >
                <ClipboardCheck className="w-5 h-5 mr-2" />
                {submittingChecklist ? 'Enviando...' : 'Enviar Checklist'}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default UserDashboard;