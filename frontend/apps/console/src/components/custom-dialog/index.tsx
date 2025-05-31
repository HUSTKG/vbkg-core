import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export type DialogSize = "sm" | "md" | "lg" | "xl" | "2xl" | "3xl";

export type DialogProps = {
  /** The title of the dialog */
  title: string;
  /** Optional description text for the dialog */
  description?: string;
  /** Children components to render in the dialog body */
  children: React.ReactNode;
  /** Text for the trigger button. If not provided, a custom trigger must be supplied */
  triggerText?: string;
  /** Custom trigger element (use this for custom button styling) */
  customTrigger?: React.ReactNode;
  /** Whether the dialog is open (for controlled usage) */
  open?: boolean;
  /** Function to set the open state (for controlled usage) */
  onOpenChange?: (open: boolean) => void;
  /** Show footer with action buttons */
  showFooter?: boolean;
  /** Text for the primary action button */
  primaryActionText?: string;
  /** Handler for the primary action button */
  onPrimaryAction?: () => void;
  /** Disable the primary action button */
  primaryActionDisabled?: boolean;
  /** Text for the cancel button */
  cancelText?: string;
  /** Handler for when the dialog is closed */
  onClose?: () => void;
  /** Additional class name for dialog content */
  contentClassName?: string;
  /** Width class for the dialog (Tailwind width class) */
  size?: DialogSize;
};

const DialogComponent: React.FC<DialogProps> = ({
  title,
  description,
  children,
  triggerText,
  customTrigger,
  open,
  onOpenChange,
  showFooter = false,
  primaryActionText = "Save",
  onPrimaryAction,
  primaryActionDisabled = false,
  cancelText = "Cancel",
  onClose,
  contentClassName = "",
  size = "2xl",
}) => {
  // For uncontrolled usage
  const [internalOpen, setInternalOpen] = React.useState(false);

  // Determine if using controlled or uncontrolled mode
  const isControlled = open !== undefined && onOpenChange !== undefined;
  const isOpen = isControlled ? open : internalOpen;
  const setIsOpen = isControlled ? onOpenChange : setInternalOpen;

  // Handle close
  const handleClose = () => {
    setIsOpen(false);
    if (onClose) onClose();
  };

  // Handle primary action
  const handlePrimaryAction = () => {
    if (onPrimaryAction) {
      onPrimaryAction();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      {customTrigger ? (
        <DialogTrigger asChild>{customTrigger}</DialogTrigger>
      ) : triggerText ? (
        <DialogTrigger asChild>
          <Button variant="default">{triggerText}</Button>
        </DialogTrigger>
      ) : null}

      <DialogContent
        className={cn(
          "max-h-[80vh] overflow-y-auto p-0",
          size === "sm" && "sm:max-w-sm",
          size === "md" && "sm:max-w-md",
          size === "lg" && "sm:max-w-lg",
          size === "xl" && "sm:max-w-xl",
          size === "2xl" && "sm:max-w-2xl",
          size === "3xl" && "sm:max-w-3xl",
          `${contentClassName} [&>button]:hidden`,
        )}
        onEscapeKeyDown={handleClose}
        onInteractOutside={handleClose}
      >
        <DialogHeader className="sticky top-0 p-6 z-100 bg-white/95">
          <div className="flex items-center justify-between">
            <DialogTitle>{title}</DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 rounded-full"
              onClick={handleClose}
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Close</span>
            </Button>
          </div>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <div className="py-4 px-6">{children}</div>

        {showFooter && (
          <DialogFooter className="p-4">
            <Button variant="outline" onClick={handleClose}>
              {cancelText}
            </Button>
            <Button
              variant="default"
              onClick={handlePrimaryAction}
              disabled={primaryActionDisabled}
            >
              {primaryActionText}
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default DialogComponent;
