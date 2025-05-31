// packages/ui/src/confirm-dialog/index.tsx
import { AlertCircle, AlertTriangle, Check, Info, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { cn } from '../../lib/utils';

export type ConfirmDialogType = 'info' | 'warning' | 'error' | 'success' | 'confirm' | 'delete';

export interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  type?: ConfirmDialogType;
  isLoading?: boolean;
  isDangerous?: boolean;
  closeOnEsc?: boolean;
  closeOnBackdropClick?: boolean;
  className?: string;
  showIcon?: boolean;
  reverseButtons?: boolean;
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Xác nhận',
  cancelLabel = 'Hủy',
  onConfirm,
  onCancel,
  type = 'confirm',
  isLoading = false,
  isDangerous = false,
  closeOnEsc = true,
  closeOnBackdropClick = true,
  className,
  showIcon = true,
  reverseButtons = false,
}) => {
  // For fade-in/fade-out animation
  const [isAnimating, setIsAnimating] = useState(false);
  
  // Auto-close on ESC key press
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen && closeOnEsc) {
        onCancel();
      }
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscKey);
      document.body.style.overflow = 'hidden'; // Prevent background scrolling
      setIsAnimating(true);
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.body.style.overflow = ''; // Re-enable scrolling
    };
  }, [isOpen, onCancel, closeOnEsc]);
  
  // Handle animation on close
  const handleClose = () => {
    setIsAnimating(false);
    setTimeout(() => {
      onCancel();
    }, 200); // Match transition duration
  };
  
  if (!isOpen && !isAnimating) {
    return null;
  }
  
  // Get icon and color based on type
  const getDialogTypeConfig = () => {
    switch (type) {
      case 'info':
        return {
          icon: <Info size={24} />,
          iconColor: 'text-blue-500 dark:text-blue-400',
          bgColor: 'bg-blue-100 dark:bg-blue-900/30',
        };
      case 'warning':
        return {
          icon: <AlertTriangle size={24} />,
          iconColor: 'text-amber-500 dark:text-amber-400',
          bgColor: 'bg-amber-100 dark:bg-amber-900/30',
        };
      case 'error':
        return {
          icon: <AlertCircle size={24} />,
          iconColor: 'text-red-500 dark:text-red-400',
          bgColor: 'bg-red-100 dark:bg-red-900/30',
        };
      case 'success':
        return {
          icon: <Check size={24} />,
          iconColor: 'text-green-500 dark:text-green-400',
          bgColor: 'bg-green-100 dark:bg-green-900/30',
        };
      case 'delete':
        return {
          icon: <X size={24} />,
          iconColor: 'text-red-500 dark:text-red-400',
          bgColor: 'bg-red-100 dark:bg-red-900/30',
        };
      case 'confirm':
      default:
        return {
          icon: <AlertTriangle size={24} />,
          iconColor: 'text-blue-500 dark:text-blue-400',
          bgColor: 'bg-blue-100 dark:bg-blue-900/30',
        };
    }
  };
  
  const { icon, iconColor, bgColor } = getDialogTypeConfig();
  
  // Button styles based on type
  const getConfirmButtonStyle = () => {
    if (type === 'delete' || isDangerous) {
      return 'bg-red-600 hover:bg-red-700 text-white';
    }
    
    switch (type) {
      case 'success':
        return 'bg-green-600 hover:bg-green-700 text-white';
      case 'error':
        return 'bg-red-600 hover:bg-red-700 text-white';
      case 'warning':
        return 'bg-amber-600 hover:bg-amber-700 text-white';
      case 'info':
      case 'confirm':
      default:
        return 'bg-blue-600 hover:bg-blue-700 text-white';
    }
  };
  
  // Create buttons in the correct order
  const renderButtons = () => {
    const confirmButton = (
      <button
        type="button"
        onClick={onConfirm}
        disabled={isLoading}
        className={cn(
          "px-4 py-2 rounded-md font-medium",
          getConfirmButtonStyle(),
          isLoading && "opacity-70 cursor-not-allowed"
        )}
      >
        {isLoading ? (
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Đang xử lý...
          </div>
        ) : (
          confirmLabel
        )}
      </button>
    );
    
    const cancelButton = (
      <button
        type="button"
        onClick={handleClose}
        disabled={isLoading}
        className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-md font-medium text-gray-700 dark:text-gray-300"
      >
        {cancelLabel}
      </button>
    );
    
    return reverseButtons ? (
      <div className="flex space-x-3">
        {confirmButton}
        {cancelButton}
      </div>
    ) : (
      <div className="flex space-x-3">
        {cancelButton}
        {confirmButton}
      </div>
    );
  };
  
  return (
    <div 
      className={cn(
        "fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 transition-opacity duration-200",
        isAnimating ? "opacity-100" : "opacity-0"
      )}
      onClick={(e) => {
        if (closeOnBackdropClick && e.target === e.currentTarget) {
          handleClose();
        }
      }}
    >
      <div 
        className={cn(
          "bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full transition-transform duration-200",
          isAnimating ? "scale-100" : "scale-95",
          className
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description"
      >
        <div className="p-6">
          <div className="flex items-start">
            {showIcon && (
              <div className={cn("p-2 mr-4 rounded-full", bgColor)}>
                <div className={iconColor}>
                  {icon}
                </div>
              </div>
            )}
            
            <div className="flex-1">
              <h3 
                id="dialog-title" 
                className="text-lg font-medium text-gray-900 dark:text-white"
              >
                {title}
              </h3>
              
              <div 
                id="dialog-description" 
                className="mt-2 text-sm text-gray-600 dark:text-gray-300"
              >
                {typeof message === 'string' ? (
                  <p>{message}</p>
                ) : (
                  message
                )}
              </div>
            </div>
          </div>
          
          <div className="mt-6 flex justify-end">
            {renderButtons()}
          </div>
        </div>
      </div>
    </div>
  );
};

// Utility function to easily create different dialog types
export const createDialog = (type: ConfirmDialogType, props: Omit<ConfirmDialogProps, 'type'>) => {
  return <ConfirmDialog type={type} {...props} />;
};

// Pre-configured dialogs
export const InfoDialog: React.FC<Omit<ConfirmDialogProps, 'type'>> = (props) => (
  <ConfirmDialog type="info" confirmLabel="OK" {...props} />
);

export const WarningDialog: React.FC<Omit<ConfirmDialogProps, 'type'>> = (props) => (
  <ConfirmDialog type="warning" {...props} />
);

export const ErrorDialog: React.FC<Omit<ConfirmDialogProps, 'type'>> = (props) => (
  <ConfirmDialog type="error" confirmLabel="OK" {...props} />
);

export const SuccessDialog: React.FC<Omit<ConfirmDialogProps, 'type'>> = (props) => (
  <ConfirmDialog type="success" confirmLabel="OK" {...props} />
);

export const DeleteDialog: React.FC<Omit<ConfirmDialogProps, 'type'>> = (props) => (
  <ConfirmDialog 
    type="delete" 
    confirmLabel="Xóa" 
    isDangerous={true}
    {...props}
  />
);

export default ConfirmDialog;
