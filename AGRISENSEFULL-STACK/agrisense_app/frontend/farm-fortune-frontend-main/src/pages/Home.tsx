import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Thermometer, Droplets, Sun, Wind, TrendingUp, AlertTriangle, CheckCircle2 } from "lucide-react";
import { Link } from "react-router-dom";

const Home = () => {
  // Mock data for demonstration
  const sensorData = [
    { icon: Thermometer, label: "Temperature", value: "24°C", status: "normal" },
    { icon: Droplets, label: "Soil Moisture", value: "68%", status: "normal" },
    { icon: Sun, label: "Light Intensity", value: "850 lux", status: "good" },
    { icon: Wind, label: "Wind Speed", value: "12 km/h", status: "normal" },
  ];

  const alerts = [
    { type: "warning", message: "Low nitrogen levels detected in Sector A", time: "2 hours ago" },
    { type: "success", message: "Irrigation completed successfully", time: "4 hours ago" },
    { type: "info", message: "Weather forecast: Rain expected tomorrow", time: "6 hours ago" },
  ];

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "warning": return <AlertTriangle className="w-4 h-4 text-destructive" />;
      case "success": return <CheckCircle2 className="w-4 h-4 text-primary" />;
      default: return <TrendingUp className="w-4 h-4 text-accent-foreground" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-secondary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Welcome to AgriSense
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Your intelligent farming companion for optimized crop management and data-driven agricultural decisions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg" className="bg-gradient-primary hover:shadow-glow transition-all duration-300 transform hover:scale-105 animate-bounce-gentle">
              <Link to="/soil-analysis">Analyze Your Soil</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="hover:bg-secondary hover:shadow-soft transition-all duration-300">
              <Link to="/recommend">Get Recommendations</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="hover:bg-secondary hover:shadow-soft transition-all duration-300">
              <Link to="/crops">Browse Crops</Link>
            </Button>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Sensor Readings */}
          <div className="lg:col-span-2">
            <Card className="shadow-medium hover:shadow-strong transition-all duration-300 animate-fade-in">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="w-5 h-5 text-primary animate-bounce-gentle" />
                  <span className="font-serif">Current Sensor Readings</span>
                </CardTitle>
                <CardDescription>
                  Real-time environmental monitoring data from your farm
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6">
                  {sensorData.map((sensor, index) => (
                    <div key={index} className="flex items-center space-x-4 p-4 bg-gradient-accent rounded-lg hover:shadow-soft transition-all duration-300 transform hover:scale-105 animate-scale-in" style={{ animationDelay: `${index * 100}ms` }}>
                      <div className="flex items-center justify-center w-12 h-12 bg-card rounded-lg shadow-soft animate-pulse-glow">
                        <sensor.icon className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">{sensor.label}</p>
                        <p className="text-2xl font-bold text-foreground font-serif">{sensor.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Alerts */}
          <div>
            <Card className="shadow-medium hover:shadow-strong transition-all duration-300 animate-fade-in" style={{ animationDelay: '200ms' }}>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <AlertTriangle className="w-5 h-5 text-primary animate-bounce-gentle" />
                  <span className="font-serif">Recent Alerts</span>
                </CardTitle>
                <CardDescription>
                  System notifications and farm updates
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {alerts.map((alert, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-secondary rounded-lg hover:bg-accent transition-all duration-300 transform hover:scale-105 animate-scale-in" style={{ animationDelay: `${300 + index * 100}ms` }}>
                    {getAlertIcon(alert.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{alert.message}</p>
                      <p className="text-xs text-muted-foreground mt-1">{alert.time}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-8">
          {[
            { value: "42", label: "Active Sensors", delay: "500ms" },
            { value: "1.2k", label: "Recommendations", delay: "600ms" },
            { value: "89%", label: "System Efficiency", delay: "700ms" },
            { value: "24/7", label: "Monitoring", delay: "800ms" }
          ].map((stat, index) => (
            <Card key={index} className="text-center shadow-soft hover:shadow-medium transition-all duration-300 transform hover:scale-105 animate-scale-in" style={{ animationDelay: stat.delay }}>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-primary mb-2 font-serif animate-pulse-glow">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;