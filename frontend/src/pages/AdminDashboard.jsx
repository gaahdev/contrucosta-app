import { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { LogOut, Truck, Users, DollarSign, Edit, ClipboardCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
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
  const [checklists, setChecklists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDeliveries, setUserDeliveries] = useState([]);
  const [editData, setEditData] = useState({ truck_type: '', delivery_count: 0 });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [checklistDialogOpen, setChecklistDialogOpen] = useState(false);
  const [selectedChecklist, setSelectedChecklist] = useState(null);
  const navigate = useNavigate();

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
      if (error.response?.status === 401 || error.response?.status === 403) {
        onLogout();
        navigate('/login');
      }
    }
  };

  const fetchChecklists = async () => {
    try {
      const response = await axios.get(`${API}/admin/checklists`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChecklists(response.data);
    } catch (error) {
      toast.error('Failed to load checklists');
    }
  };

  const fetchUserDeliveries = async (userId) => {
    try {
      const response = await axios.get(`${API}/admin/user/${userId}/deliveries`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUserDeliveries(response.data);
    } catch (error) {
      toast.error('Failed to load user deliveries');
    }
  };

  useEffect(() => {
    const loadData = async () => {
      await Promise.all([fetchUsers(), fetchChecklists()]);
      setLoading(false);
    };
    loadData();
  }, []);

  const handleEditClick = async (userData) => {
    setSelectedUser(userData);
    await fetchUserDeliveries(userData.user.id);
    setDialogOpen(true);
  };

  const handleUpdateDelivery = async () => {
    if (!editData.truck_type || editData.delivery_count < 0) {
      toast.error('Please select a truck type and enter a valid count');
      return;
    }

    try {
      await axios.post(
        `${API}/admin/delivery`,
        {
          user_id: selectedUser.user.id,
          truck_type: editData.truck_type,
          delivery_count: parseInt(editData.delivery_count)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Delivery updated successfully');
      setEditData({ truck_type: '', delivery_count: 0 });
      await fetchUsers();
      await fetchUserDeliveries(selectedUser.user.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update delivery');
    }
  };

  const handleViewChecklist = (checklist) => {
    setSelectedChecklist(checklist);
    setChecklistDialogOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  const totalUsers = users.length;
  const totalCommission = users.reduce((sum, u) => sum + u.total_commission, 0);
  const totalDeliveries = users.reduce((sum, u) => sum + u.total_deliveries, 0);

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
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk' }}>Admin Panel</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <Avatar>
                  <AvatarFallback className="bg-purple-600 text-white">
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
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList className="bg-white/20 backdrop-blur-sm">
            <TabsTrigger value="users" className="data-[state=active]:bg-white">Users & Commissions</TabsTrigger>
            <TabsTrigger value="checklists" className="data-[state=active]:bg-white">Checklists</TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="space-y-6">
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
                  <Truck className="w-5 h-5 text-purple-600" />
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-purple-600" data-testid="admin-total-deliveries">{totalDeliveries}</div>
                  <p className="text-sm text-muted-foreground mt-1">All trucks</p>
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
                        <th className="text-left py-3 px-4 font-semibold">Username</th>
                        <th className="text-left py-3 px-4 font-semibold">Role</th>
                        <th className="text-left py-3 px-4 font-semibold">Day</th>
                        <th className="text-right py-3 px-4 font-semibold">Deliveries</th>
                        <th className="text-right py-3 px-4 font-semibold">Commission</th>
                        <th className="text-center py-3 px-4 font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((userData) => (
                        <tr key={userData.user.id} className="border-b hover:bg-muted/50" data-testid={`user-row-${userData.user.username}`}>
                          <td className="py-3 px-4" data-testid={`user-name-${userData.user.username}`}>{userData.user.name}</td>
                          <td className="py-3 px-4" data-testid={`user-username-${userData.user.username}`}>{userData.user.username}</td>
                          <td className="py-3 px-4 capitalize" data-testid={`user-role-${userData.user.username}`}>{userData.user.role}</td>
                          <td className="py-3 px-4 text-sm">{userData.user.assigned_day || '-'}</td>
                          <td className="py-3 px-4 text-right" data-testid={`user-deliveries-${userData.user.username}`}>{userData.total_deliveries}</td>
                          <td className="py-3 px-4 text-right font-semibold text-green-600" data-testid={`user-commission-${userData.user.username}`}>
                            R$ {userData.total_commission.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Dialog open={dialogOpen && selectedUser?.user.id === userData.user.id} onOpenChange={(open) => {
                              setDialogOpen(open);
                              if (!open) setSelectedUser(null);
                            }}>
                              <DialogTrigger asChild>
                                <Button 
                                  size="sm" 
                                  onClick={() => handleEditClick(userData)}
                                  data-testid={`edit-user-button-${userData.user.username}`}
                                  className="bg-purple-600 hover:bg-purple-700"
                                >
                                  <Edit className="w-4 h-4 mr-1" />
                                  Edit
                                </Button>
                              </DialogTrigger>
                              <DialogContent data-testid="edit-delivery-dialog">
                                <DialogHeader>
                                  <DialogTitle>Update Deliveries - {selectedUser?.user.name}</DialogTitle>
                                  <DialogDescription>
                                    Update delivery count for any truck type
                                  </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 mt-4">
                                  <div className="p-3 bg-muted rounded-lg">
                                    <h4 className="font-semibold mb-2 text-sm">Current Deliveries:</h4>
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                      {userDeliveries.map((del) => (
                                        <div key={del.id} className="flex justify-between">
                                          <span className="font-medium">{del.truck_type}:</span>
                                          <span data-testid={`current-${del.truck_type}-count`}>{del.delivery_count}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>

                                  <div className="space-y-2">
                                    <Label>Truck Type</Label>
                                    <Select value={editData.truck_type} onValueChange={(value) => setEditData({...editData, truck_type: value})}>
                                      <SelectTrigger data-testid="select-truck-type">
                                        <SelectValue placeholder="Select truck" />
                                      </SelectTrigger>
                                      <SelectContent>
                                        {TRUCK_TYPES.map((truck) => (
                                          <SelectItem key={truck} value={truck} data-testid={`truck-option-${truck}`}>
                                            {truck} (R$ {TRUCK_RATES[truck].toFixed(2)})
                                          </SelectItem>
                                        ))}
                                      </SelectContent>
                                    </Select>
                                  </div>

                                  <div className="space-y-2">
                                    <Label>Delivery Count</Label>
                                    <Input
                                      type="number"
                                      min="0"
                                      data-testid="delivery-count-input"
                                      placeholder="Enter delivery count"
                                      value={editData.delivery_count}
                                      onChange={(e) => setEditData({...editData, delivery_count: e.target.value})}
                                    />
                                  </div>

                                  <Button 
                                    onClick={handleUpdateDelivery} 
                                    data-testid="update-delivery-button"
                                    className="w-full bg-purple-600 hover:bg-purple-700"
                                  >
                                    Update Delivery
                                  </Button>
                                </div>
                              </DialogContent>
                            </Dialog>
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
          </TabsContent>

          <TabsContent value="checklists" className="space-y-6">
            <Card className="shadow-xl">
              <CardHeader>
                <CardTitle className="text-xl flex items-center" style={{ fontFamily: 'Space Grotesk' }}>
                  <ClipboardCheck className="w-5 h-5 mr-2" />
                  Driver Checklists
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full" data-testid="checklists-table">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4 font-semibold">Driver</th>
                        <th className="text-left py-3 px-4 font-semibold">Week Start</th>
                        <th className="text-left py-3 px-4 font-semibold">Status</th>
                        <th className="text-left py-3 px-4 font-semibold">Submitted</th>
                        <th className="text-center py-3 px-4 font-semibold">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {checklists.map((checklist) => (
                        <tr key={checklist.id} className="border-b hover:bg-muted/50" data-testid={`checklist-row-${checklist.id}`}>
                          <td className="py-3 px-4 font-medium">{checklist.user_name}</td>
                          <td className="py-3 px-4">{new Date(checklist.week_start).toLocaleDateString('pt-BR')}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              checklist.completed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {checklist.completed ? 'Completo' : 'Pendente'}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm">
                            {checklist.submitted_at ? new Date(checklist.submitted_at).toLocaleString('pt-BR') : '-'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewChecklist(checklist)}
                              data-testid={`view-checklist-${checklist.id}`}
                              disabled={!checklist.completed}
                            >
                              Ver Detalhes
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {checklists.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      Nenhum checklist enviado ainda
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Checklist View Dialog */}
      <Dialog open={checklistDialogOpen} onOpenChange={setChecklistDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto" data-testid="view-checklist-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl" style={{ fontFamily: 'Space Grotesk' }}>
              Checklist - {selectedChecklist?.user_name}
            </DialogTitle>
            <DialogDescription>
              Semana: {selectedChecklist?.week_start && new Date(selectedChecklist.week_start).toLocaleDateString('pt-BR')}
            </DialogDescription>
          </DialogHeader>
          
          {selectedChecklist?.items && (
            <div className="space-y-6 mt-4">
              {Object.entries(selectedChecklist.items).map(([category, items]) => (
                <div key={category} className="border rounded-lg p-4 bg-muted/30">
                  <h3 className="font-bold text-lg mb-3" style={{ fontFamily: 'Space Grotesk' }}>{category}</h3>
                  <div className="space-y-2">
                    {Object.entries(items).map(([item, response]) => (
                      <div key={item} className="grid grid-cols-2 gap-2 text-sm">
                        <div className="font-medium capitalize">{item}:</div>
                        <div className="text-muted-foreground">{response}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdminDashboard;