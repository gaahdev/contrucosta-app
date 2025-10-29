import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { toast } from 'sonner';
import { LogOut, Truck, DollarSign, Package } from 'lucide-react';
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

function UserDashboard({ user, token, onLogout }) {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/user/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboardData(response.data);
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

  useEffect(() => {
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Truck className="w-6 h-6 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk' }}>Commission Tracker</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Avatar>
                  <AvatarFallback className="bg-purple-600 text-white">
                    {user.name.charAt(0).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden sm:block">
                  <p className="text-sm font-semibold text-white" data-testid="user-name">{user.name}</p>
                  <p className="text-xs text-white/80 capitalize" data-testid="user-role">{user.role}</p>
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
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="shadow-xl" data-testid="total-deliveries-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg font-semibold">Total Deliveries</CardTitle>
              <Package className="w-5 h-5 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-purple-600" data-testid="total-deliveries-count">
                {dashboardData?.total_deliveries || 0}
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
                R$ {dashboardData?.total_commission?.toFixed(2) || '0.00'}
              </div>
              <p className="text-sm text-muted-foreground mt-1">Total earned</p>
            </CardContent>
          </Card>
        </div>

        {/* Delivery Breakdown */}
        <Card className="shadow-xl">
          <CardHeader>
            <CardTitle className="text-xl" style={{ fontFamily: 'Space Grotesk' }}>Delivery Breakdown by Truck</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(TRUCK_RATES).map(([truck, rate]) => {
                const count = dashboardData?.deliveries?.[truck] || 0;
                const commission = count * rate;
                return (
                  <div 
                    key={truck} 
                    className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-indigo-50 border border-purple-200"
                    data-testid={`truck-card-${truck}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-bold text-lg" style={{ fontFamily: 'Space Grotesk' }}>{truck}</h3>
                      <Truck className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-muted-foreground">Rate: R$ {rate.toFixed(2)}</p>
                      <p className="text-2xl font-bold text-purple-600" data-testid={`truck-${truck}-deliveries`}>{count}</p>
                      <p className="text-sm font-semibold text-green-600" data-testid={`truck-${truck}-commission`}>
                        R$ {commission.toFixed(2)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

export default UserDashboard;