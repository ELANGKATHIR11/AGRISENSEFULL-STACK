import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Thermometer, Droplets, Sun, Wind, TrendingUp, AlertTriangle, CheckCircle2, Leaf, Users, BarChart3 } from "lucide-react";
import { Link } from "react-router-dom";
import Farm3DContainer from "@/components/three/Farm3DContainer";
import ComparisonCharts3D from "@/components/3d/ComparisonCharts3D";

const Home = () => {
  // Mock data for demonstration
  const sensorData = [
    { icon: Thermometer, label: "Temperature", value: "24°C", status: "normal", color: "text-orange-500" },
    { icon: Droplets, label: "Soil Moisture", value: "68%", status: "normal", color: "text-blue-500" },
    { icon: Sun, label: "Light Intensity", value: "850 lux", status: "good", color: "text-yellow-500" },
    { icon: Wind, label: "Wind Speed", value: "12 km/h", status: "normal", color: "text-gray-500" },
  ];

  const alerts = [
    { type: "warning", message: "Low nitrogen levels detected in Sector A", time: "2 hours ago" },
    { type: "success", message: "Irrigation completed successfully", time: "4 hours ago" },
    { type: "info", message: "Weather forecast: Rain expected tomorrow", time: "6 hours ago" },
  ];

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "warning": return <AlertTriangle className="w-4 h-4 text-destructive" />;
      case "success": return <CheckCircle2 className="w-4 h-4 text-green-600" />;
      default: return <TrendingUp className="w-4 h-4 text-blue-600" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section - Improved */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-green-500 to-green-600 rounded-full mb-6 shadow-lg">
            <Leaf className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-bold text-gray-900 mb-6 leading-tight">
            Welcome to <span className="text-green-600">AgriSense</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-10 leading-relaxed">
            Your intelligent farming companion for optimized crop management and data-driven agricultural decisions. 
            Monitor your farm, analyze soil conditions, and get personalized recommendations.
          </p>
          
          {/* Primary Actions - Better organized */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button asChild size="lg" className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 text-lg font-semibold shadow-lg hover:shadow-xl transition-all duration-300">
              <Link to="/soil-analysis">
                <BarChart3 className="mr-2 h-5 w-5" />
                Analyze Your Soil
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="border-green-600 text-green-600 hover:bg-green-50 px-8 py-3 text-lg font-semibold transition-all duration-300">
              <Link to="/recommend">
                <TrendingUp className="mr-2 h-5 w-5" />
                Get Recommendations
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="border-green-600 text-green-600 hover:bg-green-50 px-8 py-3 text-lg font-semibold transition-all duration-300">
              <Link to="/crops">
                <Leaf className="mr-2 h-5 w-5" />
                Browse Crops
              </Link>
            </Button>
          </div>
        </div>
        {/* 3D Farm Scene */}
        <div className="mb-8">
          <Farm3DContainer />
        </div>

        {/* 3D Comparison Charts - NEW! */}
        <div className="mb-12">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Why Choose <span className="text-green-600">AgriSense</span>?
            </h2>
            <p className="text-lg text-gray-600 max-w-3xl mx-auto">
              Experience dramatic improvements in resource efficiency. Our smart agriculture platform 
              reduces water usage by <span className="font-bold text-blue-600">65%</span>, 
              cuts operating costs by <span className="font-bold text-red-600">58%</span>, 
              and minimizes fertilizer consumption by <span className="font-bold text-yellow-600">52%</span>.
            </p>
          </div>
          
          <ComparisonCharts3D />
          
          {/* Key Metrics Below Chart */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <Card className="text-center border-2 border-blue-200 bg-blue-50/50 hover:shadow-lg transition-all">
              <CardContent className="pt-6 pb-6">
                <div className="text-5xl mb-3">💧</div>
                <div className="text-5xl font-bold text-blue-600 mb-2">65%</div>
                <div className="text-sm font-semibold text-gray-700 mb-1">Water Savings</div>
                <div className="text-xs text-gray-600">Smart irrigation optimization</div>
              </CardContent>
            </Card>
            <Card className="text-center border-2 border-red-200 bg-red-50/50 hover:shadow-lg transition-all">
              <CardContent className="pt-6 pb-6">
                <div className="text-5xl mb-3">💰</div>
                <div className="text-5xl font-bold text-red-600 mb-2">58%</div>
                <div className="text-sm font-semibold text-gray-700 mb-1">Cost Reduction</div>
                <div className="text-xs text-gray-600">Automated resource management</div>
              </CardContent>
            </Card>
            <Card className="text-center border-2 border-yellow-200 bg-yellow-50/50 hover:shadow-lg transition-all">
              <CardContent className="pt-6 pb-6">
                <div className="text-5xl mb-3">🌿</div>
                <div className="text-5xl font-bold text-yellow-600 mb-2">52%</div>
                <div className="text-sm font-semibold text-gray-700 mb-1">Fertilizer Efficiency</div>
                <div className="text-xs text-gray-600">Precision nutrient delivery</div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Dashboard Grid - Cleaner Design */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Sensor Readings */}
          <div className="lg:col-span-2">
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center space-x-3 text-gray-900">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  </div>
                  <span className="text-xl font-semibold">Current Sensor Readings</span>
                </CardTitle>
                <CardDescription className="text-gray-600">
                  Real-time environmental monitoring data from your farm
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {sensorData.map((sensor, index) => (
                    <div key={index} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-all duration-200">
                      <div className={`flex items-center justify-center w-12 h-12 bg-white rounded-lg shadow-sm ${sensor.color}`}>
                        <sensor.icon className="w-6 h-6" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 font-medium">{sensor.label}</p>
                        <p className="text-2xl font-bold text-gray-900">{sensor.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Alerts */}
          <div>
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center space-x-3 text-gray-900">
                  <div className="p-2 bg-amber-100 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                  </div>
                  <span className="text-xl font-semibold">Recent Alerts</span>
                </CardTitle>
                <CardDescription className="text-gray-600">
                  System notifications and farm updates
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {alerts.map((alert, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all duration-200">
                    <div className="mt-0.5">
                      {getAlertIcon(alert.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 font-medium">{alert.message}</p>
                      <p className="text-xs text-gray-500 mt-1">{alert.time}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Features Grid - New Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {[
            {
              icon: BarChart3,
              title: "Smart Analytics",
              description: "Advanced data analysis for better crop management decisions",
              color: "bg-blue-100 text-blue-600"
            },
            {
              icon: Droplets,
              title: "Water Management",
              description: "Optimize irrigation schedules and water usage efficiency",
              color: "bg-cyan-100 text-cyan-600"
            },
            {
              icon: Users,
              title: "Expert Support",
              description: "Get guidance from agricultural experts and AI recommendations",
              color: "bg-green-100 text-green-600"
            }
          ].map((feature, index) => (
            <Card key={index} className="text-center shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
              <CardContent className="pt-8 pb-8">
                <div className={`inline-flex items-center justify-center w-16 h-16 ${feature.color} rounded-2xl mb-4`}>
                  <feature.icon className="w-8 h-8" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Stats - Improved */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: "42", label: "Active Sensors", icon: TrendingUp, color: "text-green-600" },
            { value: "1.2k", label: "Recommendations", icon: CheckCircle2, color: "text-blue-600" },
            { value: "89%", label: "System Efficiency", icon: BarChart3, color: "text-purple-600" },
            { value: "24/7", label: "Monitoring", icon: Thermometer, color: "text-orange-600" }
          ].map((stat, index) => (
            <Card key={index} className="text-center shadow-lg border-0 bg-white/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
              <CardContent className="pt-6 pb-6">
                <div className={`inline-flex items-center justify-center w-12 h-12 bg-gray-100 rounded-lg mb-3 ${stat.color}`}>
                  <stat.icon className="w-6 h-6" />
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-1">{stat.value}</div>
                <div className="text-sm text-gray-600 font-medium">{stat.label}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Home;