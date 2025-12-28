import { CheckCircle2, AlertTriangle, Info, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface NotificationProps {
  id?: string;
  type?: "success" | "error" | "warning" | "info";
  title?: string;
  message: string;
  duration?: number;
  onClose?: () => void;
  action?: {
    label: string;
    onClick: () => void;
  };
}

const notificationStyles = {
  success: {
    container: "bg-green-50 border-green-200 text-green-800",
    icon: CheckCircle2,
    iconColor: "text-green-600"
  },
  error: {
    container: "bg-red-50 border-red-200 text-red-800", 
    icon: AlertCircle,
    iconColor: "text-red-600"
  },
  warning: {
    container: "bg-amber-50 border-amber-200 text-amber-800",
    icon: AlertTriangle,
    iconColor: "text-amber-600"
  },
  info: {
    container: "bg-blue-50 border-blue-200 text-blue-800",
    icon: Info,
    iconColor: "text-blue-600"
  }
};

export function Notification({ 
  type = "info", 
  title, 
  message, 
  onClose, 
  action 
}: NotificationProps) {
  const style = notificationStyles[type];
  const Icon = style.icon;

  return (
    <div className={cn(
      "flex items-start gap-3 p-4 rounded-lg border shadow-sm transition-all duration-300",
      style.container
    )}>
      <Icon className={cn("w-5 h-5 mt-0.5 flex-shrink-0", style.iconColor)} />
      
      <div className="flex-1 min-w-0">
        {title && (
          <p className="font-medium text-sm mb-1">{title}</p>
        )}
        <p className="text-sm">{message}</p>
        
        {action && (
          <button
            onClick={action.onClick}
            className="mt-2 text-sm font-medium hover:underline focus:outline-none focus:underline"
          >
            {action.label}
          </button>
        )}
      </div>
      
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 p-1 hover:bg-black/5 rounded-md transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// In-page notification component (not a toast)
export function InlineNotification({ 
  type = "info", 
  title, 
  message, 
  onClose,
  className 
}: NotificationProps & { className?: string }) {
  const style = notificationStyles[type];
  const Icon = style.icon;

  return (
    <div className={cn(
      "flex items-start gap-3 p-4 rounded-lg border",
      style.container,
      className
    )}>
      <Icon className={cn("w-5 h-5 mt-0.5 flex-shrink-0", style.iconColor)} />
      
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className="font-medium text-sm mb-1">{title}</h4>
        )}
        <p className="text-sm">{message}</p>
      </div>
      
      {onClose && (
        <button
          onClick={onClose}
          className="flex-shrink-0 p-1 hover:bg-black/5 rounded-md transition-colors"
          aria-label="Dismiss notification"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}