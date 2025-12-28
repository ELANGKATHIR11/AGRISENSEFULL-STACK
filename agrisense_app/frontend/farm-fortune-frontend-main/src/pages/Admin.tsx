import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  Settings, 
  Database, 
  Activity, 
  RefreshCw, 
  Server, 
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Zap
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import { api } from "../lib/api";
import { useTranslation } from "react-i18next";

interface SystemMetric {
  label: string;
  value: string;
  progress: number;
  status: "good" | "warning" | "error";
}

interface ModelWeight {
  model: string;
  weight: number;
  accuracy: number;
  lastUpdated: string;
}

const Admin = () => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();
  const { t } = useTranslation();

  // Mock system metrics
  const systemMetrics: SystemMetric[] = [
    { label: "CPU Usage", value: "45%", progress: 45, status: "good" },
    { label: "Memory Usage", value: "67%", progress: 67, status: "warning" },
    { label: "Disk Space", value: "23%", progress: 23, status: "good" },
    { label: "API Response Time", value: "120ms", progress: 12, status: "good" },
  ];

  // Mock model weights
  const modelWeights: ModelWeight[] = [
    {
      model: "TensorFlow Crop Predictor",
      weight: 0.7,
      accuracy: 94.5,
      lastUpdated: "2024-01-15 14:30:00"
    },
    {
      model: "TensorFlow Yield Predictor", 
      weight: 0.8,
      accuracy: 91.2,
      lastUpdated: "2024-01-15 14:30:00"
    },
    {
      model: "RandomForest Fallback",
      weight: 0.3,
      accuracy: 87.8,
      lastUpdated: "2024-01-15 14:30:00"
    },
  ];

  const recentActivities = [
    { action: "Model weights updated", time: "2 hours ago", status: "success" },
    { action: "Dataset reload completed", time: "4 hours ago", status: "success" },
    { action: "High memory usage detected", time: "6 hours ago", status: "warning" },
    { action: "API health check passed", time: "8 hours ago", status: "success" },
    { action: "TensorFlow model loaded", time: "1 day ago", status: "success" },
  ];

  const handleReloadModels = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    setLoading(false);
    
    toast({
      title: t("models_reloaded"),
      description: t("models_reload_done"),
    });
  };

  const handleReloadDataset = async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setLoading(false);
    
    toast({
      title: t("dataset_reloaded"), 
      description: t("dataset_reload_done"),
    });
  };

  const handleResetAll = async () => {
  if (!confirm(t("confirm_erase_all"))) return;
    setLoading(true);
    try {
      await api.adminReset();
      toast({ title: t("all_data_erased"), description: t("storage_reset_done") });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast({ title: t("reset_failed"), description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success": return <CheckCircle2 className="w-4 h-4 text-primary" />;
      case "warning": return <AlertTriangle className="w-4 h-4 text-destructive" />;
      default: return <Clock className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "good": return "text-primary";
      case "warning": return "text-destructive";
      case "error": return "text-destructive";
      default: return "text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("system_administration")}</h1>
          <p className="text-muted-foreground">{t("monitor_and_manage")}</p>
        </div>

        <Tabs defaultValue="overview" className="space-y-8">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">{t("overview")}</TabsTrigger>
            <TabsTrigger value="models">{t("ml_models")}</TabsTrigger>
            <TabsTrigger value="system">{t("system")}</TabsTrigger>
            <TabsTrigger value="activity">{t("activity")}</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Quick Actions */}
            <Card className="shadow-medium">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-primary" />
                  <span>{t("quick_actions")}</span>
                </CardTitle>
                <CardDescription>{t("common_admin_tasks")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Button 
                    onClick={handleReloadModels}
                    disabled={loading}
                    className="bg-gradient-primary hover:shadow-glow transition-spring"
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    {t("reload_models")}
                  </Button>
                  <Button 
                    onClick={handleReloadDataset}
                    variant="outline"
                    disabled={loading}
                  >
                    <Database className="w-4 h-4 mr-2" />
                    {t("reload_dataset")}
                  </Button>
                  <Button variant="outline">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    {t("view_logs")}
                  </Button>
                  <Button variant="outline">
                    <Settings className="w-4 h-4 mr-2" />
                    {t("config")}
                  </Button>
                  <Button onClick={handleResetAll} variant="destructive" disabled={loading}>
                    <Database className="w-4 h-4 mr-2" />
                    {t("erase_all_data")}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* System Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {systemMetrics.map((metric, index) => (
                <Card key={index} className="shadow-soft">
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-muted-foreground">{metric.label}</span>
                      <span className={`font-bold ${getStatusColor(metric.status)}`}>
                        {metric.value}
                      </span>
                    </div>
                    <Progress value={metric.progress} className="h-2" />
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* ML Models Tab */}
          <TabsContent value="models" className="space-y-6">
            <Card className="shadow-medium">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Server className="w-5 h-5 text-primary" />
                  <span>Model Blend Weights</span>
                </CardTitle>
                <CardDescription>
                  Current ML model weights and performance metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {modelWeights.map((model, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gradient-accent">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold text-foreground">{model.model}</h3>
                        <Badge className="bg-primary text-primary-foreground">
                          Weight: {(model.weight * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <span className="text-sm text-muted-foreground">Accuracy</span>
                          <div className="flex items-center space-x-2 mt-1">
                            <Progress value={model.accuracy} className="flex-1 h-2" />
                            <span className="text-sm font-medium text-foreground">
                              {model.accuracy}%
                            </span>
                          </div>
                        </div>
                        
                        <div>
                          <span className="text-sm text-muted-foreground">Last Updated</span>
                          <p className="text-sm text-foreground mt-1">{model.lastUpdated}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* System Tab */}
          <TabsContent value="system" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* System Health */}
              <Card className="shadow-medium">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="w-5 h-5 text-primary" />
                    <span>{t("system_health")}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {systemMetrics.map((metric, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-secondary rounded-lg">
                      <span className="text-sm font-medium text-foreground">{metric.label}</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm ${getStatusColor(metric.status)}`}>
                          {metric.value}
                        </span>
                        <div className={`w-2 h-2 rounded-full ${
                          metric.status === 'good' ? 'bg-primary' :
                          metric.status === 'warning' ? 'bg-destructive' : 'bg-muted-foreground'
                        }`} />
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Configuration */}
              <Card className="shadow-medium">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Settings className="w-5 h-5 text-primary" />
                    <span>{t("configuration")}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
                      <span className="text-sm text-foreground">TensorFlow Enabled</span>
                      <Badge className="bg-primary text-primary-foreground">Active</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
                      <span className="text-sm text-foreground">API Version</span>
                      <span className="text-sm text-muted-foreground">v1.2.3</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
                      <span className="text-sm text-foreground">Dataset Version</span>
                      <span className="text-sm text-muted-foreground">2024.01.15</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
                      <span className="text-sm text-foreground">Environment</span>
                      <Badge variant="outline">Development</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity">
            <Card className="shadow-medium">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-primary" />
                  <span>{t("recent_activity")}</span>
                </CardTitle>
                <CardDescription>{t("system_events_actions")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivities.map((activity, index) => (
                    <div key={index} className="flex items-center space-x-4 p-3 bg-secondary rounded-lg">
                      {getStatusIcon(activity.status)}
                      <div className="flex-1">
                        <p className="text-sm text-foreground">{activity.action}</p>
                        <p className="text-xs text-muted-foreground">{activity.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Admin;